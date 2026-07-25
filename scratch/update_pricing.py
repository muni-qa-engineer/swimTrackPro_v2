import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/services/pricing_service.py"
with open(file_path, "r") as f:
    content = f.read()

new_logic = """    # Monthly package
    elif package == 'Monthly':
        try:
            weekly_days = max(int(session_count or 3), 1)
        except Exception:
            weekly_days = 3

        actual_amount = weekly_days * 3000 * persons

    # Long Term Packages
    elif package in ['3_months', '6_months', '9_months', '12_months']:
        from services.dashboard_service import get_all_packages
        packages = get_all_packages()
        category = 'group' if persons > 1 else 'individual'
        if category in packages and package in packages[category]:
            final_price_per_person = packages[category][package]['final_price']
            # Reverse engineer the actual_amount so the final calculation equals (final_price_per_person * persons)
            actual_amount = (final_price_per_person * persons * 100) / (100 - discount)
        else:
            actual_amount = 0"""

content = re.sub(
    r"    # Monthly package\s*elif package == 'Monthly':.*?(?=\s*# Fallback)",
    new_logic + "\n\n",
    content,
    flags=re.DOTALL
)

with open(file_path, "w") as f:
    f.write(content)

print("Updated pricing_service.py successfully.")
