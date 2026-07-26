import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/admin_dashboard.html"
with open(file_path, "r") as f:
    content = f.read()

target = """            <button class="btn btn-secondary py-2 px-4 admin-tab-btn" onclick="showMyIdCard()" style="border-radius: var(--radius-sm);">My ID Card</button>
        </div>"""

replacement = """            <button class="btn btn-secondary py-2 px-4 admin-tab-btn" onclick="showMyIdCard()" style="border-radius: var(--radius-sm);">My ID Card</button>
            <button class="btn btn-warning py-2 px-4 admin-tab-btn" onclick="window.location.href='/promo'" style="border-radius: var(--radius-sm); color: black; font-weight: 600;"><i class="fa-solid fa-bullhorn me-1"></i> Promo</button>
        </div>"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Added Promo tab to admin_dashboard.html")
