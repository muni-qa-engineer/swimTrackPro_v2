import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
from services.email_service import (
    send_booking_notification,
    send_booking_confirmation_email
)
from services.pricing_service import calculate_discounted_fee
from services.booking_engine import (
    generate_booking_id,
    generate_recurring_dates,
)
from services.makeup_service import (
    create_makeup_credit,
    get_available_makeup_credits,
)
from services.settings_service import (
    get_setting,
    set_setting,
)

app = Flask(__name__)
from config import (
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    SECRET_KEY,
    DATABASE_URL
)
app.secret_key = SECRET_KEY

def get_pg_connection():
    return psycopg2.connect(DATABASE_URL)

# V0033.0 - Make-Up Class Management
def ensure_makeup_tables():
    """
    V0033.0 - Make-Up Class Management

    Creates the PostgreSQL tables required for:
    1. makeup_credits  - Stores skipped classes as reusable credits.
    2. makeup_requests - Stores replacement date requests and approvals.

    This function is safe to call multiple times because it uses
    CREATE TABLE IF NOT EXISTS.
    """
    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS makeup_credits (
        id SERIAL PRIMARY KEY,
        booking_id TEXT NOT NULL,
        original_date DATE NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'available',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used_at TIMESTAMP,
        notes TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS makeup_requests (
        id SERIAL PRIMARY KEY,
        credit_id INTEGER NOT NULL REFERENCES makeup_credits(id) ON DELETE CASCADE,
        booking_id TEXT NOT NULL,
        original_date DATE NOT NULL,
        requested_date DATE NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        requested_by VARCHAR(100),
        approved_by VARCHAR(100),
        decision_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        decided_at TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def load_data():
    ensure_makeup_tables()
    conn = get_pg_connection()
    cursor = conn.cursor()

    # Load students
    cursor.execute('SELECT * FROM students')
    student_rows = cursor.fetchall()

    students = []
    for s in student_rows:
        students.append({
            'name': s[1],
            'owner_name': s[2],
            'owner_phone': s[3]
        })

    # Load bookings
    cursor.execute('SELECT * FROM bookings')
    booking_rows = cursor.fetchall()

    # -------------------------------------------------------
    # OPTIMIZATION: Bulk-fetch all makeup data in 2 queries
    # instead of opening a new connection per booking.
    # -------------------------------------------------------

    # All credits grouped by booking_id
    cursor.execute("""
        SELECT id, booking_id, original_date, status, created_at
        FROM makeup_credits
        ORDER BY original_date
    """)
    all_credits = cursor.fetchall()

    credits_by_booking = {}
    for row in all_credits:
        bid = str(row[1])
        credits_by_booking.setdefault(bid, []).append(row)

    # All requests grouped by booking_id
    cursor.execute("""
        SELECT id, booking_id, requested_date, status
        FROM makeup_requests
        ORDER BY requested_date
    """)
    all_requests = cursor.fetchall()

    requests_by_booking = {}
    for row in all_requests:
        bid = str(row[1])
        requests_by_booking.setdefault(bid, []).append(row)

    # -------------------------------------------------------

    bookings = []

    for b in booking_rows:
        calendar_dates = generate_recurring_dates(
            str(b[3]),
            str(b[4]),
            b[6]
        )

        # V0037.3 - Real-Time Class Progress Completion
        # A class is considered completed when the current time is
        # greater than or equal to the session start time + 1 hour.
        is_completed = False
        total_classes = len(calendar_dates)
        completed_classes = 0
        remaining_classes = total_classes

        try:
            if calendar_dates:
                current_datetime = datetime.now()
                booking_time = (b[9] or '06:00 AM').strip()

                for class_date in calendar_dates:
                    class_datetime = datetime.strptime(
                        f"{class_date} {booking_time}",
                        '%Y-%m-%d %I:%M %p'
                    )
                    # Each session duration is 1 hour.
                    class_end_datetime = class_datetime + timedelta(hours=1)

                    # Mark as completed immediately after session end time.
                    if current_datetime >= class_end_datetime:
                        completed_classes += 1

                remaining_classes = max(
                    total_classes - completed_classes,
                    0
                )

                if total_classes > 0 and completed_classes >= total_classes:
                    is_completed = True

        except Exception as e:
            is_completed = False
            completed_classes = 0
            remaining_classes = total_classes

        booking = {
            'id': b[0],
            'student': b[1],
            'created_by': b[2],
            'start_date': b[3],
            'end_date': b[4],
            'package': b[5],
            'selected_days': b[6],
            'location': b[7],
            'persons': b[8],
            'time': b[9],
            'fee': b[10],
            'status': b[11],
            'payment_request': b[12],
            'payment_status': b[12],
            'owner_name': b[13],
            'owner_phone': b[14],
            'email': b[24] if len(b) > 24 else '',
            'delete_requested': b[15] if len(b) > 15 else False,
            'delete_requested_at': b[16] if len(b) > 16 else None,
            'delete_requested_by': b[17] if len(b) > 17 else None,
            'calendar_dates': calendar_dates,
            'is_completed': is_completed,
            'total_classes': total_classes,
            'completed_classes': completed_classes,
            'remaining_classes': remaining_classes
        }

        # -------------------------------------------------------
        # Map pre-fetched makeup data — no DB calls inside loop
        # -------------------------------------------------------
        bid = str(booking['id'])
        booking_credits = credits_by_booking.get(bid, [])
        booking_requests = requests_by_booking.get(bid, [])

        # Total credits created for this booking
        booking['makeup_credits_used'] = len(booking_credits)

        # First available credit
        available_credits = [
            r for r in booking_credits if r[3] == 'available'
        ]
        first_available = available_credits[0] if available_credits else None

        booking['available_makeup_credit_id'] = (
            first_available[0] if first_available else None
        )
        booking['has_available_makeup_credit'] = first_available is not None

        # Skipped dates
        booking['skipped_dates'] = [
            str(r[2]) for r in booking_credits
        ]

        # Dates where the credit was already used
        booking['used_makeup_dates'] = [
            str(r[2]) for r in booking_credits if r[3] == 'used'
        ]

        # Makeup requests
        booking['makeup_requests'] = [
            {
                'id': r[0],
                'requested_date': str(r[2]),
                'status': r[3]
            }
            for r in booking_requests
        ]

        bookings.append(booking)

    conn.close()

    return {
        'students': students,
        'bookings': bookings
    }

def save_data(students, bookings):
    conn = get_pg_connection()
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute('DELETE FROM students')
    cursor.execute('DELETE FROM bookings')

    # Save students
    for student in students:
        cursor.execute('''
        INSERT INTO students (
            student_name,
            owner_name,
            owner_phone
        ) VALUES (%s, %s, %s)
        ''', (
            student.get('name', ''),
            student.get('owner_name', ''),
            student.get('owner_phone', '')
        ))

    # Save bookings
    for booking in bookings:
        cursor.execute('''
        INSERT INTO bookings (
            id,
            student_name,
            created_by,
            start_date,
            end_date,
            package,
            selected_days,
            location,
            time,
            fee,
            status,
            payment_request,
            owner_name,
            owner_phone,
            persons,
            email
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            booking.get('id', ''),
            booking.get('student', ''),
            booking.get('created_by', ''),
            booking.get('start_date', ''),
            booking.get('end_date', ''),
            booking.get('package', ''),
            booking.get('selected_days', ''),
            booking.get('location', ''),
            booking.get('time', ''),
            int(booking.get('fee', 0)),
            booking.get('status', 'NOT_PAID'),
            booking.get('payment_request', 'NOT_PAID'),
            booking.get('owner_name', ''),
            booking.get('owner_phone', ''),
            int(booking.get('persons', 1)),
            booking.get('email', '')
        ))

    conn.commit()
    conn.close()


def save_complete_data(data):
    save_data(data.get('students', []), data.get('bookings', []))

# --- ROUTES ---
@app.route('/')
def index():
    if 'user_name' not in session:
        return render_template('login.html')
    
    data = load_data()  # Loads data from PostgreSQL
    
    current_user = session.get('user_name')
    current_phone = session.get('phone')
    current_role = session.get('role', 'guest')

    # TRAINER => view everything
    if current_role == 'trainer':
        user_bookings = data['bookings']
        user_students = data.get('students', [])

    # GUEST => isolated data only
    else:
        user_bookings = [
            b for b in data['bookings']
            if (b.get('owner_name') or '').strip().lower() == current_user
            and b.get('owner_phone') == current_phone
        ]

        user_students = [
            s for s in data.get('students', [])
            if isinstance(s, dict)
            and (s.get('owner_name') or '').strip().lower() == current_user
            and s.get('owner_phone') == current_phone
        ]
    # -----------------------------
    # Dashboard Analytics
    # -----------------------------
    total_swimmers = len(user_students)

    active_bookings = sum(
        1 for b in user_bookings
        if not b.get('is_completed', False)
    )

    completed_bookings = sum(
        1 for b in user_bookings
        if b.get('is_completed', False)
    )

    monthly_revenue = sum(
        int(b.get('fee', 0) or 0)
        for b in user_bookings
        if str(b.get('status', '')).lower() == 'paid'
    )

    pending_payments = sum(
        int(b.get('fee', 0) or 0)
        for b in user_bookings
        if str(b.get('status', '')).lower() != 'paid'
    )

    # -----------------------------
    # Location Suggestions
    # -----------------------------
    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute('''
    SELECT DISTINCT location
    FROM bookings
    WHERE location IS NOT NULL
      AND TRIM(location) <> ''
    ORDER BY location
    ''')

    location_suggestions = [
        row[0]
        for row in cursor.fetchall()
        if row[0]
    ]

    conn.close()

    return render_template(
        'dashboard.html',
        user_name=session['user_name'],
        role=session.get('role', 'guest'),
        bookings=user_bookings,
        students=user_students,
        total_swimmers=total_swimmers,
        active_bookings=active_bookings,
        completed_bookings=completed_bookings,
        monthly_revenue=monthly_revenue,
        pending_payments=pending_payments,
        location_suggestions=location_suggestions,
        notice_message=get_setting(
            'notice_message',
            '💰 Monthly fees are due before 5 days of the package end date • '
            '🏆 Special coaching sessions available • '
            '📞 Contact the trainer for any schedule changes'
        ),
        account_holder_name=get_setting("account_holder_name", ""),
        trainer_phone=get_setting("trainer_phone", ""),
        upi_id=get_setting("upi_id", "")
    )

@app.route('/login', methods=['POST'])
def login():
    role = (request.form.get('role') or '').lower()
    name = (request.form.get('name') or '').strip()
    password = (request.form.get('password') or '').strip()
    phone = (request.form.get('phone') or '').strip()

    # TRAINER LOGIN
    if role == 'trainer':

        if (
            ADMIN_USERNAME
            and ADMIN_PASSWORD
            and name.lower() == ADMIN_USERNAME.lower()
            and password == ADMIN_PASSWORD
        ):
            session['user_name'] = 'Trainer'
            session['role'] = 'trainer'
            return redirect(url_for('index'))

        flash('Invalid trainer credentials')
        return redirect(url_for('index'))

    if role == 'guest' and name:
        # Normalize values
        normalized_name = name.lower()
        phone = ''.join(ch for ch in phone if ch.isdigit())

        # Validate 10-digit phone number
        if len(phone) != 10:
            flash('Please enter a valid 10-digit mobile number.')
            return redirect(url_for('index'))

        conn = get_pg_connection()
        cursor = conn.cursor()

        # Find any existing users with the same phone number
        # from the students and bookings tables.
        cursor.execute("""
        SELECT owner_name
        FROM students
        WHERE owner_phone = %s

        UNION

        SELECT owner_name
        FROM bookings
        WHERE owner_phone = %s

        LIMIT 1
        """, (phone, phone))

        existing_row = cursor.fetchone()
        conn.close()

        # If this phone number already belongs to a different user
        # (case-insensitive comparison), reject the login.
        if existing_row:
            existing_name = (existing_row[0] or '').strip().lower()

            if existing_name != normalized_name:
                flash('User already exists with this mobile number.')
                return redirect(url_for('index'))

        # Valid guest login. Preserve the entered display name
        # and store the normalized phone number.
        session['role'] = 'guest'
        session['user_name'] = normalized_name
        session['phone'] = phone

        return redirect(url_for('index'))

    # Fallback if no valid role or name is provided
    else:
        flash("Please enter all required fields.")
        return redirect(url_for('index'))

@app.route('/add_swimmer', methods=['POST'])
def add_swimmer():
    if session.get('role') == 'trainer':
        flash('Trainer cannot add swimmers directly')
        return redirect(url_for('index'))
    data = load_data()

    name = (request.form.get('name') or '').strip()
    if not name:
        flash('Swimmer name required')
        return redirect(url_for('index'))

    # prevent duplicates
    existing_swimmer = next(
        (
            s for s in data['students']
            if isinstance(s, dict)
            and s.get('name') == name
            and s.get('owner_name') == session.get('user_name')
            and s.get('owner_phone') == session.get('phone')
        ),
        None
    )

    if existing_swimmer:
        return redirect(url_for('index', swimmer_exists='true'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO students (
        student_name,
        owner_name,
        owner_phone
    ) VALUES (%s, %s, %s)
    ''', (
        name,
        session.get('user_name'),
        session.get('phone')
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/delete_swimmer/<name>', methods=['POST'])
def delete_swimmer(name):
    current_user = session.get('user_name')
    current_phone = session.get('phone')

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Delete swimmer
    cursor.execute('''
    DELETE FROM students
    WHERE student_name = %s
    AND owner_name = %s
    AND owner_phone = %s
    ''', (
        name,
        current_user,
        current_phone
    ))

    # Delete all bookings of that swimmer
    cursor.execute('''
    DELETE FROM bookings
    WHERE student_name = %s
    AND owner_name = %s
    AND owner_phone = %s
    ''', (
        name,
        current_user,
        current_phone
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/book', methods=['POST'])
def book():
    if session.get('role') == 'trainer':
        flash('Trainer cannot create bookings directly')
        return redirect(url_for('index'))
    data = load_data()
    # Enhanced validation and logic for booking
    student = request.form['student']
    date_str = request.form['date']
    time_str = request.form['time']
    email = (request.form.get('email') or '').strip()
    package = request.form.get('package', 'Single')
    end_date = request.form.get('end_date', date_str)
    persons = request.form.get('persons', 1)

    # Default fee based on package and group discount.
    session_count = None
    if package == 'Custom':
        session_count = len(
            generate_recurring_dates(
                date_str,
                end_date,
                request.form.get('selected_days', '')
            )
        )

    fee = calculate_discounted_fee(package, persons, session_count)
    if package == 'Demo':
        fee = 500 * int(persons)

    # Allow manual fee override only for admin users.
    # Guest users always use the system-calculated fee.
    if session.get('role') == 'trainer':
        manual_fee = (request.form.get('fee') or '').strip()
        if manual_fee:
            try:
                fee = int(float(manual_fee))
            except ValueError:
                pass

    # Normalize end date based on package
    if package in ('Single', 'Demo'):
        end_date = date_str
    elif package == 'Monthly':
        start_dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        next_month = start_dt + timedelta(days=31)
        end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    # Validate that end date is not earlier than start date
    try:
        start_dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        if end_dt < start_dt:
            flash('End date cannot be earlier than start date')
            return redirect(url_for('index'))
    except Exception:
        flash('Invalid start or end date')
        return redirect(url_for('index'))

    # Validate past date
    try:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if selected_date < datetime.today().date():
            flash("Cannot book past dates")
            return redirect(url_for('index'))
    except:
        flash("Invalid date")
        return redirect(url_for('index'))

    booking_id = generate_booking_id(student, date_str, time_str)

    # Prevent overlapping bookings within 1 hour
    try:
        booking_time = datetime.strptime(time_str, '%I:%M %p')
    except Exception:
        flash('Invalid time format')
        return redirect(url_for('index'))

    new_booking_dates = generate_recurring_dates(
        date_str,
        end_date,
        request.form.get('selected_days', '')
    )

    # -------------------------------------------------
    # V0038.0 - Basic Trainer Location Conflict Check
    # Same Date + Same Time + Different Location
    # -------------------------------------------------
    new_location = (request.form.get('location') or '').strip().lower()

    for b in data['bookings']:
        try:
            existing_time = (b.get('time') or '').strip()
            existing_location = (b.get('location') or '').strip().lower()
            existing_start_date = str(b.get('start_date', ''))

            # Only compare exact slot date and exact slot time
            if existing_start_date != date_str:
                continue

            if existing_time != time_str:
                continue

            # Same location is allowed
            if existing_location == new_location:
                continue

            flash(
                'Selected time slot is already booked at another location. '
                'Please choose a different time slot or location.',
                'warning'
            )
            return redirect('/?location_conflict=true')

        except Exception:
            continue

    for b in data['bookings']:
        try:
            existing_start = str(b.get('start_date', ''))
            existing_end = str(b.get('end_date', b.get('start_date', '')))
            existing_days = b.get('selected_days', '')

            existing_booking_dates = generate_recurring_dates(
                existing_start,
                existing_end,
                existing_days
            )

            overlapping_dates = set(new_booking_dates) & set(existing_booking_dates)

            same_owner = b.get('owner_name') == session.get('user_name')
            same_student = b.get('student') == student

            if not (overlapping_dates and same_owner and same_student):
                continue

            existing_time_str = b.get('time')
            if not existing_time_str:
                continue

            existing_time = datetime.strptime(existing_time_str, '%I:%M %p')

            time_difference = abs(
                (booking_time - existing_time).total_seconds()
            ) / 60

            # Minimum 1 hour gap required
            if time_difference < 60:
                return redirect('/?booking_conflict=true')

        except Exception:
            # Ignore malformed historical records and continue checking others
            continue

    payment_choice = request.form.get('payment_status', 'Not Paid')

    if payment_choice == 'Paid':
        status = 'Pending'
    else:
        status = 'Not Paid'

    new_booking = {
        "id": booking_id,
        "student": student,
        "created_by": session.get('user_name'),
        "start_date": date_str,
        "end_date": end_date,
        "package": package,
        "selected_days": request.form.get('selected_days', ''),
        "location": request.form.get('location', '').strip(),
        "email": email,
        "persons": persons,
        "time": time_str,
        "fee": fee,
        "status": status,
        "payment_request": payment_choice,
        "owner_name": session.get('user_name'),
        "owner_phone": session.get('phone'),
    }

    # V0037.1 - Automatically create the swimmer if it does not already exist.
    existing_swimmer = next(
        (
            s for s in data['students']
            if isinstance(s, dict)
            and (s.get('name') or '').strip().lower() == student.strip().lower()
            and s.get('owner_name') == session.get('user_name')
            and s.get('owner_phone') == session.get('phone')
        ),
        None
    )

    if not existing_swimmer:
        conn = get_pg_connection()
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO students (
            student_name,
            owner_name,
            owner_phone
        ) VALUES (%s, %s, %s)
        ''', (
            student.strip(),
            session.get('user_name'),
            session.get('phone')
        ))

        conn.commit()
        conn.close()

    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO bookings (
        id,
        student_name,
        created_by,
        start_date,
        end_date,
        package,
        selected_days,
        location,
        persons,
        time,
        fee,
        status,
        payment_request,
        owner_name,
        owner_phone,
        email
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        new_booking['id'],
        new_booking['student'],
        new_booking['created_by'],
        new_booking['start_date'],
        new_booking['end_date'],
        new_booking['package'],
        new_booking['selected_days'],
        new_booking['location'],
        int(new_booking['persons']),
        new_booking['time'],
        int(new_booking['fee']),
        new_booking['status'],
        new_booking['payment_request'],
        new_booking['owner_name'],
        new_booking['owner_phone'],
        new_booking['email']
    ))

    conn.commit()
    conn.close()

    # Send admin notification.
    send_booking_notification(new_booking)

    # Send swimmer confirmation email.
    send_booking_confirmation_email(new_booking)

    return redirect(url_for('index'))


# --- Edit Booking Route ---
@app.route('/edit/<booking_id>', methods=['GET'])
def edit_booking(booking_id):
    data = load_data()

    # Find booking
    booking = next((b for b in data['bookings'] if b['id'] == booking_id), None)

    if not booking:
        flash("Booking not found")
        return redirect(url_for('index'))

    # Render edit page with booking data and user role
    return render_template(
        'editBooking.html',
        booking=booking,
        role=session.get('role', 'guest')
    )

@app.route('/update/<booking_id>', methods=['POST'])
def update_booking(booking_id):
    data = load_data()

    # Find booking
    booking = next((b for b in data['bookings'] if b['id'] == booking_id), None)

    if not booking:
        flash("Booking not found")
        return redirect(url_for('index'))

    # Get updated values
    student = request.form['student']
    date_str = request.form['date']
    time_str = request.form['time']
    package = request.form.get('package', 'Single')
    end_date = request.form.get('end_date', date_str)
    persons = request.form.get('persons', 1)

    # Default fee based on package and group discount.
    session_count = None
    if package == 'Custom':
        selected_days = request.form.getlist('selected_days')
        selected_days_str = ', '.join(selected_days)
        session_count = len(
            generate_recurring_dates(
                date_str,
                end_date,
                selected_days_str
            )
        )

    fee = calculate_discounted_fee(package, persons, session_count)
    if package == 'Demo':
        fee = 500 * int(persons)

    # Allow manual fee override only for admin users.
    # Guest users always use the system-calculated fee.
    if session.get('role') == 'trainer':
        manual_fee = (request.form.get('fee') or '').strip()
        if manual_fee:
            try:
                fee = int(float(manual_fee))
            except ValueError:
                pass

    # Normalize end date based on package
    if package in ('Single', 'Demo'):
        end_date = date_str
    elif package == 'Monthly':
        start_dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        next_month = start_dt + timedelta(days=31)
        end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
    # Validate that end date is not earlier than start date
    try:
        start_dt = datetime.strptime(date_str, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        if end_dt < start_dt:
            flash('End date cannot be earlier than start date')
            return redirect(url_for('edit_booking', booking_id=booking_id))
    except Exception:
        flash('Invalid start or end date')
        return redirect(url_for('edit_booking', booking_id=booking_id))

    # Get selected class days
    selected_days = request.form.getlist('selected_days')

    # Convert selected days list to comma-separated string
    selected_days_str = ', '.join(selected_days)

    # Recalculate fee after selected days are finalized
    if package == 'Monthly':
        fee = len(selected_days) * 3000 * int(persons)
    elif package == 'Single':
        fee = 750 * int(persons)
    elif package == 'Demo':
        fee = 500 * int(persons)

    # Prevent overlapping bookings when editing
    try:
        booking_time = datetime.strptime(time_str, '%I:%M %p')
    except Exception:
        flash('Invalid time format')
        return redirect(url_for('edit_booking', booking_id=booking_id))

    new_booking_dates = generate_recurring_dates(
        date_str,
        end_date,
        selected_days_str
    )

    for b in data['bookings']:
        try:
            # Skip the booking currently being edited
            if str(b.get('id')) == str(booking_id):
                continue

            existing_start = str(b.get('start_date', ''))
            existing_end = str(b.get('end_date', b.get('start_date', '')))
            existing_days = b.get('selected_days', '')

            existing_booking_dates = generate_recurring_dates(
                existing_start,
                existing_end,
                existing_days
            )

            overlapping_dates = set(new_booking_dates) & set(existing_booking_dates)

            same_owner = b.get('owner_name') == session.get('user_name')
            same_student = b.get('student') == student

            if not (overlapping_dates and same_owner and same_student):
                continue

            existing_time_str = b.get('time')
            if not existing_time_str:
                continue

            existing_time = datetime.strptime(existing_time_str, '%I:%M %p')

            time_difference = abs(
                (booking_time - existing_time).total_seconds()
            ) / 60

            # Minimum 1 hour gap required
            if time_difference < 60:
                return redirect('/?booking_conflict=true')

        except Exception:
            # Ignore malformed historical records
            continue

    # Update values
    booking['student'] = student
    booking['start_date'] = date_str
    booking['end_date'] = end_date
    booking['package'] = package
    booking['selected_days'] = selected_days_str
    booking['location'] = request.form.get('location', '').strip()
    booking['time'] = time_str
    booking['fee'] = fee

    booking['persons'] = persons

    payment_choice = request.form.get('payment_status', 'Not Paid')
    booking['payment_request'] = payment_choice

    role = session.get('role')

    # Guest payment request flow
    if role != 'trainer':

        if payment_choice == 'Paid':
            booking['status'] = 'Pending'
        else:
            booking['status'] = 'Not Paid'

    # Trainer edit flow
    else:

        # Trainer uses same edit dropdown
        if payment_choice == 'Paid':
            booking['status'] = 'Paid'
        else:
            booking['status'] = 'Not Paid'

    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE bookings
    SET
        student_name = %s,
        start_date = %s,
        end_date = %s,
        package = %s,
        selected_days = %s,
        location = %s,
        time = %s,
        fee = %s,
        persons = %s,
        status = %s,
        payment_request = %s
    WHERE id = %s
    ''', (
        booking['student'],
        booking['start_date'],
        booking['end_date'],
        booking['package'],
        booking['selected_days'],
        booking['location'],
        booking['time'],
        int(booking['fee']),
        int(booking['persons']),
        booking['status'],
        booking['payment_request'],
        booking_id
    ))

    conn.commit()
    conn.close()

    flash("Booking updated successfully")
    return redirect(url_for('index'))


# --- Update Payment Status Route ---
@app.route('/update_payment_status/<booking_id>', methods=['POST'])
def update_payment_status(booking_id):
    if 'user_name' not in session:
        return redirect(url_for('index'))

    new_status = (request.form.get('status') or '').strip()

    allowed_statuses = [
        'Not Paid',
        'Pending Verification',
        'Paid'
    ]

    if new_status not in allowed_statuses:
        flash('Invalid payment status selected')
        return redirect(url_for('index'))

    # Guest users cannot directly mark a booking as Paid.
    if (
        session.get('role') != 'trainer'
        and new_status == 'Paid'
    ):
        flash('Only trainer can mark a payment as Paid')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    if session.get('role') == 'trainer':
        cursor.execute('''
        UPDATE bookings
        SET
            status = %s,
            payment_request = %s
        WHERE id = %s
        ''', (
            new_status,
            'Paid' if new_status in ('Pending Verification', 'Paid') else 'Not Paid',
            booking_id
        ))

    else:
        cursor.execute('''
        UPDATE bookings
        SET
            status = %s,
            payment_request = %s
        WHERE id = %s
          AND owner_name = %s
          AND owner_phone = %s
        ''', (
            new_status,
            'Paid' if new_status == 'Pending Verification' else 'Not Paid',
            booking_id,
            session.get('user_name'),
            session.get('phone')
        ))

    conn.commit()
    conn.close()

    flash('Payment status updated successfully')
    return redirect(url_for('index'))


@app.route('/delete/<booking_id>', methods=['POST'])
def delete_booking(booking_id):
    role = session.get('role', 'guest')

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Load booking details
    cursor.execute('''
    SELECT student_name, owner_name, owner_phone, start_date, time
    FROM bookings
    WHERE id = %s
    ''', (booking_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        flash('Booking not found')
        return redirect(url_for('index'))

    deleted_student = row[0]
    owner_name = row[1]
    owner_phone = row[2]
    start_date = row[3]
    booking_time_str = row[4]

    # Guest users can delete immediately only before the first class starts.
    # After the first class start time, trainer approval is required.
    if role != 'trainer':
        try:
            first_class_datetime = datetime.strptime(
                f"{start_date} {booking_time_str}",
                '%Y-%m-%d %I:%M %p'
            )
        except Exception:
            first_class_datetime = None

        # If current time is before the first class, delete immediately.
        if first_class_datetime and datetime.now() < first_class_datetime:
            cursor.execute(
                'DELETE FROM bookings WHERE id = %s',
                (booking_id,)
            )

            # Check if swimmer still has any bookings
            cursor.execute('''
            SELECT COUNT(*)
            FROM bookings
            WHERE TRIM(student_name) = TRIM(%s)
              AND owner_name = %s
              AND owner_phone = %s
            ''', (
                deleted_student,
                owner_name,
                owner_phone
            ))

            remaining_count = cursor.fetchone()[0]

            # Remove swimmer if no bookings remain
            if remaining_count == 0:
                cursor.execute('''
                DELETE FROM students
                WHERE TRIM(student_name) = TRIM(%s)
                  AND owner_name = %s
                  AND owner_phone = %s
                ''', (
                    deleted_student,
                    owner_name,
                    owner_phone
                ))

            conn.commit()
            conn.close()

            flash(f'Booking deleted for {deleted_student}')
            return redirect(url_for('index'))

        # After the first class starts, create a delete request.
        cursor.execute('''
        UPDATE bookings
        SET
            delete_requested = TRUE,
            delete_requested_at = %s,
            delete_requested_by = %s
        WHERE id = %s
        ''', (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            session.get('user_name'),
            booking_id
        ))

        conn.commit()
        conn.close()

        flash(f'Delete request submitted for {deleted_student}')
        return redirect(url_for('index'))

    # Trainer deletes immediately
    cursor.execute(
        'DELETE FROM bookings WHERE id = %s',
        (booking_id,)
    )

    # Check if swimmer still has any bookings
    cursor.execute('''
    SELECT COUNT(*)
    FROM bookings
    WHERE TRIM(student_name) = TRIM(%s)
      AND owner_name = %s
      AND owner_phone = %s
    ''', (
        deleted_student,
        owner_name,
        owner_phone
    ))

    remaining_count = cursor.fetchone()[0]

    # Remove swimmer if no bookings remain
    if remaining_count == 0:
        cursor.execute('''
        DELETE FROM students
        WHERE TRIM(student_name) = TRIM(%s)
          AND owner_name = %s
          AND owner_phone = %s
        ''', (
            deleted_student,
            owner_name,
            owner_phone
        ))

    conn.commit()
    conn.close()

    flash(f'Booking deleted for {deleted_student}')
    return redirect(url_for('index'))


# --- Approve and Reject Delete Booking Routes ---
@app.route('/approve_delete/<booking_id>', methods=['POST'])
def approve_delete(booking_id):
    if session.get('role') != 'trainer':
        flash('Unauthorized action')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Load booking details before deletion
    cursor.execute('''
    SELECT student_name, owner_name, owner_phone
    FROM bookings
    WHERE id = %s
    ''', (booking_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        flash('Booking not found')
        return redirect(url_for('index'))

    deleted_student = row[0]
    owner_name = row[1]
    owner_phone = row[2]

    # Permanently delete the booking
    cursor.execute('DELETE FROM bookings WHERE id = %s', (booking_id,))

    # Check if swimmer still has any bookings
    cursor.execute('''
    SELECT COUNT(*)
    FROM bookings
    WHERE TRIM(student_name) = TRIM(%s)
      AND owner_name = %s
      AND owner_phone = %s
    ''', (
        deleted_student,
        owner_name,
        owner_phone
    ))

    remaining_count = cursor.fetchone()[0]

    # Remove swimmer if no bookings remain
    if remaining_count == 0:
        cursor.execute('''
        DELETE FROM students
        WHERE TRIM(student_name) = TRIM(%s)
          AND owner_name = %s
          AND owner_phone = %s
        ''', (
            deleted_student,
            owner_name,
            owner_phone
        ))

    conn.commit()
    conn.close()

    flash(f'Delete approved for {deleted_student}')
    return redirect(url_for('index'))


@app.route('/reject_delete/<booking_id>', methods=['POST'])
def reject_delete(booking_id):
    if session.get('role') != 'trainer':
        flash('Unauthorized action')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE bookings
    SET
        delete_requested = FALSE,
        delete_requested_at = NULL,
        delete_requested_by = NULL
    WHERE id = %s
    ''', (booking_id,))

    conn.commit()
    conn.close()

    flash('Delete request rejected')
    return redirect(url_for('index'))


# --- Skip Session and Create Make-Up Credit Route ---

@app.route('/skip_session/<booking_id>/<session_date>', methods=['POST'])
def skip_session(booking_id, session_date):
    """
    V0033.0 Step 2 - Skip a scheduled class and create a make-up credit.

    session_date format: YYYY-MM-DD
    """
    if 'user_name' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))

    # Validate that the booking exists directly from PostgreSQL.
    # Avoid calling load_data() here because load_data() may trigger
    # logic that rewrites existing bookings and causes duplicate
    # primary key errors.
    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        id,
        student_name,
        owner_name,
        owner_phone,
        email,
        start_date,
        end_date,
        selected_days
    FROM bookings
    WHERE id = %s
    LIMIT 1
    """, (str(booking_id),))

    row = cursor.fetchone()
    conn.close()

    if row:
        booking = {
            'id': row[0],
            'student': row[1],
            'owner_name': row[2],
            'owner_phone': row[3],
            'email': row[4] or '',
            'calendar_dates': generate_recurring_dates(
                str(row[5]),
                str(row[6]),
                row[7]
            )
        }
    else:
        booking = None

    if not booking:
        flash('Booking not found')
        return redirect(url_for('index'))

    # Guests may skip only their own bookings.
    if session.get('role') != 'trainer':
        if (
            booking.get('owner_name') != session.get('user_name')
            or booking.get('owner_phone') != session.get('phone')
        ):
            flash('Unauthorized action')
            return redirect(url_for('index'))

    # Validate that the selected date belongs to this booking schedule.
    calendar_dates = booking.get('calendar_dates', [])
    if session_date not in calendar_dates:
        flash('Invalid session date')
        return redirect(url_for('index'))

    # Create one make-up credit for this skipped session.
    created = create_makeup_credit(
        booking_id,
        session_date,
        f"Skipped session for {booking.get('student', '')}"
    )

    if created:
        flash(
            f"Session on {session_date} marked as skipped. "
            "One make-up credit has been created."
        )
    else:
        flash('A make-up credit already exists for this session.')

    return redirect(url_for('index'))


# --- Undo Skip Session Route ---
@app.route('/undo_skip_session/<booking_id>/<session_date>', methods=['POST'])
def undo_skip_session(booking_id, session_date):
    """
    Remove a skipped-session credit when no make-up request has been created.

    This allows a swimmer to reverse an accidental skip before the credit
    is used to submit a pending or approved make-up request.
    """
    if 'user_name' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Load the booking to verify ownership.
    cursor.execute("""
    SELECT owner_name, owner_phone
    FROM bookings
    WHERE id = %s
    LIMIT 1
    """, (str(booking_id),))

    booking_row = cursor.fetchone()

    if not booking_row:
        conn.close()
        flash('Booking not found.')
        return redirect(url_for('index'))

    # Guests may undo only their own skipped sessions.
    if session.get('role') != 'trainer':
        if (
            booking_row[0] != session.get('user_name')
            or booking_row[1] != session.get('phone')
        ):
            conn.close()
            flash('Unauthorized action')
            return redirect(url_for('index'))

    # Find an available make-up credit for this skipped date.
    cursor.execute("""
    SELECT id
    FROM makeup_credits
    WHERE booking_id = %s
      AND original_date = %s
      AND status = 'available'
    LIMIT 1
    """, (
        str(booking_id),
        session_date
    ))

    credit_row = cursor.fetchone()

    if not credit_row:
        conn.close()
        flash('This skipped session cannot be undone.')
        return redirect(url_for('index'))

    credit_id = credit_row[0]

    # Safety check: do not allow undo if any make-up request already exists.
    cursor.execute("""
    SELECT 1
    FROM makeup_requests
    WHERE credit_id = %s
    LIMIT 1
    """, (credit_id,))

    if cursor.fetchone():
        conn.close()
        flash('Cannot undo because a make-up request already exists.')
        return redirect(url_for('index'))

    # Delete the unused make-up credit.
    cursor.execute("""
    DELETE FROM makeup_credits
    WHERE id = %s
    """, (credit_id,))

    conn.commit()
    conn.close()

    flash('Skipped session has been restored.')
    return redirect(url_for('index'))


@app.route('/makeup_request/<booking_id>')
def makeup_request_form(booking_id):
    """
    Display the make-up request form for all available credits.
    """
    if 'user_name' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT student_name, owner_name, owner_phone
    FROM bookings
    WHERE id = %s
    LIMIT 1
    """, (str(booking_id),))

    row = cursor.fetchone()
    conn.close()

    if not row:
        flash('Booking not found')
        return redirect(url_for('index'))

    # Guests may access only their own bookings.
    if session.get('role') != 'trainer':
        if row[1] != session.get('user_name') or row[2] != session.get('phone'):
            flash('Unauthorized action')
            return redirect(url_for('index'))

    credits = get_available_makeup_credits(booking_id)

    if not credits:
        flash('No available make-up credits.')
        return redirect(url_for('index'))

    return render_template(
        'makeup_request.html',
        booking_id=booking_id,
        student_name=row[0],
        credits=credits
    )



@app.route('/submit_makeup_request', methods=['POST'])
def submit_makeup_request():
    """
    Create a make-up request for a selected credit and replacement date.
    """
    if 'user_name' not in session:
        flash('Please log in first')
        return redirect(url_for('index'))

    booking_id = (request.form.get('booking_id') or '').strip()
    credit_id = (request.form.get('credit_id') or '').strip()
    requested_date = (request.form.get('requested_date') or '').strip()

    if not booking_id or not credit_id or not requested_date:
        flash('All fields are required.')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Validate the selected credit.
    cursor.execute("""
    SELECT original_date
    FROM makeup_credits
    WHERE id = %s
      AND booking_id = %s
      AND status = 'available'
    LIMIT 1
    """, (credit_id, str(booking_id)))

    row = cursor.fetchone()

    if not row:
        conn.close()
        flash('Selected make-up credit is no longer available.')
        return redirect(url_for('index'))

    original_date = row[0]

    # --------------------------------------
    # V0033.1 Step 1 - Prevent Same-Day Selection
    # Users can only request a replacement on a future date.
    # The requested date must be strictly greater than the skipped date.
    # --------------------------------------
    try:
        requested_dt = datetime.strptime(
            requested_date,
            '%Y-%m-%d'
        ).date()

        original_dt = original_date

        if requested_dt <= original_dt:
            conn.close()
            flash(
                'Replacement date must be after the skipped session date.'
            )
            return redirect(url_for('index'))

    except Exception:
        conn.close()
        flash('Invalid replacement date.')
        return redirect(url_for('index'))

    # Prevent duplicate pending requests for the same credit.
    cursor.execute("""
    SELECT 1
    FROM makeup_requests
    WHERE credit_id = %s
      AND status IN ('pending', 'approved')
    LIMIT 1
    """, (credit_id,))

    if cursor.fetchone():
        conn.close()
        flash('A make-up request already exists for this skipped session.')
        return redirect(url_for('index'))

    # Create pending request.
    cursor.execute("""
    INSERT INTO makeup_requests (
        credit_id,
        booking_id,
        original_date,
        requested_date,
        status,
        requested_by
    ) VALUES (%s, %s, %s, %s, 'pending', %s)
    """, (
        int(credit_id),
        str(booking_id),
        original_date,
        requested_date,
        session.get('user_name')
    ))

    conn.commit()
    conn.close()

    flash('Make-up request submitted successfully for admin approval.')
    return redirect(url_for('index'))


# --- Approve and Reject Make-Up Request Routes ---

@app.route('/approve_makeup_request/<int:request_id>', methods=['POST'])
def approve_makeup_request(request_id):
    """
    Approve a pending make-up request and consume the related credit.
    """
    if session.get('role') != 'trainer':
        flash('Unauthorized action')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Load the pending request and its credit.
    cursor.execute("""
    SELECT credit_id
    FROM makeup_requests
    WHERE id = %s
      AND status = 'pending'
    LIMIT 1
    """, (request_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        flash('Pending make-up request not found.')
        return redirect(url_for('index'))

    credit_id = row[0]

    # Mark the request as approved.
    cursor.execute("""
    UPDATE makeup_requests
    SET
        status = 'approved',
        approved_by = %s,
        decided_at = CURRENT_TIMESTAMP
    WHERE id = %s
    """, (
        session.get('user_name', 'Admin'),
        request_id
    ))

    # Mark the associated credit as used.
    cursor.execute("""
    UPDATE makeup_credits
    SET
        status = 'used',
        used_at = CURRENT_TIMESTAMP
    WHERE id = %s
    """, (credit_id,))

    conn.commit()
    conn.close()

    flash('Make-up request approved successfully.')
    return redirect(url_for('index'))


@app.route('/reject_makeup_request/<int:request_id>', methods=['POST'])
def reject_makeup_request(request_id):
    """
    Reject or undo a pending make-up request.

    Behavior:
    - Delete the pending record from makeup_requests.
    - Restore the related makeup_credits row to status = 'available'.
    """
    if session.get('role') not in ('trainer', 'guest'):
        flash('Unauthorized action')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Load the pending request and related credit.
    cursor.execute("""
    SELECT credit_id
    FROM makeup_requests
    WHERE id = %s
      AND status = 'pending'
    LIMIT 1
    """, (request_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        flash('Pending make-up request not found.')
        return redirect(url_for('index'))

    credit_id = row[0]

    # Restore the make-up credit so it can be used again.
    cursor.execute("""
    UPDATE makeup_credits
    SET
        status = 'available',
        used_at = NULL
    WHERE id = %s
    """, (credit_id,))

    # Remove the pending request completely.
    cursor.execute("""
    DELETE FROM makeup_requests
    WHERE id = %s
    """, (request_id,))

    conn.commit()
    conn.close()

    flash('Pending make-up request has been revoked.')
    return redirect(url_for('index'))

@app.route('/about-trainer')
def about_trainer():
    if 'user_name' not in session:
        return redirect(url_for('index'))

    return render_template('about_trainer.html')

# --- Help Page Route ---

@app.route('/help')
def help_page():
    if 'user_name' not in session:
        return redirect(url_for('index'))

    return render_template('help.html')

@app.route('/update_notice', methods=['POST'])
def update_notice():
    if 'user_name' not in session:
        return redirect(url_for('index'))

    if session.get('role') != 'trainer':
        flash('Only trainer can update the Notice Board.', 'danger')
        return redirect(url_for('index'))

    notice_message = request.form.get('notice_message', '').strip()

    if not notice_message:
        flash('Notice Board message cannot be empty.', 'warning')
        return redirect(url_for('index'))

    set_setting('notice_message', notice_message)

    flash('Notice Board updated successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)