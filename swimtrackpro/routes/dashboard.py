"""Dashboard route."""

from flask import render_template, session, request, jsonify

from services.dashboard_service import (
    get_admin_dashboard_data,
    get_trainer_dashboard_data,
    get_guest_dashboard_data,
    get_all_packages
)
from swimtrackpro.runtime import get_pg_connection, load_data
from swimtrackpro.routes.bookings import check_and_perform_auto_resumes
from services.pricing_service import get_pricing_config_dict

def index():
    if 'user_name' not in session:
        packages = get_all_packages()
        coaches_list = []
        carousel_images = []
        gallery_items = []

        fallback_highlights = [
            {
                'id': 'curated_1',
                'url': '/static/images/Album/DSC08188.JPG',
                'category': 'coaching',
                'category_label': 'Coach & Learners',
                'author': 'Doorstep Coaching',
                'caption': 'Underwater Freestyle Form & Stroke Correction Drill',
                'is_coach': False,
                'coach_username': ''
            },
            {
                'id': 'curated_2',
                'url': '/static/images/Album/IMG20220514170101_01.jpg',
                'category': 'achievements',
                'category_label': 'Achievement',
                'author': 'Tournament Merit',
                'caption': 'State & National Championship Merit Certificates',
                'is_coach': False,
                'coach_username': ''
            },
            {
                'id': 'curated_3',
                'url': '/static/images/Album/DSC08279.JPG',
                'category': 'coaching',
                'category_label': 'Coach & Learners',
                'author': 'Junior Swimmer',
                'caption': 'Young Learner Kickboard & Breath Control Practice',
                'is_coach': False,
                'coach_username': ''
            },
            {
                'id': 'curated_4',
                'url': '/static/images/Album/DSC08390.jpg',
                'category': 'swimmers',
                'category_label': 'Swimmers in Action',
                'author': 'Advanced Swimmer',
                'caption': 'Butterfly Stroke Rhythm & Technique Drill at Student Pool',
                'is_coach': False,
                'coach_username': ''
            },
            {
                'id': 'curated_5',
                'url': '/static/images/Album/Medals.jpg',
                'category': 'achievements',
                'category_label': 'Achievement',
                'author': 'Championship Laurels',
                'caption': 'Tournament Medals & Podiums Won by Trained Swimmers',
                'is_coach': False,
                'coach_username': ''
            },
            {
                'id': 'curated_6',
                'url': '/static/images/Album/10376914.jpg',
                'category': 'achievements',
                'category_label': 'Achievement',
                'author': 'Championship Team',
                'caption': 'Proud Swimmers Celebrating Gold & Silver Laurels',
                'is_coach': False,
                'coach_username': ''
            },
            {
                'id': 'curated_7',
                'url': '/static/images/Album/DSC08280.JPG',
                'category': 'coaching',
                'category_label': 'Coach & Learners',
                'author': 'Personalized Training',
                'caption': '1-on-1 Stroke Guidance with Certified Trainer at Villa Pool',
                'is_coach': False,
                'coach_username': ''
            },
            {
                'id': 'curated_8',
                'url': '/static/images/Album/News 08_12_2020.jpg',
                'category': 'achievements',
                'category_label': 'Achievement',
                'author': 'Press & Honors',
                'caption': 'Media Spotlight & Competitive Swimming Accolades',
                'is_coach': False,
                'coach_username': ''
            }
        ]

        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            # Fetch carousel images
            cursor.execute("SELECT id, image_url FROM homepage_carousel ORDER BY created_at DESC")
            carousel_images = [{'id': row[0], 'url': row[1]} for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT t.username, t.name, t.experience, t.qualification, t.currently_working, t.residence_location, t.rating,
                       (SELECT COUNT(DISTINCT b.student_name) FROM bookings b WHERE LOWER(b.trainer_username) = LOWER(t.username)) as student_count,
                       (SELECT COUNT(*) FROM coach_feedback c WHERE c.trainer_username = t.username) as review_count,
                       t.available_slots,
                       t.photos,
                       t.id_number,
                       t.id_proof_file,
                       pp.filename as profile_pic
                FROM trainers t
                LEFT JOIN profile_pictures pp ON pp.id_number = t.id_number
                WHERE t.is_approved = TRUE
                ORDER BY t.rating DESC, t.name
            """)
            raw_trainers = cursor.fetchall()
            for row in raw_trainers:
                photos_str = (row[10] if len(row) > 10 and row[10] else "").strip()
                first_photo = [p.strip() for p in photos_str.split(",") if p.strip()]
                first_photo_val = first_photo[0] if first_photo else ""
                id_num = (row[11] if len(row) > 11 and row[11] else "").strip()
                id_proof_val = (row[12] if len(row) > 12 and row[12] else "").strip()
                prof_pic = (row[13] if len(row) > 13 and row[13] else "").strip()

                photo_url = ""
                if prof_pic:
                    if prof_pic.startswith("http://") or prof_pic.startswith("https://"):
                        photo_url = prof_pic
                    else:
                        photo_url = f"/static/profile_pictures/{prof_pic}"
                elif first_photo_val:
                    if first_photo_val.startswith("http://") or first_photo_val.startswith("https://"):
                        photo_url = first_photo_val
                    else:
                        photo_url = f"/static/uploads/{first_photo_val}"
                elif id_proof_val:
                    photo_url = f"/static/uploads/id_proofs/{id_proof_val}"

                coaches_list.append({
                    'username': row[0],
                    'name': row[1],
                    'experience': row[2],
                    'qualification': row[3],
                    'currently_working': row[4],
                    'residence_location': row[5],
                    'rating': float(row[6]) if row[6] is not None else 0.0,
                    'student_count': row[7],
                    'review_count': row[8] or 0,
                    'available_slots': row[9] or "[]",
                    'photos': photos_str,
                    'id_number': id_num,
                    'profile_pic': prof_pic,
                    'photo_url': photo_url
                })

            # Build unified gallery items:
            # 1. Admin photos (homepage_carousel)
            for img in carousel_images:
                img_url = (img.get('url') or '').strip()
                if img_url:
                    gallery_items.append({
                        'id': f"admin_{img.get('id')}",
                        'url': img_url,
                        'category': 'swimmers',
                        'category_label': 'Training Moment',
                        'author': 'SwimTrackPro Training',
                        'caption': 'Doorstep Swimming Session & Drill Practice',
                        'is_coach': False,
                        'coach_username': ''
                    })

            # 2. Coach photos (trainers.photos)
            for row in raw_trainers:
                t_user = row[0]
                t_name = row[1]
                t_photos_raw = row[10] or ''
                photo_list = [p.strip() for p in t_photos_raw.split(',') if p.strip()]
                for idx, p in enumerate(photo_list):
                    url = p if p.startswith('http') else f"/static/images/Album/{p}"
                    gallery_items.append({
                        'id': f"coach_{t_user}_{idx}",
                        'url': url,
                        'category': 'coaching',
                        'category_label': 'Coach & Learners',
                        'author': f"Coach {t_name}",
                        'caption': f"Personalized Training Session with Coach {t_name}",
                        'is_coach': True,
                        'coach_username': t_user
                    })

            # 3. Ensure gallery has curated items if uploads are low
            if len(gallery_items) < 6:
                existing_urls = {item['url'] for item in gallery_items}
                for item in fallback_highlights:
                    if item['url'] not in existing_urls:
                        gallery_items.append(item)

            recent_reviews = []
            cursor.execute("""
                SELECT c.guest_name, c.rating, c.comment, t.name 
                FROM coach_feedback c
                JOIN trainers t ON c.trainer_username = t.username
                WHERE c.rating >= 4 AND c.comment IS NOT NULL AND c.comment != ''
                ORDER BY c.created_at DESC
                LIMIT 10
            """)
            for row in cursor.fetchall():
                recent_reviews.append({
                    'guest_name': (row[0] or "Swimmer").strip().split(" ")[0],
                    'rating': row[1],
                    'comment': row[2],
                    'coach_name': row[3]
                })
            conn.close()
        except Exception as e:
            print("Error loading data for landing page:", e)
            if not gallery_items:
                gallery_items = fallback_highlights

        data = load_data()
        active_bookings = [
            {
                'student': b.get('student', ''),
                'trainer_username': (b.get('trainer_username') or '').strip().lower(),
                'location': b.get('location', ''),
                'time': b.get('time', ''),
                'calendar_dates': b.get('calendar_dates', []),
                'start_date': str(b.get('start_date', '')),
                'end_date': str(b.get('end_date', '')),
                'selected_days': b.get('selected_days', ''),
                'status': b.get('status'),
                'payment_request': b.get('payment_request')
            }
            for b in data.get('bookings', [])
            if b.get('payment_request') != 'unconfirmed' and b.get('status') != 'unconfirmed'
        ]

        return render_template(
            'login.html',
            pkg=packages,
            coaches=coaches_list,
            carousel_images=carousel_images,
            recent_reviews=recent_reviews,
            all_bookings=active_bookings,
            gallery_items=gallery_items,
            pricing_config=get_pricing_config_dict()
        )

    
    check_and_perform_auto_resumes()
    data = load_data()
    
    current_user = session.get('user_name', '')
    current_phone = session.get('phone', '')
    current_role = session.get('role', 'guest')

    # Query user_activity to check first-time vs returning status and tour status
    is_first_login = False
    tour_completed = False
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT COALESCE(login_count, 0), COALESCE(tour_completed, FALSE), previous_login
            FROM user_activity
            WHERE LOWER(user_name) = LOWER(%s)
              AND role = %s
            ORDER BY current_login DESC
            LIMIT 1
            ''',
            (current_user, current_role)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            login_count = row[0]
            tour_completed = bool(row[1])
            prev_login = row[2]
            if 'is_first_login' in session:
                is_first_login = bool(session['is_first_login'])
            else:
                is_first_login = (login_count <= 1 and not tour_completed) or (prev_login is None and not tour_completed)
        else:
            is_first_login = session.get('is_first_login', True)
    except Exception as e:
        print("Error checking user activity in dashboard:", e)
        is_first_login = session.get('is_first_login', False)

    user_display_name = current_user.title()
    if current_role == 'trainer':
        if is_first_login:
            welcome_title = f"Welcome Coach {user_display_name}! 👋"
            welcome_subtitle = "Take a quick 1-minute tour of your dashboard and menu."
        else:
            welcome_title = f"Welcome back, Coach {user_display_name}! 😊👋"
            welcome_subtitle = "Ready for today's coaching sessions?"
    elif current_role == 'admin':
        welcome_title = f"Welcome back, {user_display_name}! 😊👋"
        welcome_subtitle = "Super Admin Portal • Academy Operations"
    else:
        # Swimmer / Guest
        if is_first_login:
            welcome_title = f"Welcome {user_display_name}! 👋"
            welcome_subtitle = "Take a quick 1-minute tour of your dashboard and menu."
        else:
            welcome_title = f"Welcome back, {user_display_name}! 😊👋"
            welcome_subtitle = "Ready for your next swim session?"

    welcome_text = welcome_title

    if current_role == 'admin':
        admin_context = get_admin_dashboard_data(current_user, data)
        admin_context['welcome_text'] = welcome_text
        admin_context['welcome_title'] = welcome_title
        admin_context['welcome_subtitle'] = welcome_subtitle
        admin_context['is_first_login'] = is_first_login
        return render_template('admin_dashboard.html', **admin_context)

    if current_role == 'trainer':
        trainer_username = session.get('trainer_username') or 'asdf'
        context = get_trainer_dashboard_data(trainer_username, data)
        context['welcome_text'] = welcome_text
        context['welcome_title'] = welcome_title
        context['welcome_subtitle'] = welcome_subtitle
        context['is_first_login'] = is_first_login
        context['user_name'] = session['user_name']
        context['role'] = current_role
        return render_template('trainer_dashboard.html', **context)
    
    # Guest
    context = get_guest_dashboard_data(current_user, current_phone, data)
    context['welcome_text'] = welcome_text
    context['welcome_title'] = welcome_title
    context['welcome_subtitle'] = welcome_subtitle
    context['is_first_login'] = is_first_login
    context['user_name'] = session['user_name']
    context['role'] = current_role
    return render_template('guest_dashboard.html', **context)

def toggle_favorite_coach():
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

def confirm_coach_session():
    """
    Coach session completion confirmation endpoint.
    - If status == 'completed': Marks session as attended in bookings.attended_sessions (+1 to progress).
    - If status == 'missed': Adds 1 make-up credit in makeup_credits. Package end_date is untouched!
    """
    if 'user_name' not in session or session.get('role') not in ('trainer', 'admin'):
        return jsonify({"success": False, "message": "Unauthorized. Coach login required."}), 401

    payload = request.get_json(silent=True) or request.form.to_dict()
    booking_id = (payload.get('booking_id') or '').strip()
    session_date = (payload.get('session_date') or '').strip()
    status_input = (payload.get('status') or '').strip().lower()

    if not booking_id or not session_date or not status_input:
        return jsonify({"success": False, "message": "booking_id, session_date, and status are required."}), 400

    from services.makeup_service import create_makeup_credit

    try:
        conn = get_pg_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT trainer_username, attended_sessions, student_name, end_date FROM bookings WHERE id = %s", (booking_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({"success": False, "message": "Booking not found."}), 404

        assigned_trainer = (row[0] or '').strip().lower()
        current_user = (session.get('user_name') or '').strip().lower()
        current_trainer_user = (session.get('trainer_username') or '').strip().lower()

        if session.get('role') != 'admin' and assigned_trainer not in (current_user, current_trainer_user):
            conn.close()
            return jsonify({"success": False, "message": "You are not assigned to this student."}), 403

        attended_raw = row[1] or ''
        attended_list = [d.strip() for d in attended_raw.split(',') if d.strip()]
        student_name = row[2] or 'Swimmer'

        if status_input in ('completed', 'yes', 'present'):
            if session_date not in attended_list:
                attended_list.append(session_date)
            new_attended_str = ','.join(attended_list)
            cursor.execute("UPDATE bookings SET attended_sessions = %s WHERE id = %s", (new_attended_str, booking_id))

            # Remove any pending/mistaken makeup credit for this date
            cursor.execute("DELETE FROM makeup_credits WHERE booking_id = %s AND original_date = %s", (booking_id, session_date))
            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "status": "completed",
                "student_name": student_name,
                "session_date": session_date,
                "message": f"{student_name}'s session on {session_date} marked as completed (+1 Class done)."
            })

        elif status_input in ('missed', 'no', 'absent'):
            # Remove from attended if it was present
            if session_date in attended_list:
                attended_list = [d for d in attended_list if d != session_date]
                new_attended_str = ','.join(attended_list)
                cursor.execute("UPDATE bookings SET attended_sessions = %s WHERE id = %s", (new_attended_str, booking_id))
                conn.commit()
            conn.close()

            # Create Make-up credit for swimmer. Note: Package end_date is untouched!
            created = create_makeup_credit(
                booking_id=booking_id,
                original_date=session_date,
                notes=f"Missed session confirmed by coach {session.get('user_name')}"
            )

            return jsonify({
                "success": True,
                "status": "missed",
                "student_name": student_name,
                "session_date": session_date,
                "credit_created": created,
                "message": f"Session marked as missed. 1 Make-up credit added for {student_name}. Package end date is unaffected."
            })
        else:
            conn.close()
            return jsonify({"success": False, "message": f"Invalid status '{status_input}'. Use 'completed' or 'missed'."}), 400

    except Exception as e:
        print("Error confirming coach session:", e)
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

def get_coach_pending_confirmations():
    """Return list of pending session confirmations for the active coach."""
    if 'user_name' not in session or session.get('role') not in ('trainer', 'admin'):
        return jsonify({"success": False, "pending_confirmations": []}), 401

    data = load_data()
    trainer_username = session.get('trainer_username') or session.get('user_name') or 'asdf'
    context = get_trainer_dashboard_data(trainer_username, data)
    return jsonify({
        "success": True,
        "pending_confirmations": context.get('pending_confirmations', [])
    })

def complete_tour():
    """Mark tour as completed for current user in session and database."""
    user_name = session.get("user_name")
    role = session.get("role")
    session['is_first_login'] = False
    if user_name and role:
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_activity
                SET tour_completed = TRUE
                WHERE LOWER(user_name) = LOWER(%s) AND role = %s
            """, (user_name, role))
            conn.commit()
            conn.close()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": True, "notice": str(e)})
    return jsonify({"success": True})


def register_dashboard_routes(app):
    app.add_url_rule('/', endpoint='index', view_func=index)
    app.add_url_rule('/api/toggle_favorite_coach', endpoint='toggle_favorite_coach', view_func=toggle_favorite_coach, methods=['POST'])
    app.add_url_rule('/api/coach/confirm_session', endpoint='confirm_coach_session', view_func=confirm_coach_session, methods=['POST'])
    app.add_url_rule('/api/coach/pending_confirmations', endpoint='get_coach_pending_confirmations', view_func=get_coach_pending_confirmations, methods=['GET'])
    app.add_url_rule('/api/complete_tour', endpoint='complete_tour', view_func=complete_tour, methods=['POST'])
