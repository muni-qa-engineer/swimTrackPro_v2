import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/swimtrackpro/routes/pages.py"
with open(file_path, "r") as f:
    content = f.read()

# Add import if not exists
if "from services.dashboard_service import get_all_packages" not in content:
    content = content.replace("from services.settings_service import get_setting", "from services.settings_service import get_setting\nfrom services.dashboard_service import get_all_packages\nimport json")

# Add preselected package parsing before render_template("booking.html"
# The render_template is around line 139. Let's find "renew_booking=renew_booking" and inject it there.
replacement = """
        packages = get_all_packages()
        preselected_package = request.args.get('package', '')
        
        return render_template(
            "booking.html",
            role=current_role,
            user_name=current_user,
            students=user_students,
            bookings=_bookings_for_session(data),
            all_bookings=data.get("bookings", []),
            location_suggestions=location_suggestions,
            trainers=trainers,
            admin_phone=get_setting("trainer_phone", ""),
            renew_booking=renew_booking,
            packages=packages,
            preselected_package=preselected_package,
            packages_json=json.dumps(packages)
        )"""

content = re.sub(
    r'return render_template\(\s*"booking\.html",.*?,.*?renew_booking=renew_booking\s*\)',
    replacement.strip(),
    content,
    flags=re.DOTALL
)

with open(file_path, "w") as f:
    f.write(content)
print("Updated pages.py successfully.")
