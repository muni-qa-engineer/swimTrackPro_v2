import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/booking.html"
with open(file_path, "r") as f:
    content = f.read()

# 1. Add options to the dropdown
options_html = """                            <option value="Demo">Demo Class</option>
                            <option value="Single">Single Session</option>
                            <option value="Monthly">Monthly Pack</option>
                            <option value="Custom">Custom Duration</option>
                            <option value="3_months">Long Term (3 Months)</option>
                            <option value="6_months">Long Term (6 Months)</option>
                            <option value="9_months">Long Term (9 Months)</option>
                            <option value="12_months">Long Term (1 Year)</option>"""

content = re.sub(
    r'<option value="Demo">Demo Class</option>.*?<option value="Custom">Custom Duration</option>',
    options_html,
    content,
    flags=re.DOTALL
)

# 2. Inject JSON string of packages before closing head or before script tag
# I'll put it right after {% block content %} starts or before the booking.js include.
# Let's insert it before `<script src="{{ url_for('static', filename='booking.js') }}"></script>`
json_injection = """
<script>
    window.LONG_TERM_PACKAGES = {{ packages_json | safe }};
    window.PRESELECTED_PACKAGE = "{{ preselected_package }}";
</script>
<script src="{{ url_for('static', filename='booking.js') }}"></script>"""

content = content.replace(
    """<script src="{{ url_for('static', filename='booking.js') }}"></script>""",
    json_injection
)

with open(file_path, "w") as f:
    f.write(content)
print("Updated booking.html successfully.")
