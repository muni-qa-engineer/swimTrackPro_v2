import re

with open('swimtrackpro/routes/deletions.py', 'r') as f:
    content = f.read()

# We need to insert a check after checking for trainer.
new_check = """
    if role == 'trainer':
        trainer_user = session.get('trainer_username') or 'asdf'
        if (row[8] or 'asdf').strip().lower() != trainer_user.strip().lower():
            conn.close()
            flash('Unauthorized action')
            return redirect(url_for('index'))
    elif role == 'admin':
        pass # Admin can delete
    else:
        # Guest user check (IDOR fix)
        session_phone = session.get('user_phone')
        session_name = session.get('user_name')
        # We assume if phone is set, they logged in with phone, otherwise username.
        if session_phone:
            if not row[3] or row[3].strip() != session_phone.strip():
                conn.close()
                flash('Unauthorized action')
                return redirect(url_for('index'))
        elif session_name:
            if not row[2] or row[2].strip().lower() != session_name.strip().lower():
                conn.close()
                flash('Unauthorized action')
                return redirect(url_for('index'))
        else:
            conn.close()
            flash('Unauthorized action')
            return redirect(url_for('index'))
"""

content = re.sub(
    r"    if role == 'trainer':.*?return redirect\(url_for\('index'\)\)",
    new_check,
    content,
    flags=re.DOTALL
)

with open('swimtrackpro/routes/deletions.py', 'w') as f:
    f.write(content)

print("IDOR fixed in deletions.py")
