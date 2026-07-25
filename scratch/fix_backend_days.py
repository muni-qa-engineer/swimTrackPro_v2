import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/swimtrackpro/routes/bookings.py"
with open(file_path, "r") as f:
    content = f.read()

target = """        "end_date": end_date,
        "package": package,
        "selected_days": request.form.get('selected_days', ''),
        "location": request.form.get('location', '').strip(),"""

replacement = """        "end_date": end_date,
        "package": package,
        "selected_days": (
            datetime.strptime(date_str, '%Y-%m-%d').strftime('%A') 
            if package in ('Single', 'Demo') 
            else request.form.get('selected_days', '')
        ),
        "location": request.form.get('location', '').strip(),"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated bookings.py to enforce Single/Demo selected_days on backend.")
