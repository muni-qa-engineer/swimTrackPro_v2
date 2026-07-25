import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/booking.html"
with open(file_path, "r") as f:
    content = f.read()

target = """<!-- Add standard booking controllers -->
<script src="{{ url_for('static', filename='common.js') }}"></script>
<script src="{{ url_for('static', filename='booking.js') }}?v=4"></script>"""

replacement = """<!-- Add standard booking controllers -->
<script>
    // Inject pricing configuration for frontend validation
    window.LONG_TERM_PACKAGES = {{ packages_json|safe if packages_json else 'null' }};
</script>
<script src="{{ url_for('static', filename='common.js') }}"></script>
<script src="{{ url_for('static', filename='booking.js') }}?v=5"></script>"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated booking.html with LONG_TERM_PACKAGES.")
