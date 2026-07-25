import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/app.py"
with open(file_path, "r") as f:
    content = f.read()

target = """    cursor.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE")"""
replacement = """    cursor.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE")

    cursor.execute(\"\"\"
    CREATE TABLE IF NOT EXISTS guest_favorites (
        guest_phone TEXT,
        trainer_username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (guest_phone, trainer_username)
    )
    \"\"\")"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Added guest_favorites table to app.py")
