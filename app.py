import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from services.email_service import (
    send_booking_notification,
    send_booking_confirmation_email,
    send_booking_updated_email,
    send_booking_deleted_email,
    send_booking_deleted_alert,
    send_payment_reminder_email,
    send_package_completion_email
)
from services.pricing_service import calculate_discounted_fee
from services.booking_engine import (
    generate_booking_id,
    generate_booking_code,
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
                current_datetime = datetime.now(
                    ZoneInfo('Asia/Kolkata')
                ).replace(tzinfo=None)
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
            'booking_code': b[25] if len(b) > 25 else '',
            'payment_reminder_sent': b[26] if len(b) > 26 else False,
            'payment_reminder_sent_at': b[27] if len(b) > 27 else None,
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
    # V0038.6 Dashboard Statistics
    # -----------------------------
    total_sessions = sum(
        int(b.get('total_classes', 0) or 0)
        for b in user_bookings
    )

    completed_sessions = sum(
        int(b.get('completed_classes', 0) or 0)
        for b in user_bookings
    )

    remaining_sessions = sum(
        int(b.get('remaining_classes', 0) or 0)
        for b in user_bookings
    )

    makeup_sessions = sum(
        1
        for b in user_bookings
        if b.get('has_available_makeup_credit', False)
    )

    # -----------------------------
    # V0039.1 Dynamic Mini Calendar
    # -----------------------------
    import calendar

    ist_now = datetime.now(ZoneInfo('Asia/Kolkata'))
    current_year = ist_now.year
    current_month = ist_now.month
    today_day = ist_now.day

    current_month_name = ist_now.strftime('%B %Y')

    booked_dates = set()
    makeup_dates = set()

    today_date = ist_now.date()

    for booking in user_bookings:
        booking_time = (booking.get('time') or '06:00 AM').strip()

        for session_date in booking.get('calendar_dates', []):
            try:
                dt = datetime.strptime(session_date, '%Y-%m-%d')

                session_datetime = datetime.strptime(
                    f"{session_date} {booking_time}",
                    '%Y-%m-%d %I:%M %p'
                )

                session_end = session_datetime + timedelta(hours=1)

                # Show green only for upcoming / active sessions.
                # Completed sessions should return to normal calendar state.
                if (
                    dt.year == current_year
                    and dt.month == current_month
                    and session_end > ist_now.replace(tzinfo=None)
                ):
                    booked_dates.add(dt.day)

            except Exception:
                pass

        for makeup_date in booking.get('used_makeup_dates', []):
            try:
                dt = datetime.strptime(str(makeup_date), '%Y-%m-%d')

                if (
                    dt.year == current_year
                    and dt.month == current_month
                ):
                    makeup_dates.add(dt.day)
            except Exception:
                pass

    cal = calendar.Calendar(firstweekday=0)
    calendar_days = []

    for week in cal.monthdayscalendar(current_year, current_month):
        for day in week:
            if day == 0:
                calendar_days.append({
                    'day': None,
                    'is_today': False,
                    'is_booked': False,
                    'is_makeup': False
                })
            else:
                calendar_days.append({
                    'day': day,
                    'is_today': day == today_day,
                    'is_booked': day in booked_dates,
                    'is_makeup': day in makeup_dates
                })

    # -----------------------------
    # V0039.2 Dynamic Hero Banner
    # -----------------------------
    current_date_display = ist_now.strftime('%A, %d %b %Y')

    notification_count = 0

    pending_verification_count = sum(
        1
        for b in user_bookings
        if str(b.get('status', '')).lower() == 'pending verification'
    )

    notification_count += pending_verification_count
    notification_count += makeup_sessions

    if current_role == 'trainer':
        hero_message = (
            f'Manage {len(user_students)} swimmers and '
            f'{len(user_bookings)} bookings from one place.'
        )
    else:
        hero_message = (
            'Track sessions, bookings, payments and swimmer progress '
            'from one place.'
        )

    next_session_name = '--'
    next_session_date = '--'
    next_session_time = '--'
    guest_upcoming_sessions = []

    trainer_upcoming_slots = []
    trainer_remaining_slots = 0

    upcoming_sessions = []

    for booking in user_bookings:
        booking_time = (booking.get('time') or '').strip()

        for session_date in booking.get('calendar_dates', []):
            try:
                session_datetime = datetime.strptime(
                    f"{session_date} {booking_time}",
                    '%Y-%m-%d %I:%M %p'
                )

                current_time = ist_now.replace(tzinfo=None)
                next_24_hours = current_time + timedelta(hours=24)

                if current_time <= session_datetime <= next_24_hours:
                    upcoming_sessions.append({
                        'datetime': session_datetime,
                        'student': booking.get('student', '--'),
                        'time': booking_time
                    })
            except Exception:
                continue

    if current_role == 'trainer':
        slot_counts = {}

        for upcoming_session in upcoming_sessions:
            date_text = upcoming_session['datetime'].strftime('%d %b')
            time_text = upcoming_session['datetime'].strftime('%I:%M %p')
            slot_key = (date_text, time_text)

            if slot_key not in slot_counts:
                slot_counts[slot_key] = {
                    'count': 0,
                    'swimmers': []
                }

            slot_counts[slot_key]['count'] += 1
            slot_counts[slot_key]['swimmers'].append(
                upcoming_session.get('student', '--')
            )
        sorted_slots = sorted(
            slot_counts.items(),
            key=lambda x: datetime.strptime(
                f"{x[0][0]} {x[0][1]}",
                "%d %b %I:%M %p"
            )
        )
        trainer_remaining_slots = max(len(sorted_slots) - 3, 0)
        trainer_upcoming_slots = [
            {
                'date': date_text,
                'slot': time_text,
                'count': slot_data['count'],
                'swimmer_names': ', '.join(slot_data['swimmers'][:2]) + (
                    f" +{len(slot_data['swimmers']) - 2} More"
                    if len(slot_data['swimmers']) > 2 else ''
                )
            }
            for (date_text, time_text), slot_data in sorted_slots[:3]
        ]

    elif upcoming_sessions:
        sorted_sessions = sorted(
            upcoming_sessions,
            key=lambda x: x['datetime']
        )

        guest_upcoming_sessions = [
            {
                'name': s['student'],
                'date': s['datetime'].strftime('%d %b'),
                'time': s['time']
            }
            for s in sorted_sessions[:5]
        ]

        next_session = sorted_sessions[0]

        next_session_name = next_session['student']
        next_session_date = next_session['datetime'].strftime('%d %b')
        next_session_time = next_session['time']

    # -----------------------------
    # V0039.4 Real Payment Summary Data
    # -----------------------------
    # V0042.0.3 Payment Summary Rework
    total_packages = len(user_bookings)

    active_packages = sum(
        1 for b in user_bookings
        if not b.get('is_completed', False)
    )

    completed_packages = sum(
        1 for b in user_bookings
        if b.get('is_completed', False)
    )

    active_package_name = 'No Package'
    active_package_valid_till = '--'
    package_status = 'Active'

    received_amount = sum(
        int(b.get('fee', 0) or 0)
        for b in user_bookings
        if str(b.get('status', '')).lower() == 'paid'
    )

    pending_amount = sum(
        int(b.get('fee', 0) or 0)
        for b in user_bookings
        if str(b.get('status', '')).lower() != 'paid'
    )

    active_booking = None

    for booking in sorted(
        user_bookings,
        key=lambda b: str(b.get('end_date', '')),
        reverse=True
    ):
        if not booking.get('is_completed', False):
            active_booking = booking
            break

    if active_booking:
        active_package_name = active_booking.get('package', 'No Package')

        valid_till = active_booking.get('end_date')
        if valid_till:
            try:
                active_package_valid_till = datetime.strptime(
                    str(valid_till),
                    '%Y-%m-%d'
                ).strftime('%d %b %Y')
            except Exception:
                active_package_valid_till = str(valid_till)

        try:
            expiry_date = datetime.strptime(
                str(active_booking.get('end_date')),
                '%Y-%m-%d'
            ).date()

            if expiry_date < ist_now.date():
                package_status = 'Expired'
        except Exception:
            pass

    # -----------------------------
    # V0039.5 My Swimmers Insights
    # -----------------------------
    enriched_students = []

    for swimmer in user_students:
        swimmer_name = (swimmer.get('name') or '').strip()

        swimmer_bookings = [
            b for b in user_bookings
            if (b.get('student') or '').strip().lower() == swimmer_name.lower()
        ]

        completed_total = sum(
            int(b.get('completed_classes', 0) or 0)
            for b in swimmer_bookings
        )

        sessions_total = sum(
            int(b.get('total_classes', 0) or 0)
            for b in swimmer_bookings
        )

        next_session = ''
        future_dates = []

        for booking in swimmer_bookings:
            for session_date in booking.get('calendar_dates', []):
                try:
                    dt = datetime.strptime(session_date, '%Y-%m-%d').date()
                    if dt >= ist_now.date():
                        future_dates.append(dt)
                except Exception:
                    pass

        if future_dates:
            next_session = min(future_dates).strftime('%d %b %Y')

        active_package = ''
        active_booking_for_swimmer = None

        for booking in sorted(
            swimmer_bookings,
            key=lambda b: str(b.get('end_date', '')),
            reverse=True
        ):
            if not booking.get('is_completed', False):
                active_booking_for_swimmer = booking
                break

        if active_booking_for_swimmer:
            active_package = active_booking_for_swimmer.get('package', '')

        swimmer_copy = dict(swimmer)
        swimmer_copy['completed_sessions'] = completed_total
        swimmer_copy['total_sessions'] = sessions_total
        swimmer_copy['next_session'] = next_session
        swimmer_copy['package'] = active_package

        enriched_students.append(swimmer_copy)

    user_students = enriched_students

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
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        remaining_sessions=remaining_sessions,
        makeup_sessions=makeup_sessions,
        location_suggestions=location_suggestions,
        current_month_name=current_month_name,
        today_day=today_day,
        booked_dates=booked_dates,
        makeup_dates=makeup_dates,
        calendar_days=calendar_days,
        notification_count=notification_count,
        hero_message=hero_message,
        current_date_display=current_date_display,
        next_session_name=next_session_name,
        next_session_date=next_session_date,
        next_session_time=next_session_time,
        guest_upcoming_sessions=guest_upcoming_sessions,
        trainer_upcoming_slots=trainer_upcoming_slots,
        trainer_remaining_slots=trainer_remaining_slots,
        active_package_name=active_package_name,
        active_package_valid_till=active_package_valid_till,
        package_status=package_status,
        total_packages=total_packages,
        active_packages=active_packages,
        completed_packages=completed_packages,
        received_amount=received_amount,
        pending_amount=pending_amount,
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

# -----------------------------
# V0040.0 Navigation Refactor
# -----------------------------
@app.route('/booking')
def booking_page():
    if 'user_name' not in session:
        return redirect(url_for('index'))

    data = load_data()

    current_user = session.get('user_name')
    current_phone = session.get('phone')
    current_role = session.get('role', 'guest')

    if current_role == 'trainer':
        user_students = data.get('students', [])
        user_bookings = data.get('bookings', [])
    else:
        user_students = [
            s for s in data.get('students', [])
            if isinstance(s, dict)
            and (s.get('owner_name') or '').strip().lower() == current_user
            and s.get('owner_phone') == current_phone
        ]

        user_bookings = [
            b for b in data.get('bookings', [])
            if (b.get('owner_name') or '').strip().lower() == current_user
            and b.get('owner_phone') == current_phone
        ]

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
        'booking.html',
        role=current_role,
        user_name=current_user,
        students=user_students,
        bookings=user_bookings,
        location_suggestions=location_suggestions
    )


@app.route('/my-bookings')
def my_bookings_page():
    if 'user_name' not in session:
        return redirect(url_for('index'))

    data = load_data()

    current_user = session.get('user_name')
    current_phone = session.get('phone')
    current_role = session.get('role', 'guest')

    if current_role == 'trainer':
        user_bookings = data.get('bookings', [])
    else:
        user_bookings = [
            b for b in data.get('bookings', [])
            if (b.get('owner_name') or '').strip().lower() == current_user
            and b.get('owner_phone') == current_phone
        ]

    return render_template(
        'my_bookings.html',
        bookings=user_bookings,
        role=current_role,
        user_name=current_user
    )


@app.route('/calendar')
def calendar_page():
    if 'user_name' not in session:
        return redirect(url_for('index'))

    data = load_data()

    current_user = session.get('user_name')
    current_phone = session.get('phone')
    current_role = session.get('role', 'guest')

    if current_role == 'trainer':
        user_bookings = data['bookings']
    else:
        user_bookings = [
            b for b in data['bookings']
            if (b.get('owner_name') or '').strip().lower() == current_user
            and b.get('owner_phone') == current_phone
        ]

    return render_template(
        'calendar.html',
        bookings=user_bookings,
        role=current_role,
        user_name=current_user
    )


@app.route('/payments')
def payments_page():
    if 'user_name' not in session:
        return redirect(url_for('index'))

    data = load_data()

    current_user = session.get('user_name')
    current_phone = session.get('phone')
    current_role = session.get('role', 'guest')

    # Restore booking filtering before payment reminder processing
    if current_role == 'trainer':
        user_bookings = data.get('bookings', [])
    else:
        user_bookings = [
            b for b in data.get('bookings', [])
            if (b.get('owner_name') or '').strip().lower() == current_user
            and b.get('owner_phone') == current_phone
        ]

    if current_role == 'trainer':
        reminder_conn = get_pg_connection()
        reminder_cursor = reminder_conn.cursor()

        for booking in user_bookings:
            try:
                payment_status = str(
                    booking.get('status', '')
                ).strip().lower()

                remaining_classes = booking.get('remaining_classes', 0)
                is_completed = booking.get('is_completed', False)

                if (
                    payment_status == 'paid'
                    and remaining_classes == 0
                    and is_completed
                ):
                    try:
                        send_package_completion_email(booking)
                    except Exception:
                        pass
                    continue

                if (
                    booking.get('remaining_classes', 0) <= 3
                    and payment_status != 'paid'
                    and not booking.get('payment_reminder_sent', False)
                ):
                    send_payment_reminder_email(booking)

                    reminder_cursor.execute(
                        '''
                        UPDATE bookings
                        SET
                            payment_reminder_sent = TRUE,
                            payment_reminder_sent_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        ''',
                        (booking.get('id'),)
                    )

            except Exception as exc:
                print('PAYMENT REMINDER ERROR:', exc)

        reminder_conn.commit()
        reminder_conn.close()

    # V0044.2 - Total Outstanding Amount
    total_pending_amount = sum(
        int(b.get('fee', 0) or 0)
        for b in user_bookings
        if str(b.get('status', '')).strip().lower() != 'paid'
    )

    return render_template(
        'payments.html',
        bookings=user_bookings,
        role=current_role,
        user_name=current_user,
        total_pending_amount=total_pending_amount,
        account_holder_name=get_setting('account_holder_name', ''),
        trainer_phone=get_setting('trainer_phone', ''),
        upi_id=get_setting('upi_id', '')
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

            conn = get_pg_connection()
            cursor = conn.cursor()

            cursor.execute("""
INSERT INTO user_activity (
    user_name,
    phone,
    role
)
VALUES (%s, %s, %s)
""", (
    'Trainer',
    '',
    'trainer'
))

            conn.commit()
            conn.close()

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

        conn = get_pg_connection()
        cursor = conn.cursor()

        cursor.execute("""
INSERT INTO user_activity (
    user_name,
    phone,
    role
)
VALUES (%s, %s, %s)
""", (
    normalized_name,
    phone,
    'guest'
))

        conn.commit()
        conn.close()

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

    return redirect(url_for('booking_page'))

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

    return redirect(url_for('booking_page'))

@app.route('/book', methods=['POST'])
def book():
    if session.get('role') == 'trainer':
        flash('Trainer cannot create bookings directly')
        return redirect(url_for('index'))
    data = load_data()
    # Enhanced validation and logic for booking
    student = request.form['student']
    date_str = request.form['date']
    time_str = (request.form.get('time') or '').strip()

    if not time_str:
        print('DEBUG BOOK FORM KEYS:', list(request.form.keys()))
        flash('Please select a valid time slot before confirming booking.', 'warning')
        return redirect('/booking')
    email = (request.form.get('email') or '').strip()
    package = request.form.get('package', 'Single')
    end_date = request.form.get('end_date', date_str)
    persons = request.form.get('persons', 1)

    # Default fee based on package and group discount.
    session_count = None

    if package == 'Monthly':
        selected_days = request.form.get('selected_days', '')
        session_count = len([
            day.strip()
            for day in selected_days.split(',')
            if day.strip()
        ])

    elif package == 'Custom':
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

    # V0044.0 - Custom package fee is calculated by the frontend fee engine.
    if package == 'Custom':
        try:
            fee = int(float(request.form.get('fee', 0) or 0))
        except Exception:
            fee = 0

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

    conn = get_pg_connection()
    cursor = conn.cursor()
    booking_code = generate_booking_code(cursor)
    print('GENERATED BOOKING CODE:', booking_code)

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
            return redirect('/booking?location_conflict=true')

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
                flash(
                    'Duplicate booking already exists.',
                    'warning'
                )
                return redirect('/booking?booking_conflict=true')

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
        "booking_code": booking_code,
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
        swimmer_conn = get_pg_connection()
        swimmer_cursor = swimmer_conn.cursor()

        swimmer_cursor.execute('''
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

        swimmer_conn.commit()
        swimmer_conn.close()

    cursor.execute('''
    INSERT INTO bookings (
        id,
        booking_code,
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
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        new_booking['id'],
        new_booking['booking_code'],
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

    return redirect('/my-bookings?booking_success=true')


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
    old_values = {
        'student': booking.get('student', ''),
        'start_date': booking.get('start_date', ''),
        'end_date': booking.get('end_date', ''),
        'package': booking.get('package', ''),
        'selected_days': booking.get('selected_days', ''),
        'location': booking.get('location', ''),
        'time': booking.get('time', ''),
        'fee': booking.get('fee', ''),
        'persons': booking.get('persons', '')
    }

    # Get updated values
    student = request.form['student']
    date_str = request.form['date']
    time_str = (request.form.get('time') or '').strip()

    if not time_str:
        print('DEBUG UPDATE FORM KEYS:', list(request.form.keys()))
        flash('Please select a valid time slot before saving changes.', 'warning')
        return redirect(url_for('edit_booking', booking_id=booking_id))

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

    # V0044.0 - Custom package fee is calculated by the frontend fee engine.
    if package == 'Custom':
        try:
            fee = int(float(request.form.get('fee', 0) or 0))
        except Exception:
            fee = 0

    # Fee was already calculated above using calculate_discounted_fee().
    # Do not recalculate here, otherwise Edit Booking can overwrite the
    # correct pricing engine result (for example Monthly 2-days becoming ₹9000).
    # Trainer can still manually override the fee.
    # Only the old package/day-based recalculation was removed.
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
                flash(
                    'Duplicate booking already exists.',
                    'warning'
                )
                return redirect(
                    url_for('edit_booking', booking_id=booking_id)
                )

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

    changes = []

    field_labels = {
        'student': 'Swimmer',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'package': 'Package',
        'selected_days': 'Selected Days',
        'location': 'Location',
        'time': 'Time',
        'fee': 'Fee',
        'persons': 'Persons'
    }

    for field, label in field_labels.items():
        old_value = str(old_values.get(field, ''))
        new_value = str(booking.get(field, ''))

        if old_value != new_value:
            changes.append({
                'field': label,
                'old': old_value,
                'new': new_value
            })

    conn.commit()
    conn.close()

    if changes:
        print('BOOKING UPDATED EMAIL:', changes)

        # Send updated-booking email to swimmer/owner.
        send_booking_updated_email(booking, changes)

        # Send trainer/admin notification as well.
        trainer_booking = dict(booking)
        trainer_booking['update_changes'] = changes
        send_booking_notification(trainer_booking)

    # flash("Booking updated successfully")
    return redirect('/my-bookings')


# --- Update Payment Status Route ---
@app.route('/update_payment_status/<booking_id>', methods=['POST'])
def update_payment_status(booking_id):
    if 'user_name' not in session:
        return redirect(url_for('index'))

    new_status = (request.form.get('status') or '').strip()
    print('=' * 60)
    print('PAYMENT UPDATE REQUEST')
    print('Booking ID:', booking_id)
    print('Role:', session.get('role'))
    print('Requested Status:', new_status)
    print('=' * 60)

    allowed_statuses = [
        'Not Paid',
        'Pending Verification',
        'Paid'
    ]

    if new_status not in allowed_statuses:
        flash('Invalid payment status selected')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    role = session.get('role')

    # -------------------------
    # TRAINER VERIFICATION FLOW
    # -------------------------
    if role == 'trainer':

        print('TRAINER FLOW')
        print('Saving status:', new_status)
        cursor.execute('''
        UPDATE bookings
        SET
            status = %s,
            payment_request = %s
        WHERE id = %s
        ''', (
            new_status,
            'Paid' if new_status == 'Paid' else 'Not Paid',
            booking_id
        ))

    # -------------------------
    # GUEST PAYMENT REQUEST FLOW
    # -------------------------
    else:

        # Guest selecting Paid means:
        # Request trainer verification.
        if new_status == 'Paid':
            actual_status = 'Pending Verification'
            actual_request = 'Paid'
        else:
            actual_status = 'Not Paid'
            actual_request = 'Not Paid'

        print('GUEST FLOW')
        print('Actual Status:', actual_status)
        print('Actual Request:', actual_request)
        print('Owner Name:', session.get('user_name'))
        print('Owner Phone:', session.get('phone'))
        print('SESSION USER:', repr(session.get('user_name')))
        print('SESSION PHONE:', repr(session.get('phone')))
        cursor.execute(
            '''
            SELECT owner_name, owner_phone, status, payment_request
            FROM bookings
            WHERE id = %s
            ''',
            (booking_id,)
        )

        booking_row = cursor.fetchone()

        print('DB Booking Row:', booking_row)
        if booking_row:
            print('DB OWNER NAME:', repr(booking_row[0]))
            print('DB OWNER PHONE:', repr(booking_row[1]))
        cursor.execute('''
        UPDATE bookings
        SET
            status = %s,
            payment_request = %s
        WHERE id = %s
        ''', (
            actual_status,
            actual_request,
            booking_id
        ))
        print('ROWS UPDATED:', cursor.rowcount)

    conn.commit()
    cursor.execute(
        '''
        SELECT status, payment_request
        FROM bookings
        WHERE id = %s
        ''',
        (booking_id,)
    )

    saved_row = cursor.fetchone()

    print('DB Saved Values:', saved_row)
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
    SELECT booking_code,
           student_name,
           owner_name,
           owner_phone,
           start_date,
           time,
           package,
           email
    FROM bookings
    WHERE id = %s
    ''', (booking_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        flash('Booking not found')
        return redirect(url_for('index'))

    booking_info = {
        'booking_code': row[0] or '',
        'student': row[1] or '',
        'owner_name': row[2] or '',
        'owner_phone': row[3] or '',
        'start_date': str(row[4]) if row[4] else '',
        'time': row[5] or '',
        'package': row[6] or '',
        'email': row[7] or ''
    }

    deleted_student = booking_info['student']
    owner_name = booking_info['owner_name']
    owner_phone = booking_info['owner_phone']
    start_date = booking_info['start_date']
    booking_time_str = booking_info['time']

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

            send_booking_deleted_email(booking_info)
            send_booking_deleted_alert(booking_info)

            flash(f'Booking deleted for {deleted_student}')
            return redirect(url_for('my_bookings_page'))

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
        return redirect(url_for('my_bookings_page'))

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

    send_booking_deleted_email(booking_info)
    send_booking_deleted_alert(booking_info)

    flash(f'Booking deleted for {deleted_student}')
    return redirect(url_for('my_bookings_page'))


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