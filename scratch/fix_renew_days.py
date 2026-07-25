import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/static/booking.js"
with open(file_path, "r") as f:
    content = f.read()

target = """        // 5. Pre-fill Days
        if (window.renewBookingData.selected_days) {"""

replacement = """        // 5. Pre-fill Days (Skip for Single/Demo because Start Date dictates the day)
        if (window.renewBookingData.selected_days && !['Single', 'Demo'].includes(window.renewBookingData.package)) {"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated renew logic for days.")
