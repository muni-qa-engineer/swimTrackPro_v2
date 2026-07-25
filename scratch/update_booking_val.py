import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/booking.html"
with open(file_path, "r") as f:
    content = f.read()

# Remove Step 2 validation in wizardNext
start_str = "        // Custom validation for Step 2"
end_str = "        // Hide current step, show next"
start_idx = content.find(start_str)
end_idx = content.find(end_str)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + content[end_idx:]
else:
    print("Could not find step 2 validation")

with open(file_path, "w") as f:
    f.write(content)
print("booking.html validation updated successfully.")
