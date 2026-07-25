import os

# 1. Update booking.js to parse the date as local time to prevent month shift bugs
js_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/static/booking.js"
with open(js_path, "r") as f:
    js_content = f.read()

target_date_parse = "const selectedDate = new Date(startDateInput.value);"
replacement_date_parse = "const selectedDate = new Date(startDateInput.value + 'T00:00:00');"
js_content = js_content.replace(target_date_parse, replacement_date_parse)

# We also need to fix autoEndDate parsing: `const autoEndDate = new Date(selectedDate);` - this works perfectly since selectedDate is now local time.

with open(js_path, "w") as f:
    f.write(js_content)

# 2. Update booking.html (Cache-busting + Increase Size of Person Input)
html_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/booking.html"
with open(html_path, "r") as f:
    html_content = f.read()

# Cache busting
html_content = html_content.replace("filename='booking.js') }}?v=2", "filename='booking.js') }}?v=3")

# Resize person input
target_input = """<div class="input-group">
                            <button class="btn btn-outline-secondary" type="button" id="btn-minus-person\""""
replacement_input = """<div class="input-group input-group-lg" style="height: 100%;">
                            <button class="btn btn-outline-secondary px-4" type="button" id="btn-minus-person\""""
html_content = html_content.replace(target_input, replacement_input)

# Also update the plus button to match the padding of the minus button
html_content = html_content.replace('id="btn-plus-person" style', 'id="btn-plus-person" class="btn btn-outline-secondary px-4" style')

with open(html_path, "w") as f:
    f.write(html_content)

print("Fixed local date parsing and resized persons input.")
