import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/static/booking.js"
with open(file_path, "r") as f:
    content = f.read()

# 1. Update allowed days & end date display logic
long_term_list = "['Monthly', '3_months', '6_months', '9_months', '12_months']"
content = content.replace("if (pkg.value === 'Monthly') {", f"if ({long_term_list}.includes(pkg.value)) {{")
content = content.replace(
    "const autoEndDate = new Date(selectedDate);\n        autoEndDate.setMonth(autoEndDate.getMonth() + 1);",
    "const autoEndDate = new Date(selectedDate);\n        let m = 1;\n        if (pkg.value === '3_months') m = 3;\n        if (pkg.value === '6_months') m = 6;\n        if (pkg.value === '9_months') m = 9;\n        if (pkg.value === '12_months') m = 12;\n        autoEndDate.setMonth(autoEndDate.getMonth() + m);"
)

# 2. Update the "if (pkg.value === 'Monthly' && selected.length > 3)"
content = content.replace(
    "if (pkg.value === 'Monthly' && selected.length > 3) {",
    f"if ({long_term_list}.includes(pkg.value) && selected.length > 3) {{",
)

# 3. Update the "if (pkg.value === 'Monthly' && selected.length === 1)"
content = content.replace(
    "if (pkg.value === 'Monthly' && selected.length === 1) {",
    f"if ({long_term_list}.includes(pkg.value) && selected.length === 1) {{",
)

# 4. Update the fee calculation
new_fee_logic = f"""    else if ({long_term_list}.includes(pkg.value)) {{
      if (selected.length < 2 || selected.length > 3) {{
        feeInput.value = '';
        feeInput.placeholder = 'Select 2 or 3 class days';
        return;
      }}

      if (pkg.value === 'Monthly') {{
        if (selected.length === 2) {{
          actualAmount = 6000 * persons;
        }} else {{
          actualAmount = 9000 * persons;
        }}
      }} else {{
        const isGroup = persons > 1;
        const category = isGroup ? 'group' : 'individual';
        const pricingData = window.LONG_TERM_PACKAGES && window.LONG_TERM_PACKAGES[category] && window.LONG_TERM_PACKAGES[category][pkg.value];
        if (pricingData) {{
            actualAmount = Math.round((pricingData.final_price * persons * 100) / (100 - discountPercent));
        }} else {{
            actualAmount = 0;
        }}
      }}
    }}"""

content = re.sub(
    r"else if \(pkg\.value === 'Monthly'\) \{\s*if \(selected\.length < 2.*?\n\s*\}\s*\}",
    new_fee_logic,
    content,
    flags=re.DOTALL
)

# 5. Form submission validation
content = content.replace(
    "if (pkg && pkg.value === 'Monthly') {",
    f"if (pkg && {long_term_list}.includes(pkg.value)) {{",
)

# 6. Initialize PRESELECTED_PACKAGE
init_logic = """document.addEventListener('DOMContentLoaded', () => {
    if (window.PRESELECTED_PACKAGE) {
        const pkgSelect = document.getElementById('packageSelect');
        if (pkgSelect) {
            pkgSelect.value = window.PRESELECTED_PACKAGE;
            pkgSelect.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }"""
content = content.replace("document.addEventListener('DOMContentLoaded', () => {", init_logic, 1)

with open(file_path, "w") as f:
    f.write(content)

print("Updated booking.js successfully.")
