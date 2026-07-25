import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/swimtrackpro/routes/bookings.py"
with open(file_path, "r") as f:
    content = f.read()

target = """    selected_days = request.form.getlist('selected_days')
    if not selected_days:
        selected_days = request.form.get('selected_days', '').split(',')
    selected_days_str = ', '.join(selected_days)"""

replacement = """    selected_days = request.form.getlist('selected_days')
    if not selected_days:
        selected_days = request.form.get('selected_days', '').split(',')
    selected_days_str = ', '.join(selected_days)
    
    if package in ('Single', 'Demo'):
        selected_days_str = datetime.strptime(start_date, '%Y-%m-%d').strftime('%A')"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated edit_booking logic.")
