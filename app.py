import psycopg2
from flask import Flask
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from services.booking_engine import generate_recurring_dates
from swimtrackpro import runtime
from swimtrackpro.routes.authentication import register_authentication_routes
from swimtrackpro.routes.bookings import register_bookings_routes
from swimtrackpro.routes.dashboard import register_dashboard_routes
from swimtrackpro.routes.deletions import register_deletions_routes
from swimtrackpro.routes.general import register_general_routes
from swimtrackpro.routes.makeup import register_makeup_routes
from swimtrackpro.routes.pages import register_page_routes
from swimtrackpro.routes.payments import register_payments_routes
from swimtrackpro.routes.swimmers import register_swimmer_routes

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
        SELECT id, credit_id, booking_id, original_date, requested_date, status
        FROM makeup_requests
        ORDER BY requested_date
    """)
    all_requests = cursor.fetchall()

    requests_by_booking = {}
    for row in all_requests:
        bid = str(row[2])
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

        pending_request = next((r for r in booking_requests if r[5] == 'pending'), None)
        approved_request = next((r for r in booking_requests if r[5] == 'approved'), None)

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

        # Add new fields for Calendar UI make-up workflow state
        booking['pending_request_id'] = pending_request[0] if pending_request else None
        booking['approved_request_id'] = approved_request[0] if approved_request else None
        booking['skip_remaining'] = len(available_credits)
        booking['skip_eligible'] = True
        booking['valid_until'] = booking['end_date']
        booking['makeup_used'] = approved_request is not None

        # Makeup requests (expanded for Calendar UI)
        booking['makeup_requests'] = [
            {
                'id': r[0],
                'credit_id': r[1],
                'original_date': str(r[3]),
                'requested_date': str(r[4]),
                'status': r[5]
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
runtime.configure(
    get_pg_connection=get_pg_connection,
    load_data=load_data,
)

register_dashboard_routes(app)
register_page_routes(
    app,
    get_pg_connection=get_pg_connection,
    load_data=load_data,
)
register_authentication_routes(
    app,
    get_pg_connection=get_pg_connection,
    admin_username=ADMIN_USERNAME,
    admin_password=ADMIN_PASSWORD,
)
register_swimmer_routes(
    app,
    get_pg_connection=get_pg_connection,
    load_data=load_data,
)
register_bookings_routes(app)
register_payments_routes(app)
register_deletions_routes(app)
register_makeup_routes(app)
register_general_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
