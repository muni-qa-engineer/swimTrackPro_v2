import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html"
with open(file_path, "r") as f:
    content = f.read()

# 1. Add confirm dialog to form
target_form = """<form action="/delete/{{ b.id }}" method="POST" class="d-inline delete-booking-form" onsubmit="saveScrollPosition();">"""
replacement_form = """<form action="/delete/{{ b.id }}" method="POST" class="d-inline delete-booking-form" onsubmit="saveScrollPosition(); return confirm('Are you sure you want to delete this booking?');">"""
content = content.replace(target_form, replacement_form)

# 2. Change button type="button" to type="submit"
target_btn = """<button type="button" class="btn btn-outline animated-delete-btn" """
replacement_btn = """<button type="submit" class="btn btn-outline animated-delete-btn" """
content = content.replace(target_btn, replacement_btn)

with open(file_path, "w") as f:
    f.write(content)
print("Updated my_bookings.html successfully.")
