import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/swimtrackpro/routes/general.py"
with open(file_path, "r") as f:
    content = f.read()

target = """def register_general_routes(app):"""

replacement = """@admin_required("Only admin can view marketing materials.")
def marketing_materials():
    return render_template("marketing_materials.html", role=session.get("role", "guest"))

def register_general_routes(app):"""

content = content.replace(target, replacement)

target2 = """    app.add_url_rule(
        "/about",
        endpoint="about_page",
        view_func=about_page,
    )"""

replacement2 = """    app.add_url_rule(
        "/about",
        endpoint="about_page",
        view_func=about_page,
    )
    app.add_url_rule(
        "/promo",
        endpoint="marketing_materials",
        view_func=marketing_materials,
    )"""

content = content.replace(target2, replacement2)

with open(file_path, "w") as f:
    f.write(content)

print("Added /promo route to general.py")
