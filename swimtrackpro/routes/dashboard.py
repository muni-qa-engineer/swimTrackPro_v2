"""Dashboard route."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import render_template, session

from services.settings_service import get_setting
from swimtrackpro.runtime import get_pg_connection, load_data


def index():
    if 'user_name' not in session:
        return render_template('login.html')
    
    data = load_data()  # Loads data from PostgreSQL
    
    current_user = session.get('user_name')
    current_phone = session.get('phone')
    current_role = session.get('role', 'guest')

    welcome_text = f"Welcome Back, {current_user.title()}"

    if current_role == 'admin':
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Fetch trainers
        cursor.execute("SELECT username, name, phone, email, experience, qualification, currently_working, residence_location, rating, is_approved FROM trainers ORDER BY name")
        trainers_list = []
        for row in cursor.fetchall():
            trainers_list.append({
                'username': row[0],
                'name': row[1],
                'phone': row[2],
                'email': row[3],
                'experience': row[4],
                'qualification': row[5],
                'currently_working': row[6],
                'residence_location': row[7],
                'rating': float(row[8]) if row[8] else 5.0,
                'is_approved': row[9]
            })
            
        # Fetch user activities
        cursor.execute("SELECT user_name, phone, role, current_login, previous_login FROM user_activity ORDER BY current_login DESC")
        activities_list = []
        for row in cursor.fetchall():
            activities_list.append({
                'user_name': row[0],
                'phone': row[1],
                'role': row[2],
                'current_login': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else '--',
                'previous_login': row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else '--'
            })
            
        conn.close()

        # Calculate today's sessions and weekly distribution from full bookings data
        today_str = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d')
        today_sessions = []
        
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_counts = {d: 0 for d in days_of_week}
        
        for b in data.get('bookings', []):
            # Check for today's sessions
            if today_str in b.get('calendar_dates', []):
                today_sessions.append({
                    'time': b.get('time', '06:00 AM'),
                    'student': b.get('student', '--'),
                    'package': b.get('package', '--'),
                    'trainer_username': b.get('trainer_username', 'asdf'),
                    'booking_id': b.get('id')
                })
            # Count selected days distribution
            sel_days = b.get('selected_days', '')
            if sel_days:
                for day in days_of_week:
                    if day.lower() in sel_days.lower():
                        day_counts[day] += 1
                        
        chart_data = [day_counts[d] for d in days_of_week]
        
        return render_template(
            'admin_dashboard.html',
            welcome_text=welcome_text,
            trainers=trainers_list,
            bookings=data.get('bookings', []),
            students=data.get('students', []),
            today_sessions=today_sessions,
            activities=activities_list,
            chart_data=chart_data
        )

    try:
        conn = get_pg_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT previous_login
            FROM user_activity
            WHERE LOWER(user_name) = LOWER(%s)
              AND role = %s
            ''',
            (current_user, current_role)
        )

        row = cursor.fetchone()
        conn.close()

        if not row or row[0] is None:
            welcome_text = f"Hi {current_user.title()}, Welcome"

    except Exception:
        pass

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

    # Fetch trainer-specific notices
    if current_role == 'trainer':
        trainer_user = session.get("trainer_username") or "asdf"
        cursor.execute("SELECT notice FROM trainers WHERE username = %s", (trainer_user,))
        row_notice = cursor.fetchone()
        notice_message = row_notice[0] if (row_notice and row_notice[0]) else ""
        if not notice_message:
            notice_message = "Welcome to SwimTrackPro! Use • to separate multiple announcements."
    else:
        assigned_usernames = list(set([b.get("trainer_username", "asdf") for b in user_bookings if b.get("trainer_username")]))
        if not assigned_usernames:
            assigned_usernames = ["asdf"]

        placeholders = ", ".join(["%s"] * len(assigned_usernames))
        cursor.execute(f"SELECT name, notice FROM trainers WHERE username IN ({placeholders})", tuple(assigned_usernames))
        rows_notice = cursor.fetchall()
        
        announcements_list = []
        for name, notice in rows_notice:
            if notice:
                for ann in notice.split("•"):
                    ann_text = ann.strip()
                    if ann_text:
                        announcements_list.append(f"Coach {name.title()}: {ann_text}")
        if announcements_list:
            notice_message = " • ".join(announcements_list)
        else:
            notice_message = ""

    # Build list of notifications
    notification_list = []
    
    if current_role == 'trainer':
        for b in user_bookings:
            if str(b.get('status', '')).lower() == 'pending verification':
                notification_list.append(f"💰 Payment verification needed for {b.get('student', 'Swimmer')}'s {b.get('package')} package.")
        for b in user_bookings:
            if b.get('delete_requested'):
                notification_list.append(f"🗑️ Deletion requested by {b.get('student', 'Swimmer')} for booking #{b.get('id')}.")
        for b in user_bookings:
            for req in b.get('makeup_requests', []):
                if req.get('status') == 'pending':
                    notification_list.append(f"⏳ Pending Make-up request for {b.get('student', 'Swimmer')} on {req.get('requested_date')}.")
    else:
        for b in user_bookings:
            if str(b.get('status', '')).lower() != 'paid':
                notification_list.append(f"💰 Payment due: Please complete payment of ₹{b.get('fee')} for {b.get('student')}'s {b.get('package')} package.")
        for b in user_bookings:
            if b.get('has_available_makeup_credit'):
                notification_list.append(f"🔄 Make-up credit available for {b.get('student')} (Valid until {b.get('valid_until')}).")
        if announcements_list:
            for ann in announcements_list:
                notification_list.append(f"📢 Notice: {ann}")
                
    notification_count = len(notification_list)

    conn.close()

    return render_template(
        'dashboard.html',
        user_name=session['user_name'],
        role=session.get('role', 'guest'),
        notification_list=notification_list,
        welcome_text=welcome_text,
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
        notice_message=notice_message,
        account_holder_name=get_setting("account_holder_name", ""),
        trainer_phone=get_setting("trainer_phone", ""),
        upi_id=get_setting("upi_id", "")
    )

def register_dashboard_routes(app):
    app.add_url_rule('/', endpoint='index', view_func=index)
