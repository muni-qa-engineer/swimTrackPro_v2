"""Booking deletion and approval routes."""

from datetime import datetime

from flask import flash, redirect, session, url_for

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
           trainer_username
    FROM bookings
    WHERE id = %s
    ''', (booking_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        flash('Booking not found')
        return redirect(url_for('index'))

    if role == 'trainer':
        trainer_user = session.get('trainer_username') or 'asdf'
        if (row[8] or 'asdf').strip().lower() != trainer_user.strip().lower():
            conn.close()
            flash('Unauthorized action')
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

    # Guest users can delete immediately if no classes have been completed.
    # A class is completed 1 hour after its start time.
    if role != 'trainer':
        completed_classes = 0
        try:
            first_class_datetime = datetime.strptime(
                f"{start_date} {booking_time_str}",
                '%Y-%m-%d %I:%M %p'
            )
            first_class_end_datetime = first_class_datetime + timedelta(hours=1)
            if datetime.now() >= first_class_end_datetime:
                completed_classes = 1
        except Exception:
            completed_classes = 0

        # If progress is 0, delete immediately.
        if completed_classes == 0:
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


    flash(f'Booking deleted for {deleted_student}')
    return redirect(url_for('my_bookings_page'))

def approve_delete(booking_id):
    if session.get('role') != 'trainer':
        flash('Unauthorized action')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Load booking details before deletion
    cursor.execute('''
    SELECT student_name, owner_name, owner_phone, trainer_username
    FROM bookings
    WHERE id = %s
    ''', (booking_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        flash('Booking not found')
        return redirect(url_for('index'))

    trainer_user = session.get('trainer_username') or 'asdf'
    if (row[3] or 'asdf').strip().lower() != trainer_user.strip().lower():
        conn.close()
        flash('Unauthorized action')
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

def reject_delete(booking_id):
    if session.get('role') != 'trainer':
        flash('Unauthorized action')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT trainer_username FROM bookings WHERE id = %s', (booking_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        flash('Booking not found')
        return redirect(url_for('index'))

    trainer_user = session.get('trainer_username') or 'asdf'
    if (row[0] or 'asdf').strip().lower() != trainer_user.strip().lower():
        conn.close()
        flash('Unauthorized action')
        return redirect(url_for('index'))

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

def register_deletions_routes(app):
    app.add_url_rule('/delete/<booking_id>', endpoint='delete_booking', view_func=delete_booking, methods=['POST'])
    app.add_url_rule('/approve_delete/<booking_id>', endpoint='approve_delete', view_func=approve_delete, methods=['POST'])
    app.add_url_rule('/reject_delete/<booking_id>', endpoint='reject_delete', view_func=reject_delete, methods=['POST'])
