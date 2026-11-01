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

    # Send booking cancellation notification email to swimmer and admin alert
    try:
        from services.email_service import send_booking_deleted_email, send_booking_deleted_alert
        send_booking_deleted_email(booking_info)
        send_booking_deleted_alert(booking_info)
    except Exception as mail_err:
        print("Booking deletion email notification error:", mail_err)

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
    SELECT student_name, owner_name, owner_phone, trainer_username, booking_code, email, start_date, time, package
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

    # Send booking cancellation notification email to swimmer and admin alert
    try:
        from services.email_service import send_booking_deleted_email, send_booking_deleted_alert
        approved_booking_info = {
            'id': booking_id,
            'booking_code': row[4] or str(booking_id),
            'student': deleted_student,
            'owner_name': owner_name,
            'owner_phone': owner_phone,
            'email': row[5] or '',
            'start_date': str(row[6]) if row[6] else '',
            'time': row[7] or '',
            'package': row[8] or ''
        }
        send_booking_deleted_email(approved_booking_info)
        send_booking_deleted_alert(approved_booking_info)
    except Exception as mail_err:
        print("Approve deletion email notification error:", mail_err)

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


def force_delete_booking(booking_id):
    """
    Force delete an active booking by Coach or Admin.
    Prompts for and logs:
    - classes_done (updated attendance)
    - amount_collected (financial tracking)
    Logs action to booking_actions_audit and permanently removes booking.
    """
    role = session.get('role')
    if role not in ('admin', 'trainer'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Unauthorized action'}), 403
        flash('Unauthorized action', 'danger')
        return redirect(url_for('my_bookings_page'))

    payload = request.get_json(silent=True) or request.form.to_dict()
    try:
        classes_done = int(payload.get('classes_done', 0))
    except (ValueError, TypeError):
        classes_done = 0

    try:
        amount_collected = float(payload.get('amount_collected', 0.0))
    except (ValueError, TypeError):
        amount_collected = 0.0

    notes = (payload.get('notes') or '').strip()

    conn = get_pg_connection()
    cursor = conn.cursor()

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
           fee
    FROM bookings
    WHERE id = %s OR TRIM(id::text) = TRIM(%s)
    ''', (str(booking_id), str(booking_id)))
    row = cursor.fetchone()

    if not row:
        conn.close()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404
        flash('Booking not found', 'warning')
        return redirect(url_for('my_bookings_page'))

    # Trainer authorization: verify coach assignment if not admin
    if role == 'trainer':
        trainer_user = (session.get('trainer_username') or '').strip().lower()
        trainer_name = (session.get('user_name') or '').strip().lower()
        booking_trainer = (row[8] or '').strip().lower()
        is_coach_authorized = (
            (bool(trainer_user) and (booking_trainer == trainer_user or trainer_user in booking_trainer or booking_trainer in trainer_user)) or
            (bool(trainer_name) and (booking_trainer == trainer_name or trainer_name in booking_trainer or booking_trainer in trainer_name)) or
            booking_trainer in ('', 'asdf', 'unassigned') or
            not bool(booking_trainer)
        )
        if not is_coach_authorized:
            conn.close()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'error': 'You are not assigned to this booking'}), 403
            flash('Unauthorized action', 'danger')
            return redirect(url_for('my_bookings_page'))

    student_name = row[1] or 'Swimmer'
    owner_name = row[2] or ''
    owner_phone = row[3] or ''
    performed_by = session.get('user_name') or session.get('trainer_username') or role

    # 1. Log audit trail
    try:
        cursor.execute('''
        INSERT INTO booking_actions_audit (
            booking_id, student_name, owner_name, owner_phone,
            action, performed_by, role, classes_done, amount_collected, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            str(booking_id), student_name, owner_name, owner_phone,
            'FORCE_DELETE', performed_by, role, classes_done, amount_collected, notes
        ))
    except Exception as audit_err:
        print("Notice: booking_actions_audit logging error:", audit_err)

    # 2. Cleanup dependent records safely
    for cleanup_query in [
        'DELETE FROM makeup_requests WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)',
        'DELETE FROM makeup_credits WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)',
        'DELETE FROM package_pause_audit WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)'
    ]:
        try:
            cursor.execute('SAVEPOINT sp_force_del_dep')
            cursor.execute(cleanup_query, (str(booking_id), str(booking_id)))
            cursor.execute('RELEASE SAVEPOINT sp_force_del_dep')
        except Exception:
            try:
                cursor.execute('ROLLBACK TO SAVEPOINT sp_force_del_dep')
            except Exception:
                pass

    # 3. Delete booking record
    cursor.execute('DELETE FROM bookings WHERE id = %s OR TRIM(id::text) = TRIM(%s)', (str(booking_id), str(booking_id)))

    # 4. Cleanup student if no other bookings remain
    try:
        cursor.execute('''
        SELECT COUNT(*) FROM bookings
        WHERE TRIM(student_name) = TRIM(%s) AND owner_name = %s AND owner_phone = %s
        ''', (student_name, owner_name, owner_phone))
        rem = cursor.fetchone()[0]
        if rem == 0:
            cursor.execute('''
            DELETE FROM students
            WHERE TRIM(student_name) = TRIM(%s) AND owner_name = %s AND owner_phone = %s
            ''', (student_name, owner_name, owner_phone))
    except Exception as st_err:
        print("Notice: student cleanup check error:", st_err)

    conn.commit()
    conn.close()

    flash(f"Booking for {student_name} was force-deleted (Classes done: {classes_done}, Collected: ₹{amount_collected:,.2f}).", "info")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'message': f"Booking for {student_name} force-deleted successfully.",
            'booking_id': str(booking_id)
        })
    return redirect(request.referrer or url_for('my_bookings_page'))


def force_complete_booking(booking_id):
    """
    Force complete an active booking by Coach or Admin.
    Prompts for and logs:
    - classes_done (updated attendance)
    - amount_collected (financial tracking)
    Updates booking to completed status, paid status, and records audit trail.
    """
    role = session.get('role')
    if role not in ('admin', 'trainer'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Unauthorized action'}), 403
        flash('Unauthorized action', 'danger')
        return redirect(url_for('my_bookings_page'))

    payload = request.get_json(silent=True) or request.form.to_dict()
    try:
        classes_done = int(payload.get('classes_done', 0))
    except (ValueError, TypeError):
        classes_done = 0

    try:
        amount_collected = float(payload.get('amount_collected', 0.0))
    except (ValueError, TypeError):
        amount_collected = 0.0

    notes = (payload.get('notes') or '').strip()

    conn = get_pg_connection()
    cursor = conn.cursor()

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
           fee,
           attended_sessions
    FROM bookings
    WHERE id = %s OR TRIM(id::text) = TRIM(%s)
    ''', (str(booking_id), str(booking_id)))
    row = cursor.fetchone()

    if not row:
        conn.close()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404
        flash('Booking not found', 'warning')
        return redirect(url_for('my_bookings_page'))

    # Trainer authorization
    if role == 'trainer':
        trainer_user = (session.get('trainer_username') or '').strip().lower()
        trainer_name = (session.get('user_name') or '').strip().lower()
        booking_trainer = (row[8] or '').strip().lower()
        is_coach_authorized = (
            (bool(trainer_user) and (booking_trainer == trainer_user or trainer_user in booking_trainer or booking_trainer in trainer_user)) or
            (bool(trainer_name) and (booking_trainer == trainer_name or trainer_name in booking_trainer or booking_trainer in trainer_name)) or
            booking_trainer in ('', 'asdf', 'unassigned') or
            not bool(booking_trainer)
        )
        if not is_coach_authorized:
            conn.close()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
                return jsonify({'success': False, 'error': 'You are not assigned to this booking'}), 403
            flash('Unauthorized action', 'danger')
            return redirect(url_for('my_bookings_page'))

    student_name = row[1] or 'Swimmer'
    owner_name = row[2] or ''
    owner_phone = row[3] or ''
    performed_by = session.get('user_name') or session.get('trainer_username') or role

    # 1. Log audit trail
    try:
        cursor.execute('''
        INSERT INTO booking_actions_audit (
            booking_id, student_name, owner_name, owner_phone,
            action, performed_by, role, classes_done, amount_collected, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            str(booking_id), student_name, owner_name, owner_phone,
            'FORCE_COMPLETE', performed_by, role, classes_done, amount_collected, notes
        ))
    except Exception as audit_err:
        print("Notice: booking_actions_audit logging error:", audit_err)

    # 2. Update booking status to completed
    # Set status='Paid' and payment_request='Paid' if amount_collected > 0
    payment_status_val = 'Paid' if amount_collected > 0 else 'Not Paid'
    today_str = datetime.now().strftime('%Y-%m-%d')

    cursor.execute('''
    UPDATE bookings
    SET
        package_status = 'COMPLETED',
        is_force_completed = TRUE,
        force_completed_classes = %s,
        status = %s,
        payment_request = %s,
        fee = %s,
        end_date = %s,
        pause_status = 'ACTIVE'
    WHERE id = %s OR TRIM(id::text) = TRIM(%s)
    ''', (
        classes_done,
        payment_status_val,
        payment_status_val,
        int(amount_collected),
        today_str,
        str(booking_id),
        str(booking_id)
    ))

    conn.commit()
    conn.close()

    flash(f"Booking for {student_name} marked as Force Completed! (Classes done: {classes_done}, Collected: ₹{amount_collected:,.2f}).", "success")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'message': f"Booking for {student_name} marked as Completed.",
            'booking_id': str(booking_id)
        })
    return redirect(request.referrer or url_for('my_bookings_page'))


def register_deletions_routes(app):
    app.add_url_rule('/delete/<booking_id>', endpoint='delete_booking', view_func=delete_booking, methods=['GET', 'POST'])
    app.add_url_rule('/approve_delete/<booking_id>', endpoint='approve_delete', view_func=approve_delete, methods=['POST'])
    app.add_url_rule('/reject_delete/<booking_id>', endpoint='reject_delete', view_func=reject_delete, methods=['POST'])
    app.add_url_rule('/booking/force_delete/<booking_id>', endpoint='force_delete_booking', view_func=force_delete_booking, methods=['POST'])
    app.add_url_rule('/booking/force_complete/<booking_id>', endpoint='force_complete_booking', view_func=force_complete_booking, methods=['POST'])
