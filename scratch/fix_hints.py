import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/booking.html"
with open(file_path, "r") as f:
    content = f.read()

hint_target = """<span id="monthlyPackageHint" class="text-muted small ms-2" style="display:none;">(Monthly: Choose 2 or 3 days/week)</span>"""
hint_replacement = """<span id="monthlyPackageHint" class="text-muted small ms-2" style="display:none;">(Monthly: Choose 2 or 3 days/week)</span>
                        <span id="longtermPackageHint" class="text-muted small ms-2" style="display:none;">(Long Term: Choose exactly 3 days/week)</span>"""

content = content.replace(hint_target, hint_replacement)

with open(file_path, "w") as f:
    f.write(content)

# Update booking.js to toggle the new hint
js_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/static/booking.js"
with open(js_path, "r") as f:
    js_content = f.read()

js_hint_target = """  const monthlyPackageHint = document.getElementById('monthlyPackageHint');"""
js_hint_replacement = """  const monthlyPackageHint = document.getElementById('monthlyPackageHint');
  const longtermPackageHint = document.getElementById('longtermPackageHint');"""
js_content = js_content.replace(js_hint_target, js_hint_replacement)

js_hint_toggle_target = """      if (monthlyPackageHint) monthlyPackageHint.style.display = pkg.value === 'Monthly' ? 'inline' : 'none';"""
js_hint_toggle_replacement = """      if (monthlyPackageHint) monthlyPackageHint.style.display = pkg.value === 'Monthly' ? 'inline' : 'none';
      if (longtermPackageHint) longtermPackageHint.style.display = ['3_months', '6_months', '9_months', '12_months'].includes(pkg.value) ? 'inline' : 'none';"""
js_content = js_content.replace(js_hint_toggle_target, js_hint_toggle_replacement)

with open(js_path, "w") as f:
    f.write(js_content)

print("Updated hints successfully.")
