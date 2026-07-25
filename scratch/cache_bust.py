import os

html_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/booking.html"
with open(html_path, "r") as f:
    html_content = f.read()

# Cache busting from v=3 to v=4
html_content = html_content.replace("filename='booking.js') }}?v=3", "filename='booking.js') }}?v=4")

with open(html_path, "w") as f:
    f.write(html_content)

print("Updated booking cache bust.")
