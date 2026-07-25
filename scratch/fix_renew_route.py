import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/swimtrackpro/routes/bookings.py"
with open(file_path, "r") as f:
    content = f.read()

target = """    package = original.get('package', 'Single')
    selected_days = original.get('selected_days', '')"""

replacement = """    package = original.get('package', 'Single')
    selected_days = original.get('selected_days', '')
    
    # Ensure correct day for Single/Demo
    if package in ('Single', 'Demo'):
        selected_days = datetime.strptime(start_date, '%Y-%m-%d').strftime('%A')"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated renew_booking logic to enforce Single/Demo selected_days.")
