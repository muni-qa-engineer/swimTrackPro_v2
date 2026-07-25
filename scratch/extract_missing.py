import re

# Read old html
with open("/Users/munisekhar/Desktop/swimTrackPro_v2/scratch/my_bookings_old.html", "r") as f:
    old_content = f.read()

# Extract missing part
start_marker = "    // Trainer group collapse"
start_idx = old_content.find(start_marker)

end_marker = "<script src=\"{{ url_for('static', filename='common.js') }}\"></script>"
end_idx = old_content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    missing_part = old_content[start_idx:end_idx]
    
    # Let's read current
    with open("/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html", "r") as f2:
        current_content = f2.read()
    
    # In current_content, find where to inject it
    inject_marker = "</script>\n\n<script src=\"{{ url_for('static', filename='common.js') }}\"></script>"
    inject_idx = current_content.find(inject_marker)
    
    if inject_idx != -1:
        # missing_part starts with "    // Trainer group collapse", we can inject it right before </script>
        # Wait, missing_part contains </script> and HTML for renewModal and another <script>.
        # So we should inject it BEFORE the </script> for the first part?
        # No, the start_marker is inside the DOMContentLoaded from the old filter script!
        # Let's just put it inside the DOMContentLoaded of the current filter script!
        pass
        
    print("Found missing part length:", len(missing_part))
    with open("/Users/munisekhar/Desktop/swimTrackPro_v2/scratch/missing_part.txt", "w") as f3:
        f3.write(missing_part)
