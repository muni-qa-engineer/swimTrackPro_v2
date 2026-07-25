import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/services/dashboard_service.py"
with open(file_path, "r") as f:
    content = f.read()

target = """def get_guest_dashboard_data(current_user, current_phone, data):
    \"\"\"Fetch and process data specifically for the Guest dashboard.\"\"\"
    user_bookings = [
        b for b in data.get('bookings', [])
        if (b.get('owner_name') or '').strip().lower() == current_user
        and b.get('owner_phone') == current_phone
        and b.get('payment_request') != 'unconfirmed'
    ]
    user_students = [
        s for s in data.get('students', [])
        if isinstance(s, dict)
        and (s.get('owner_name') or '').strip().lower() == current_user
        and s.get('owner_phone') == current_phone
    ]
    return _process_common_dashboard_data(user_bookings, user_students, 'guest', current_user)"""

replacement = """def get_guest_dashboard_data(current_user, current_phone, data):
    \"\"\"Fetch and process data specifically for the Guest dashboard.\"\"\"
    user_bookings = [
        b for b in data.get('bookings', [])
        if (b.get('owner_name') or '').strip().lower() == current_user
        and b.get('owner_phone') == current_phone
        and b.get('payment_request') != 'unconfirmed'
    ]
    user_students = [
        s for s in data.get('students', [])
        if isinstance(s, dict)
        and (s.get('owner_name') or '').strip().lower() == current_user
        and s.get('owner_phone') == current_phone
    ]
    result = _process_common_dashboard_data(user_bookings, user_students, 'guest', current_user)
    
    from swimtrackpro.runtime import get_pg_connection
    coaches_list = []
    favorite_usernames = set()
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        # Get favorites for this guest
        cursor.execute("SELECT trainer_username FROM guest_favorites WHERE guest_phone = %s", (current_phone,))
        favorite_usernames = {row[0] for row in cursor.fetchall()}
        
        # Get approved coaches
        cursor.execute(\"\"\"
            SELECT username, name, experience, qualification, currently_working, residence_location, rating, photos, bio, specialties, instagram, facebook, twitter, youtube
            FROM trainers
            WHERE is_approved = TRUE
            ORDER BY rating DESC, name
        \"\"\")
        
        for row in cursor.fetchall():
            coaches_list.append({
                'username': row[0],
                'name': row[1],
                'experience': row[2],
                'qualification': row[3],
                'currently_working': row[4],
                'residence_location': row[5],
                'rating': float(row[6]) if row[6] is not None else 5.0,
                'photos': row[7],
                'bio': row[8],
                'specialties': row[9],
                'instagram': row[10],
                'facebook': row[11],
                'twitter': row[12],
                'youtube': row[13],
                'is_favorited': row[0] in favorite_usernames
            })
            
        conn.close()
    except Exception as e:
        print("Error fetching coaches for guest dashboard:", e)
        
    result['available_coaches'] = coaches_list
    return result"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated get_guest_dashboard_data in dashboard_service.py")
