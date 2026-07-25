file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html"
with open(file_path, "r") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "{% elif b.package == 'Single' %}" in line:
        # Check if the previous line is an empty line or just spaces, and the one before that is </div>
        if "</div>" in lines[i-2] and lines[i-1].strip() == "":
            start_idx = i - 1
            break

if start_idx != -1:
    # Now find the matching {% endfor %} right before {% if ns.show_add_card
    for i in range(start_idx, len(lines)):
        if "{% if ns.show_add_card and role != 'trainer' %}" in lines[i]:
            # The previous lines should be {% endfor %}
            for j in range(i-1, start_idx, -1):
                if "{% endfor %}" in lines[j]:
                    end_idx = j + 1
                    break
            break

if start_idx != -1 and end_idx != -1:
    print(f"Deleting lines {start_idx+1} to {end_idx}")
    print(f"First deleted: {lines[start_idx].strip()}")
    print(f"Last deleted: {lines[end_idx-1].strip()}")
    print(f"Next line: {lines[end_idx].strip()}")
    
    del lines[start_idx:end_idx]
    
    with open(file_path, "w") as f:
        f.writelines(lines)
    print("Cleanup successful.")
else:
    print("Could not find bounds.", start_idx, end_idx)
