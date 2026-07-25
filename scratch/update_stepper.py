file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/components/booking_stepper.html"
with open(file_path, "r") as f:
    content = f.read()

# Remove Step 2
start_idx = content.find("<!-- Step 2: Coach Selection -->")
# Find the next divider after step 2
next_divider = content.find("<!-- Step 3: Swimmer Details -->")

if start_idx != -1 and next_divider != -1:
    content = content[:start_idx] + content[next_divider:]

# Renumber Step 3 to 2
content = content.replace("<!-- Step 3: Swimmer Details -->", "<!-- Step 2: Swimmer Details -->")
content = content.replace("id=\"step-indicator-3\"", "id=\"step-indicator-2\"")
content = content.replace("current_step == 3", "current_step == 2")
content = content.replace("current_step > 3", "current_step > 2")
content = content.replace("{% else %}3{% endif %}", "{% else %}2{% endif %}")

# Renumber Step 4 to 3
content = content.replace("<!-- Step 4: Confirmation -->", "<!-- Step 3: Confirmation -->")
content = content.replace("id=\"step-indicator-4\"", "id=\"step-indicator-3\"")
content = content.replace("current_step == 4", "current_step == 3")
content = content.replace("current_step > 4", "current_step > 3")
content = content.replace("{% else %}4{% endif %}", "{% else %}3{% endif %}")

with open(file_path, "w") as f:
    f.write(content)
print("Stepper updated successfully.")
