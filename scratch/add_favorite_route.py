import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/swimtrackpro/routes/dashboard.py"
with open(file_path, "r") as f:
    content = f.read()

# Add imports
if "from flask import render_template, session, request, jsonify" not in content:
    content = content.replace("from flask import render_template, session", "from flask import render_template, session, request, jsonify")

# Add the function and route registration
target = """def register_dashboard_routes(app):
    app.add_url_rule('/', endpoint='index', view_func=index)"""

replacement = """def toggle_favorite_coach():
    if 'user_name' not in session or session.get('role') != 'guest':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    trainer_username = request.form.get('trainer_username')
    current_phone = session.get('phone')
    
    if not trainer_username or not current_phone:
        return jsonify({"status": "error", "message": "Missing data"}), 400
        
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM guest_favorites WHERE guest_phone = %s AND trainer_username = %s", (current_phone, trainer_username))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("DELETE FROM guest_favorites WHERE guest_phone = %s AND trainer_username = %s", (current_phone, trainer_username))
            is_favorited = False
        else:
            cursor.execute("INSERT INTO guest_favorites (guest_phone, trainer_username) VALUES (%s, %s)", (current_phone, trainer_username))
            is_favorited = True
            
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "is_favorited": is_favorited})
    except Exception as e:
        print("Error toggling favorite:", e)
        return jsonify({"status": "error", "message": "Database error"}), 500

def register_dashboard_routes(app):
    app.add_url_rule('/', endpoint='index', view_func=index)
    app.add_url_rule('/api/toggle_favorite_coach', endpoint='toggle_favorite_coach', view_func=toggle_favorite_coach, methods=['POST'])"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Added toggle_favorite_coach to dashboard.py")
