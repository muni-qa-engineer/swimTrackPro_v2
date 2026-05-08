import os, json, hashlib, sqlite3
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta

app = Flask(__name__)
from config import ADMIN_USERNAME, ADMIN_PASSWORD, SECRET_KEY
app.secret_key = SECRET_KEY

# --- CONFIG & PERSISTENCE ---
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'database' / 'swim_data.db'
DATA_FILE = "swim_data.json"  # Backup only

def generate_booking_id(student, start_date, time_str):
    return hashlib.md5(f"{student}{start_date}{time_str}".encode()).hexdigest()


# --- SQLite Persistence Layer ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Load students
    cursor.execute('SELECT * FROM students')
    student_rows = cursor.fetchall()

    students = []

    for s in student_rows:
        students.append({
            'name': s['student_name'],
            'owner_name': s['owner_name'],
            'owner_phone': s['owner_phone']
        })

    # Load bookings
    cursor.execute('SELECT * FROM bookings')
    booking_rows = cursor.fetchall()

    bookings = []

    for b in booking_rows:
        bookings.append({
            'id': b['id'],
            'student': b['student_name'],
            'created_by': b['created_by'],
            'start_date': b['start_date'],
            'end_date': b['end_date'],
            'package': b['package'],
            'selected_days': b['selected_days'],
            'location': b['location'],
            'persons': b['persons'],
            'time': b['time'],
            'fee': b['fee'],
            'status': b['status'],
            'payment_request': b['payment_request'],
            'owner_name': b['owner_name'],
            'owner_phone': b['owner_phone']
        })

    conn.close()

    return {
        'students': students,
        'bookings': bookings,
        'users': {}
    }


def save_data(students, bookings):
    conn = get_db_connection()
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
        ) VALUES (?, ?, ?)
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
            persons
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            int(booking.get('persons', 1))
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
    
    data = load_data() # Loads your swim_data.json
    
    current_user = session.get('user_name')
    current_phone = session.get('phone')
    current_role = session.get('role', 'guest')

    # ADMIN => view everything
    if current_role == 'admin':
        user_bookings = data['bookings']
        user_students = data.get('students', [])

    # GUEST => isolated data only
    else:
        user_bookings = [
            b for b in data['bookings']
            if b.get('owner_name') == current_user
            and b.get('owner_phone') == current_phone
        ]

        user_students = [
            s for s in data.get('students', [])
            if isinstance(s, dict)
            and s.get('owner_name') == current_user
            and s.get('owner_phone') == current_phone
        ]
        
    return render_template('dashboard.html', 
                           user_name=session['user_name'],
                           role=session.get('role', 'guest'),
                           bookings=user_bookings,
                           students=user_students)

@app.route('/login', methods=['POST'])
def login():
    role = (request.form.get('role') or '').lower()
    name = (request.form.get('name') or '').strip()
    password = (request.form.get('password') or '').strip()
    phone = (request.form.get('phone') or '').strip()

    # ADMIN LOGIN
    if role == 'admin':

        # if name == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        if name.lower() == ADMIN_USERNAME.lower() and password == ADMIN_PASSWORD:
            session['user_name'] = 'Admin'
            session['role'] = 'admin'
            return redirect(url_for('index'))

        flash('Invalid admin credentials')
        return redirect(url_for('index'))

    if role == "guest" and name:
        # Validate 10-digit phone number for guests
        if not phone.isdigit() or len(phone) != 10:
            flash("Invalid phone number. Please enter exactly 10 digits.")
            return redirect(url_for('index'))

        data = load_data()
        users = {}

        # Existing name check: Verify phone matches if user exists
        if name in users:
            if users[name] != phone:
                flash("This name is already registered with a different phone number.")
                return redirect(url_for('index'))

        # Existing phone check: Ensure phone isn't taken by a different name
        for existing_name, existing_phone in users.items():
            if existing_phone == phone and existing_name != name:
                flash("This phone number is already registered to another user.")
                return redirect(url_for('index'))

        # Register new user if they don't exist
        if name not in users:
            users[name] = phone

        # SQLite migration phase → skip JSON user persistence

        session['role'] = 'guest'
        # Set Guest session
        session['user_name'] = name
        session['phone'] = phone
        return redirect(url_for('index'))

    # Fallback if no valid role or name is provided
    else:
        flash("Please enter all required fields.")
        return redirect(url_for('index'))

@app.route('/add_swimmer', methods=['POST'])
def add_swimmer():
    if session.get('role') == 'admin':
        flash('Admin cannot add swimmers directly')
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

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO students (
        student_name,
        owner_name,
        owner_phone
    ) VALUES (?, ?, ?)
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
    data = load_data()

    current_user = session.get('user_name')
    current_phone = session.get('phone')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete swimmer
    cursor.execute('''
    DELETE FROM students
    WHERE student_name = ?
    AND owner_name = ?
    AND owner_phone = ?
    ''', (
        name,
        current_user,
        current_phone
    ))

    # Delete all bookings of that swimmer
    cursor.execute('''
    DELETE FROM bookings
    WHERE student_name = ?
    AND owner_name = ?
    AND owner_phone = ?
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
    if session.get('role') == 'admin':
        flash('Admin cannot create bookings directly')
        return redirect(url_for('index'))
    data = load_data()
    # Enhanced validation and logic for booking
    student = request.form['student']
    date_str = request.form['date']
    time_str = request.form['time']
    package = request.form.get('package', 'Single')
    end_date = request.form.get('end_date', date_str)
    fee = int(request.form.get('fee', 0))

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
    booking_time = datetime.strptime(time_str, '%I:%M %p')

    for b in data['bookings']:

        same_student = b.get('student') == student
        same_date = b.get('start_date') == date_str
        same_owner = b.get('owner_name') == session.get('user_name')

        if same_student and same_date and same_owner:

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
        "persons": request.form.get('persons', 1),
        "time": time_str,
        "fee": fee,
        "status": status,
        "payment_request": payment_choice,
        "owner_name": session.get('user_name'),
        "owner_phone": session.get('phone'),
    }
    conn = get_db_connection()
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
        owner_phone
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        new_booking['owner_phone']
    ))

    conn.commit()
    conn.close()

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

    # Render edit page with booking data
    return render_template('editBooking.html', booking=booking)

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
    fee = int(request.form.get('fee', 0))

    # Get selected class days
    selected_days = request.form.getlist('selected_days')

    # Update values
    booking['student'] = student
    booking['start_date'] = date_str
    booking['end_date'] = end_date
    booking['package'] = package
    booking['selected_days'] = ', '.join(selected_days)
    booking['location'] = request.form.get('location', '').strip()
    booking['time'] = time_str
    booking['fee'] = fee

    booking['persons'] = request.form.get('persons', 1)

    payment_choice = request.form.get('payment_status', 'Not Paid')
    booking['payment_request'] = payment_choice

    role = session.get('role')

    # Guest payment request flow
    if role != 'admin':

        if payment_choice == 'Paid':
            booking['status'] = 'Pending'
        else:
            booking['status'] = 'Not Paid'

    # Admin edit flow
    else:

        # Admin uses same edit dropdown
        if payment_choice == 'Paid':
            booking['status'] = 'Paid'
        else:
            booking['status'] = 'Not Paid'

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE bookings
    SET
        student_name = ?,
        start_date = ?,
        end_date = ?,
        package = ?,
        selected_days = ?,
        location = ?,
        time = ?,
        fee = ?,
        persons = ?,
        status = ?,
        payment_request = ?
    WHERE id = ?
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

@app.route('/delete/<booking_id>', methods=['POST'])
def delete_booking(booking_id):
    data = load_data()

    # Find booking index
    index = next((i for i, b in enumerate(data['bookings']) if b['id'] == booking_id), None)

    if index is None:
        flash("Booking not found")
        return redirect(url_for('index'))

    # Remove booking
    deleted_booking = data['bookings'].pop(index)

    deleted_student = deleted_booking.get('student')

    # Check if swimmer still has remaining bookings
    # Use deleted booking owner details instead of current session
    has_remaining_bookings = any(
        b.get('student', '').strip() == deleted_student.strip()
        and b.get('owner_name') == deleted_booking.get('owner_name')
        and b.get('owner_phone') == deleted_booking.get('owner_phone')
        for b in data['bookings']
    )

    # Remove swimmer if no bookings exist
    if not has_remaining_bookings:
        data['students'] = [
            s for s in data['students']
            if not (
                isinstance(s, dict)
                and s.get('name') == deleted_student
                and s.get('owner_name') == deleted_booking.get('owner_name')
                and s.get('owner_phone') == deleted_booking.get('owner_phone')
            )
        ]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete booking directly
    cursor.execute(
        'DELETE FROM bookings WHERE id = ?',
        (booking_id,)
    )

    # Remove swimmer if no remaining bookings exist
    if not has_remaining_bookings:
        cursor.execute('''
        DELETE FROM students
        WHERE TRIM(student_name) = TRIM(?)
        AND owner_name = ?
        AND owner_phone = ?
        ''', (
            deleted_student,
            deleted_booking.get('owner_name'),
            deleted_booking.get('owner_phone')
        ))

    conn.commit()
    conn.close()

    flash(f"Booking deleted for {deleted_booking['student']}")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)