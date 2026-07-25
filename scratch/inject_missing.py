import sys

with open("/Users/munisekhar/Desktop/swimTrackPro_v2/scratch/my_bookings_old.html", "r") as f:
    lines = f.readlines()

# The missing part is from line 658 (0-indexed 657) to line 872 (0-indexed 871)
missing_part_lines = lines[657:872]
missing_part = "".join(missing_part_lines)

with open("/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html", "r") as f2:
    current = f2.read()

# We need to inject the first part of missing_part (the inside of DOMContentLoaded) 
# into the END of the current DOMContentLoaded listener.
# The current DOMContentLoaded ends at line 630. Let's find "    });\n</script>" at the bottom.
inject_idx = current.rfind("    });\n</script>")
if inject_idx != -1:
    new_content = current[:inject_idx] + missing_part + current[inject_idx + 8:]
    with open("/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html", "w") as f3:
        f3.write(new_content)
    print("Injected successfully")
else:
    print("Could not find injection point")
