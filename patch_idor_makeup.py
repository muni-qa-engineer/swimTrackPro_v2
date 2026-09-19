import re

with open('swimtrackpro/routes/makeup.py', 'r') as f:
    content = f.read()

# We need to insert a check for guest ownership in reject_makeup_request.
new_check = """
    if session.get('role') not in ('trainer', 'guest'):
        flash('Unauthorized action')
        return redirect(url_for('index'))

    conn = get_pg_connection()
    cursor = conn.cursor()

    # If guest, verify ownership of the booking
    if session.get('role') == 'guest':
        cursor.execute('''
            SELECT b.owner_name, b.owner_phone 
            FROM makeup_requests r
            JOIN bookings b ON r.booking_id = b.id
            WHERE r.id = %s
        ''', (request_id,))
        booking_row = cursor.fetchone()
        if not booking_row:
            conn.close()
            flash('Request not found')
            return redirect(url_for('index'))
            
        session_phone = session.get('user_phone')
        session_name = session.get('user_name')
        
        if session_phone and booking_row[1] != session_phone:
            conn.close()
            flash('Unauthorized action')
            return redirect(url_for('index'))
        elif session_name and booking_row[0].strip().lower() != session_name.strip().lower():
            conn.close()
            flash('Unauthorized action')
            return redirect(url_for('index'))
"""

content = re.sub(
    r"    if session\.get\('role'\) not in \('trainer', 'guest'\):.*?cursor = conn\.cursor\(\)",
    new_check,
    content,
    flags=re.DOTALL
)

with open('swimtrackpro/routes/makeup.py', 'w') as f:
    f.write(content)

print("IDOR fixed in makeup.py")
