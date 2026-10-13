"""Booking deletion and approval routes."""

import re
from datetime import datetime, timedelta
from flask import flash, redirect, session, url_for, request, jsonify
from swimtrackpro.runtime import get_pg_connection


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
           email,
           trainer_username,
           created_by
    FROM bookings
    WHERE id = %s
    ''', (str(booking_id),))

    row = cursor.fetchone()

    if not row:
        conn.close()
        flash('Booking not found', 'warning')
        return redirect(url_for('my_bookings_page'))

    # Authorization Check
    if role == 'admin':
        pass  # Admin can delete any booking
    elif role == 'trainer':
        trainer_user = (session.get('trainer_username') or '').strip().lower()
        trainer_name = (session.get('user_name') or '').strip().lower()
        booking_trainer = (row[8] or '').strip().lower()

        is_coach_authorized = (
            (bool(trainer_user) and booking_trainer == trainer_user) or
            (bool(trainer_name) and booking_trainer == trainer_name) or
            booking_trainer in ('', 'asdf', 'unassigned') or
            not bool(booking_trainer)
        )
        if not is_coach_authorized:
            conn.close()
            flash('Unauthorized action', 'danger')
            return redirect(url_for('my_bookings_page'))
    else:
        # Guest / User Level Check
        current_user = (session.get('user_name') or '').strip().lower()
        current_phone = (session.get('phone') or session.get('user_phone') or '').strip()
        user_clean_phone = re.sub(r'\D', '', current_phone)

        b_student = (row[1] or '').strip().lower()
        b_owner_name = (row[2] or '').strip().lower()
        b_owner_phone = re.sub(r'\D', '', str(row[3] or ''))
        b_created_by = (row[9] or '').strip().lower() if len(row) > 9 and row[9] else ''

        phone_match = bool(user_clean_phone) and bool(b_owner_phone) and (
            user_clean_phone == b_owner_phone or
            user_clean_phone.endswith(b_owner_phone) or
            b_owner_phone.endswith(user_clean_phone)
        )
        name_match = bool(current_user) and (
            b_owner_name == current_user or
            b_student == current_user or
            b_created_by == current_user or
            current_user in b_owner_name or
            b_owner_name in current_user
        )

        if not (phone_match or name_match):
            conn.close()
            flash('Unauthorized action', 'danger')
            return redirect(url_for('my_bookings_page'))

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

    # Delete related dependent records first to maintain DB integrity
    try:
        cursor.execute('DELETE FROM makeup_requests WHERE booking_id = %s', (str(booking_id),))
        cursor.execute('DELETE FROM makeup_credits WHERE booking_id = %s', (str(booking_id),))
        cursor.execute('DELETE FROM package_pause_audit WHERE booking_id = %s', (str(booking_id),))
    except Exception as e:
        print(f"Notice: cleanup dependent booking rows error: {e}")

    # Delete booking record
    cursor.execute('DELETE FROM bookings WHERE id = %s', (str(booking_id),))

    # Check if swimmer still has any other active bookings
    try:
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
    except Exception as e:
        print(f"Notice: cleanup student count error: {e}")

    conn.commit()
    conn.close()

    flash(f'Booking for {deleted_student} deleted successfully.', 'success')
    return redirect(url_for('my_bookings_page'))


def approve_delete(booking_id):
    if session.get('role') not in ('trainer', 'admin'):
        flash('Unauthorized action', 'danger')
        return redirect(url_for('my_bookings_page'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Load booking details before deletion
    cursor.execute('''
    SELECT student_name, owner_name, owner_phone, trainer_username
    FROM bookings
    WHERE id = %s
    ''', (str(booking_id),))

    row = cursor.fetchone()

    if not row:
        conn.close()
        flash('Booking not found', 'warning')
        return redirect(url_for('my_bookings_page'))

    if session.get('role') == 'trainer':
        trainer_user = (session.get('trainer_username') or '').strip().lower()
        trainer_name = (session.get('user_name') or '').strip().lower()
        booking_trainer = (row[3] or '').strip().lower()
        is_coach_authorized = (
            (bool(trainer_user) and booking_trainer == trainer_user) or
            (bool(trainer_name) and booking_trainer == trainer_name) or
            booking_trainer in ('', 'asdf', 'unassigned') or
            not bool(booking_trainer)
        )
        if not is_coach_authorized:
            conn.close()
            flash('Unauthorized action', 'danger')
            return redirect(url_for('my_bookings_page'))

    deleted_student = row[0]
    owner_name = row[1]
    owner_phone = row[2]

    # Delete related dependent records first
    try:
        cursor.execute('DELETE FROM makeup_requests WHERE booking_id = %s', (str(booking_id),))
        cursor.execute('DELETE FROM makeup_credits WHERE booking_id = %s', (str(booking_id),))
        cursor.execute('DELETE FROM package_pause_audit WHERE booking_id = %s', (str(booking_id),))
    except Exception as e:
        print(f"Notice: approve_delete cleanup error: {e}")

    # Permanently delete the booking
    cursor.execute('DELETE FROM bookings WHERE id = %s', (str(booking_id),))

    # Check if swimmer still has any bookings
    try:
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
    except Exception as e:
        print(f"Notice: approve_delete student cleanup error: {e}")

    conn.commit()
    conn.close()

    flash(f'Delete approved for {deleted_student}', 'success')
    return redirect(url_for('my_bookings_page'))


def reject_delete(booking_id):
    if session.get('role') not in ('trainer', 'admin'):
        flash('Unauthorized action', 'danger')
        return redirect(url_for('my_bookings_page'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT trainer_username FROM bookings WHERE id = %s', (str(booking_id),))
    row = cursor.fetchone()
    if not row:
        conn.close()
        flash('Booking not found', 'warning')
        return redirect(url_for('my_bookings_page'))

    if session.get('role') == 'trainer':
        trainer_user = (session.get('trainer_username') or '').strip().lower()
        trainer_name = (session.get('user_name') or '').strip().lower()
        booking_trainer = (row[0] or '').strip().lower()
        is_coach_authorized = (
            (bool(trainer_user) and booking_trainer == trainer_user) or
            (bool(trainer_name) and booking_trainer == trainer_name) or
            booking_trainer in ('', 'asdf', 'unassigned') or
            not bool(booking_trainer)
        )
        if not is_coach_authorized:
            conn.close()
            flash('Unauthorized action', 'danger')
            return redirect(url_for('my_bookings_page'))

    cursor.execute('''
    UPDATE bookings
    SET
        delete_requested = FALSE,
        delete_requested_at = NULL,
        delete_requested_by = NULL
    WHERE id = %s
    ''', (str(booking_id),))

    conn.commit()
    conn.close()

    flash('Delete request rejected', 'info')
    return redirect(url_for('my_bookings_page'))


def register_deletions_routes(app):
    app.add_url_rule('/delete/<booking_id>', endpoint='delete_booking', view_func=delete_booking, methods=['GET', 'POST'])
    app.add_url_rule('/approve_delete/<booking_id>', endpoint='approve_delete', view_func=approve_delete, methods=['POST'])
    app.add_url_rule('/reject_delete/<booking_id>', endpoint='reject_delete', view_func=reject_delete, methods=['POST'])
