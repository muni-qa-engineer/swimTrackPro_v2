"""Booking creation and editing routes."""

from datetime import datetime, timedelta

from flask import flash, redirect, render_template, request, session, url_for

from services.booking_engine import (
    generate_booking_code,
    generate_booking_id,
    generate_recurring_dates,
)
from services.email_service import send_booking_confirmation_email
from services.pricing_service import calculate_discounted_fee
from swimtrackpro.runtime import get_pg_connection, load_data


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
    # Recurring-date Trainer Location Conflict Check & Group Swimmer Handling
    # -------------------------------------------------
    new_location = (request.form.get('location') or '').strip().lower()
    # group_swimmers = []
    group_swimmers = set()
    for b in data['bookings']:
        try:
            existing_time = (b.get('time') or '').strip()
            existing_location = (b.get('location') or '').strip().lower()
            existing_start = str(b.get('start_date', ''))
            existing_end = str(b.get('end_date', b.get('start_date', '')))
            existing_days = b.get('selected_days', '')
            existing_booking_dates = generate_recurring_dates(
                existing_start,
                existing_end,
                existing_days
            )
            overlapping_dates = set(new_booking_dates) & set(existing_booking_dates)
            if not overlapping_dates:
                continue
            if existing_time != time_str:
                continue
            if existing_location != new_location:
                # Pick the first overlapping date for message
                conflict_date = sorted(overlapping_dates)[0]
                conflict_dt = datetime.strptime(conflict_date, '%Y-%m-%d')
                conflict_date_str = conflict_dt.strftime('%d %b %Y')
                flash(
                    f'Trainer already has a session with {b.get("student", "another swimmer")} at {b.get("location", "")} on {conflict_date_str} at {existing_time}. Please choose another time or location.',
                    'warning'
                )
                return redirect('/booking?location_conflict=true')
            else:
                # Same location, group booking: collect swimmer names except current student
                group_swimmer_name = b.get('student')
                if group_swimmer_name and group_swimmer_name.strip().lower() != student.strip().lower():
                    # group_swimmers.append(group_swimmer_name)
                    group_swimmers.add(group_swimmer_name)
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

    # Convert group_swimmers set to sorted list for deterministic indexing
    group_swimmers = sorted(group_swimmers)
    # Flash group swimmer info if needed
    if group_swimmers:
        if len(group_swimmers) == 1:
            flash(f'You are swimming along with {group_swimmers[0]}.', 'info')
        else:
            name1 = group_swimmers[0]
            name2 = group_swimmers[1] if len(group_swimmers) > 1 else ''
            others_count = len(group_swimmers) - 2
            if others_count > 0:
                flash(f'You are swimming along with {name1}, {name2} and {others_count} others.', 'info')
            else:
                flash(f'You are swimming along with {name1}, {name2}.', 'info')

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

    # Send swimmer confirmation email.
    send_booking_confirmation_email(new_booking)

    return redirect('/my-bookings?booking_success=true')

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
    selected_days = request.form.getlist('selected_days')
    selected_days_str = ', '.join(selected_days)

    if package == 'Monthly':
        session_count = len([
            day.strip()
            for day in selected_days
            if day.strip()
        ])

    elif package == 'Custom':
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

    # --- Recurring-date Trainer Location Conflict Check (same as in book()) ---
    new_location = (request.form.get('location') or '').strip().lower()
    for b in data['bookings']:
        try:
            # Skip the booking currently being edited
            if str(b.get('id')) == str(booking_id):
                continue
            existing_time = (b.get('time') or '').strip()
            existing_location = (b.get('location') or '').strip().lower()
            existing_start = str(b.get('start_date', ''))
            existing_end = str(b.get('end_date', b.get('start_date', '')))
            existing_days = b.get('selected_days', '')
            existing_booking_dates = generate_recurring_dates(
                existing_start,
                existing_end,
                existing_days
            )
            overlapping_dates = set(new_booking_dates) & set(existing_booking_dates)
            if not overlapping_dates:
                continue
            if existing_time != time_str:
                continue
            if existing_location != new_location:
                # Pick the first overlapping date for message
                conflict_date = sorted(overlapping_dates)[0]
                conflict_dt = datetime.strptime(conflict_date, '%Y-%m-%d')
                conflict_date_str = conflict_dt.strftime('%d %b %Y')
                flash(
                    f'Trainer already has a session with {b.get("student", "another swimmer")} at {b.get("location", "")} on {conflict_date_str} at {existing_time}. Please choose another time or location.',
                    'warning'
                )
                return redirect(url_for('edit_booking', booking_id=booking_id))
        except Exception:
            continue

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
        print('BOOKING UPDATED:', changes)

    # flash("Booking updated successfully")
    return redirect('/my-bookings')

def register_bookings_routes(app):
    app.add_url_rule('/book', endpoint='book', view_func=book, methods=['POST'])
    app.add_url_rule('/edit/<booking_id>', endpoint='edit_booking', view_func=edit_booking)
    app.add_url_rule('/update/<booking_id>', endpoint='update_booking', view_func=update_booking, methods=['POST'])
