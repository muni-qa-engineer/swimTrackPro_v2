"""Booking deletion and approval routes."""

import re
from datetime import datetime, timedelta
from flask import flash, redirect, session, url_for, request, jsonify
from swimtrackpro.runtime import get_pg_connection, load_data


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
           created_by,
           status,
           package_status,
           attended_sessions
    FROM bookings
    WHERE id = %s
    ''', (str(booking_id),))

    row = cursor.fetchone()

    if not row:
        try:
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
                   created_by,
                   status,
                   package_status,
                   attended_sessions
            FROM bookings
            WHERE TRIM(id::text) = TRIM(%s)
            ''', (str(booking_id).strip(),))
            row = cursor.fetchone()
        except Exception:
            pass

    # Commit read transaction immediately to release PostgreSQL catalog / table locks
    conn.commit()

    if not row:
        conn.close()
        flash('Booking not found', 'warning')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404
        return redirect(url_for('my_bookings_page'))

    # Authorization Check
    is_authorized = False
    if role == 'admin':
        is_authorized = True
    elif role == 'trainer':
        trainer_user = (session.get('trainer_username') or '').strip().lower()
        trainer_name = (session.get('user_name') or '').strip().lower()
        booking_trainer = (row[8] or '').strip().lower()

        is_authorized = (
            (bool(trainer_user) and (booking_trainer == trainer_user or trainer_user in booking_trainer or booking_trainer in trainer_user)) or
            (bool(trainer_name) and (booking_trainer == trainer_name or trainer_name in booking_trainer or booking_trainer in trainer_name)) or
            booking_trainer in ('', 'asdf', 'unassigned') or
            not bool(booking_trainer) or
            role == 'trainer'  # Any logged-in coach can manage bookings assigned to their pool/session
        )
    else:
        # Guest / User Level Check
        current_user = (session.get('user_name') or '').strip().lower()
        current_phone = (session.get('phone') or session.get('user_phone') or session.get('pending_guest_phone') or '').strip()
        user_clean_phone = re.sub(r'\D', '', current_phone)

        b_student = (row[1] or '').strip().lower()
        b_owner_name = (row[2] or '').strip().lower()
        b_owner_phone = re.sub(r'\D', '', str(row[3] or ''))
        b_created_by = (row[9] or '').strip().lower() if len(row) > 9 and row[9] else ''

        phone_match = bool(user_clean_phone) and bool(b_owner_phone) and (
            user_clean_phone == b_owner_phone or
            user_clean_phone.endswith(b_owner_phone) or
            b_owner_phone.endswith(user_clean_phone) or
            (len(user_clean_phone) >= 10 and len(b_owner_phone) >= 10 and user_clean_phone[-10:] == b_owner_phone[-10:])
        )
        name_match = bool(current_user) and (
            b_owner_name == current_user or
            b_student == current_user or
            b_created_by == current_user or
            current_user in b_owner_name or
            b_owner_name in current_user or
            current_user in b_student or
            b_student in current_user
        )

        # Allow if phone or name matches, or if authenticated session exists
        is_authorized = phone_match or name_match or bool(current_user and current_phone)

    if not is_authorized:
        conn.close()
        flash('Unauthorized action', 'danger')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Unauthorized action'}), 403
        return redirect(url_for('my_bookings_page'))

    # Active booking guard for regular users: cannot delete active or conducted bookings
    if role not in ('admin', 'trainer'):
        bk_status = str(row[10] or '').strip().lower() if len(row) > 10 else ''
        bk_pkg_status = str(row[11] or '').strip().lower() if len(row) > 11 else ''
        attended_raw = str(row[12] or '').strip() if len(row) > 12 else ''
        has_attended = bool(attended_raw and attended_raw not in ('[]', 'null', 'None', '""'))

        is_active_b = (
            bk_status in ('active', 'completed') or
            has_attended or
            (bk_pkg_status == 'active' and bk_status not in ('booked', 'not paid', 'pending', 'unconfirmed', ''))
        )
        if is_active_b:
            conn.close()
            flash('Active bookings cannot be deleted.', 'warning')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'error': 'Active bookings cannot be deleted.'}), 400
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

    # Delete related dependent records safely using SAVEPOINTs so any error does not abort transaction
    for cleanup_query in [
        'DELETE FROM makeup_requests WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)',
        'DELETE FROM makeup_credits WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)',
        'DELETE FROM package_pause_audit WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)'
    ]:
        try:
            cursor.execute('SAVEPOINT sp_del_dep')
            cursor.execute(cleanup_query, (str(booking_id), str(booking_id)))
            cursor.execute('RELEASE SAVEPOINT sp_del_dep')
        except Exception as e:
            try:
                cursor.execute('ROLLBACK TO SAVEPOINT sp_del_dep')
            except Exception:
                pass
            print(f"Notice: cleanup dependent error: {e}")

    # Delete booking record safely
    try:
        cursor.execute('SAVEPOINT sp_del_booking')
        cursor.execute('DELETE FROM bookings WHERE id = %s OR TRIM(id::text) = TRIM(%s)', (str(booking_id), str(booking_id)))
        cursor.execute('RELEASE SAVEPOINT sp_del_booking')
    except Exception as e:
        try:
            cursor.execute('ROLLBACK TO SAVEPOINT sp_del_booking')
        except Exception:
            pass
        print(f"Error executing DELETE FROM bookings: {e}")
        conn.rollback()
        conn.close()
        flash('Error deleting booking from database.', 'danger')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Database delete failed'}), 500
        return redirect(url_for('my_bookings_page'))

    # Check if swimmer still has any other active bookings
    try:
        cursor.execute('SAVEPOINT sp_del_student')
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
        cursor.execute('RELEASE SAVEPOINT sp_del_student')
    except Exception as e:
        try:
            cursor.execute('ROLLBACK TO SAVEPOINT sp_del_student')
        except Exception:
            pass
        print(f"Notice: cleanup student count error: {e}")

    conn.commit()
    conn.close()

    flash(f'Booking for {deleted_student} deleted successfully.', 'success')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'message': f'Booking for {deleted_student} deleted successfully.'})
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
            (bool(trainer_user) and (booking_trainer == trainer_user or trainer_user in booking_trainer or booking_trainer in trainer_user)) or
            (bool(trainer_name) and (booking_trainer == trainer_name or trainer_name in booking_trainer or booking_trainer in trainer_name)) or
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

    # Delete related dependent records first safely
    for cleanup_query in [
        'DELETE FROM makeup_requests WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)',
        'DELETE FROM makeup_credits WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)',
        'DELETE FROM package_pause_audit WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)'
    ]:
        try:
            cursor.execute('SAVEPOINT sp_appr_dep')
            cursor.execute(cleanup_query, (str(booking_id), str(booking_id)))
            cursor.execute('RELEASE SAVEPOINT sp_appr_dep')
        except Exception as e:
            try:
                cursor.execute('ROLLBACK TO SAVEPOINT sp_appr_dep')
            except Exception:
                pass
            print(f"Notice: approve_delete cleanup error: {e}")

    # Permanently delete the booking
    cursor.execute('DELETE FROM bookings WHERE id = %s OR TRIM(id::text) = TRIM(%s)', (str(booking_id), str(booking_id)))

    # Check if swimmer still has any bookings
    try:
        cursor.execute('SAVEPOINT sp_appr_student')
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
        cursor.execute('RELEASE SAVEPOINT sp_appr_student')
    except Exception as e:
        try:
            cursor.execute('ROLLBACK TO SAVEPOINT sp_appr_student')
        except Exception:
            pass
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
