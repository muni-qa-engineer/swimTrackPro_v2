"""General authenticated pages and session routes."""

from flask import flash, redirect, render_template, request, session, url_for, jsonify

from services.settings_service import get_setting
from swimtrackpro.auth import login_required, trainer_required, admin_required
from swimtrackpro.runtime import get_pg_connection, load_data


@login_required
def about_trainer():
    import re
    current_user = (session.get("user_name") or "").strip().lower()
    current_phone = (session.get("phone") or "").strip()
    user_clean_phone = re.sub(r"\D", "", current_phone)
    current_role = session.get("role", "guest")

    conn = get_pg_connection()
    cursor = conn.cursor()

    if current_role == "trainer":
        assigned_usernames = []
        trainer_user = session.get("trainer_username") or "asdf"
        cursor.execute("""
            SELECT username, name, phone, email, experience, qualification, currently_working, residence_location, rating, photos, whatsapp, bio, specialties, instagram, facebook, twitter, youtube 
            FROM trainers WHERE username = %s
        """, (trainer_user,))
        trainers = cursor.fetchall()
    else:
        # Swimmer/Guest: find trainer usernames from bookings
        data = load_data()
        bookings = []
        for b in data.get("bookings", []):
            b_owner = (b.get("owner_name") or "").strip().lower()
            b_created = (b.get("created_by") or "").strip().lower()
            b_student = (b.get("student") or "").strip().lower()
            b_phone = re.sub(r"\D", "", str(b.get("owner_phone") or ""))
            
            name_match = current_user and (b_owner == current_user or b_created == current_user or b_student == current_user)
            phone_match = user_clean_phone and b_phone and (user_clean_phone == b_phone or user_clean_phone.endswith(b_phone) or b_phone.endswith(user_clean_phone))
            if name_match or phone_match:
                bookings.append(b)

        assigned_usernames = [str(b.get("trainer_username")).strip() for b in bookings if b.get("trainer_username")]

        # Also query PostgreSQL bookings table directly to ensure no assigned coaches are missed
        try:
            cursor.execute(r"""
                SELECT DISTINCT trainer_username FROM bookings 
                WHERE LOWER(owner_name) = %s OR LOWER(student_name) = %s OR LOWER(created_by) = %s
                   OR (owner_phone IS NOT NULL AND %s <> '' AND regexp_replace(owner_phone, '\D', '', 'g') = %s)
            """, (current_user, current_user, current_user, user_clean_phone, user_clean_phone))
            for row in cursor.fetchall():
                if row[0] and row[0].strip():
                    assigned_usernames.append(row[0].strip())
        except Exception as e:
            print("DB lookup in about_trainer error:", e)

        assigned_usernames = list(set([u for u in assigned_usernames if u]))

        trainers = []
        if assigned_usernames:
            clean_list = [u.lower() for u in assigned_usernames if u]
            placeholders = ", ".join(["%s"] * len(clean_list))
            cursor.execute(f"""
                SELECT username, name, phone, email, experience, qualification, currently_working, residence_location, rating, photos, whatsapp, bio, specialties, instagram, facebook, twitter, youtube, id_number 
                FROM trainers 
                WHERE (LOWER(username) IN ({placeholders}) OR LOWER(name) IN ({placeholders})) AND is_approved = TRUE
            """, tuple(clean_list) + tuple(clean_list))
            trainers = cursor.fetchall()

    coaches_list = []
    for r in trainers:
        username = r[0]
        trainer_id_num = r[17] if len(r) > 17 and r[17] else ""
        profile_pic = ""
        if trainer_id_num:
            cursor.execute("SELECT filename FROM profile_pictures WHERE id_number = %s", (trainer_id_num,))
            pic_row = cursor.fetchone()
            if pic_row and pic_row[0]:
                profile_pic = pic_row[0]

        cursor.execute("""
            SELECT guest_name, rating, comment, created_at 
            FROM coach_feedback 
            WHERE trainer_username = %s 
            ORDER BY created_at DESC
        """, (username,))
        feedbacks = []
        for f in cursor.fetchall():
            display_name = (f[0] or "Swimmer").strip().split(" ")[0]
            feedbacks.append({
                "guest_name": display_name,
                "rating": f[1],
                "comment": f[2] or "",
                "created_at": f[3].strftime('%Y-%m-%d') if f[3] else '--'
            })

        coaches_list.append({
            "username": username,
            "name": r[1],
            "phone": r[2] or "",
            "email": r[3] or "",
            "experience": r[4] or "5+ Years",
            "qualification": r[5] or "Certified Swim Coach",
            "currently_working": r[6] or "SwimTrackPro Academy",
            "residence_location": r[7] or "Local Camp",
            "rating": float(r[8]) if r[8] is not None else 5.0,
            "photos": [p.strip() for p in (r[9] or "").split(",") if p.strip()],
            "profile_pic": profile_pic,
            "whatsapp": r[10] or "",
            "bio": r[11] or "",
            "specialties": r[12] or "",
            "instagram": r[13] or "",
            "facebook": r[14] or "",
            "twitter": r[15] or "",
            "youtube": r[16] or "",
            "feedbacks": feedbacks
        })

    conn.close()

    return render_template("about_trainer.html", coaches=coaches_list, role=current_role, assigned_usernames=assigned_usernames, admin_phone=get_setting("trainer_phone", ""))


def help_page():
    return render_template("help.html", role=session.get("role", "guest"))

def about_swimming():
    return render_template("about_swimming.html", role=session.get("role", "guest"))


def about_page():
    return render_template("about.html", role=session.get("role", "guest"))

def faq_page():
    return render_template("faq.html", role=session.get("role", "guest"))


@trainer_required("Only trainer can update the Notice Board.")
def update_notice():
    notice_message = request.form.get("notice_message", "").strip()

    if not notice_message:
        flash("Notice Board message cannot be empty.", "warning")
        return redirect(url_for("index"))

    trainer_user = session.get("trainer_username") or "asdf"
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE trainers SET notice = %s WHERE username = %s", (notice_message, trainer_user))
    conn.commit()
    conn.close()

    flash("Notice Board updated successfully.", "success")
    return redirect(url_for("index"))


@login_required
def profile_page():
    current_role = session.get("role", "guest")
    conn = get_pg_connection()
    cursor = conn.cursor()

    # Determine view mode for Admin
    admin_override_role = None
    admin_target_id = None
    if current_role == "admin":
        admin_override_role = request.args.get("user_type", "").strip().lower()
        admin_target_id = request.args.get("id", "").strip()

    # -------------------------------------------------------------
    # 1. GUEST / SWIMMER PROFILE (or Admin overriding Swimmer)
    # -------------------------------------------------------------
    if (current_role == "guest") or (current_role == "admin" and admin_override_role == "swimmer"):
        swimmer_phone = admin_target_id if (current_role == "admin" and admin_target_id) else session.get("phone", "")
        swimmer_name = session.get("user_name", "")

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            dob = request.form.get("dob", "").strip()
            gender = request.form.get("gender", "").strip()
            email = request.form.get("email", "").strip()
            address = request.form.get("address", "").strip()
            city = request.form.get("city", "").strip()
            state = request.form.get("state", "").strip()
            pincode = request.form.get("pincode", "").strip()
            preferred_location = request.form.get("preferred_location", "").strip()
            skill_level = request.form.get("skill_level", "").strip()
            experience = request.form.get("experience", "").strip()
            goals_list = request.form.getlist("swimming_goals")
            goals = ",".join(goals_list) if goals_list else request.form.get("swimming_goals", "").strip()
            training_type = request.form.get("training_type", "").strip()
            days_list = request.form.getlist("preferred_days")
            days = ",".join(days_list) if days_list else request.form.get("preferred_days", "").strip()
            preferred_time = request.form.get("preferred_time", "").strip()
            swimmer_type = request.form.get("swimmer_type", "").strip()
            height = request.form.get("height", "").strip()
            emergency_name = request.form.get("emergency_name", "").strip()
            emergency_phone = request.form.get("emergency_phone", "").strip()
            medical_notes = request.form.get("medical_notes", "").strip()

            # Admin-only overrides
            account_status = request.form.get("account_status", "Active").strip() if current_role == "admin" else None

            cursor.execute("""
                INSERT INTO swimmer_profiles (
                    phone, name, dob, gender, email, address, city, state, pincode,
                    preferred_location, skill_level, experience, swimming_goals,
                    training_type, preferred_days, preferred_time, swimmer_type,
                    height, emergency_name, emergency_phone, medical_notes,
                    account_status, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    COALESCE(%s, 'Active'), CURRENT_TIMESTAMP
                )
                ON CONFLICT (phone) DO UPDATE SET
                    name = EXCLUDED.name,
                    dob = EXCLUDED.dob,
                    gender = EXCLUDED.gender,
                    email = EXCLUDED.email,
                    address = EXCLUDED.address,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    pincode = EXCLUDED.pincode,
                    preferred_location = EXCLUDED.preferred_location,
                    skill_level = EXCLUDED.skill_level,
                    experience = EXCLUDED.experience,
                    swimming_goals = EXCLUDED.swimming_goals,
                    training_type = EXCLUDED.training_type,
                    preferred_days = EXCLUDED.preferred_days,
                    preferred_time = EXCLUDED.preferred_time,
                    swimmer_type = EXCLUDED.swimmer_type,
                    height = EXCLUDED.height,
                    emergency_name = EXCLUDED.emergency_name,
                    emergency_phone = EXCLUDED.emergency_phone,
                    medical_notes = EXCLUDED.medical_notes,
                    account_status = CASE WHEN %s IS NOT NULL THEN %s ELSE swimmer_profiles.account_status END,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                swimmer_phone, name, dob, gender, email, address, city, state, pincode,
                preferred_location, skill_level, experience, goals,
                training_type, days, preferred_time, swimmer_type,
                height, emergency_name, emergency_phone, medical_notes,
                account_status,
                account_status, account_status
            ))

            # Sync student name and skill level in students table
            if name:
                cursor.execute("""
                    UPDATE students 
                    SET student_name = %s, skill_level = %s 
                    WHERE owner_phone = %s
                """, (name, skill_level, swimmer_phone))

            # If user is updating their own profile, sync session user_name
            if current_role == "guest" and name:
                session["user_name"] = name
                cursor.execute("UPDATE user_activity SET user_name = %s WHERE phone = %s", (name, swimmer_phone))

            conn.commit()
            flash("Swimmer Profile updated successfully!", "success")
            if current_role == "admin":
                conn.close()
                return redirect(url_for("profile_page", user_type="swimmer", id=swimmer_phone))
            conn.close()
            return redirect(url_for("profile_page"))

        # Fetch Swimmer Profile data
        cursor.execute("SELECT * FROM swimmer_profiles WHERE phone = %s", (swimmer_phone,))
        s_row = cursor.fetchone()

        # If not present in swimmer_profiles, prefill from students or user_activity
        if not s_row:
            cursor.execute("SELECT student_name, skill_level FROM students WHERE owner_phone = %s LIMIT 1", (swimmer_phone,))
            std_row = cursor.fetchone()
            initial_name = swimmer_name or (std_row[0] if std_row else "")
            initial_skill = std_row[1] if std_row else "Beginner"

            cursor.execute("""
                INSERT INTO swimmer_profiles (phone, name, skill_level)
                VALUES (%s, %s, %s)
                ON CONFLICT (phone) DO NOTHING
            """, (swimmer_phone, initial_name, initial_skill))
            conn.commit()

            cursor.execute("SELECT * FROM swimmer_profiles WHERE phone = %s", (swimmer_phone,))
            s_row = cursor.fetchone()

        # Get column names for swimmer_profiles
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'swimmer_profiles' ORDER BY ordinal_position")
        s_cols = [c[0] for c in cursor.fetchall()]
        swimmer_dict = dict(zip(s_cols, s_row)) if s_row else {}

        # Swimmer ID Number and Profile Pic
        swimmer_id_num = session.get("id_number", "STPS0001")
        if current_role == "admin" and admin_target_id:
            cursor.execute("SELECT id_number FROM user_activity WHERE phone = %s AND id_number IS NOT NULL LIMIT 1", (swimmer_phone,))
            act_id = cursor.fetchone()
            if act_id and act_id[0]:
                swimmer_id_num = act_id[0]

        profile_pic = ""
        cursor.execute("SELECT filename FROM profile_pictures WHERE id_number = %s", (swimmer_id_num,))
        pic_row = cursor.fetchone()
        if pic_row and pic_row[0]:
            profile_pic = pic_row[0]

        # Registration date
        reg_date = "2026"
        if swimmer_dict.get("created_at"):
            reg_date = swimmer_dict["created_at"].strftime("%b %Y")
        else:
            try:
                cursor.execute("SELECT current_login FROM user_activity WHERE phone = %s ORDER BY current_login ASC LIMIT 1", (swimmer_phone,))
                act_row = cursor.fetchone()
                if act_row and act_row[0]:
                    reg_date = act_row[0].strftime("%b %Y")
            except Exception:
                conn.rollback()

        conn.close()

        # Parse goals and days as lists for checkbox/pill checking
        goals_arr = [g.strip() for g in (swimmer_dict.get("swimming_goals") or "").split(",") if g.strip()]
        days_arr = [d.strip() for d in (swimmer_dict.get("preferred_days") or "").split(",") if d.strip()]

        return render_template(
            "profile.html",
            role="guest",
            profile_type="swimmer",
            swimmer=swimmer_dict,
            swimmer_goals=goals_arr,
            swimmer_days=days_arr,
            id_number=swimmer_id_num,
            profile_pic=profile_pic,
            member_since=reg_date,
            is_admin_override=(current_role == "admin"),
            admin_target_id=swimmer_phone
        )

    # -------------------------------------------------------------
    # 2. TRAINER PROFILE (or Admin overriding Trainer)
    # -------------------------------------------------------------
    elif (current_role == "trainer") or (current_role == "admin" and admin_override_role == "trainer"):
        trainer_user = admin_target_id if (current_role == "admin" and admin_target_id) else (session.get("trainer_username") or "asdf")

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            whatsapp = request.form.get("whatsapp", "").strip()
            dob = request.form.get("dob", "").strip()
            gender = request.form.get("gender", "").strip()

            professional_title = request.form.get("professional_title", "").strip()
            bio = request.form.get("bio", "").strip()
            experience = request.form.get("experience", "").strip()
            spec_list = request.form.getlist("specialties")
            specialties = ",".join(spec_list) if spec_list else request.form.get("specialties", "").strip()
            levels_list = request.form.getlist("coaching_levels")
            coaching_levels = ",".join(levels_list) if levels_list else request.form.get("coaching_levels", "").strip()
            lang_list = request.form.getlist("languages")
            languages = ",".join(lang_list) if lang_list else request.form.get("languages", "").strip()

            qualification = request.form.get("qualification", "").strip()
            currently_working = request.form.get("currently_working", "").strip()
            residence_location = request.form.get("residence_location", "").strip()
            certificate_validity = request.form.get("certificate_validity", "").strip()

            loc_list = request.form.getlist("training_locations")
            training_locations = ",".join(loc_list) if loc_list else request.form.get("training_locations", "").strip()
            days_list = request.form.getlist("preferred_training_days")
            preferred_training_days = ",".join(days_list) if days_list else request.form.get("preferred_training_days", "").strip()
            available_slots = request.form.get("available_slots", "").strip()
            training_type = request.form.get("training_type", "").strip()
            max_students = request.form.get("max_students", "5").strip()

            public_profile_visible = bool(request.form.get("public_profile_visible"))
            show_experience = bool(request.form.get("show_experience"))
            show_qualifications = bool(request.form.get("show_qualifications"))
            show_profile_photo = bool(request.form.get("show_profile_photo"))

            # Admin-only overrides
            profile_approval_status = request.form.get("profile_approval_status", "Approved").strip() if current_role == "admin" else None
            is_blocked = (request.form.get("is_blocked") == "true") if current_role == "admin" and "is_blocked" in request.form else None

            cursor.execute("""
                UPDATE trainers 
                SET name = %s, phone = %s, email = %s, whatsapp = %s, dob = %s, gender = %s,
                    professional_title = %s, bio = %s, experience = %s, specialties = %s,
                    coaching_levels = %s, languages = %s, qualification = %s,
                    currently_working = %s, residence_location = %s, certificate_validity = %s,
                    training_locations = %s, preferred_training_days = %s, available_slots = %s,
                    training_type = %s, max_students = %s, public_profile_visible = %s,
                    show_experience = %s, show_qualifications = %s, show_profile_photo = %s
                WHERE username = %s
            """, (
                name, phone, email, whatsapp, dob, gender,
                professional_title, bio, experience, specialties,
                coaching_levels, languages, qualification,
                currently_working, residence_location, certificate_validity,
                training_locations, preferred_training_days, available_slots,
                training_type, int(max_students) if max_students.isdigit() else 5,
                public_profile_visible, show_experience, show_qualifications, show_profile_photo,
                trainer_user
            ))

            if current_role == "admin" and profile_approval_status:
                cursor.execute("UPDATE trainers SET profile_approval_status = %s WHERE username = %s", (profile_approval_status, trainer_user))
            if current_role == "admin" and is_blocked is not None:
                cursor.execute("UPDATE trainers SET is_blocked = %s WHERE username = %s", (is_blocked, trainer_user))

            conn.commit()

            # Update session user_name if current trainer
            if current_role == "trainer" and name:
                session["user_name"] = name

            flash("Trainer Profile updated successfully!", "success")
            if current_role == "admin":
                conn.close()
                return redirect(url_for("profile_page", user_type="trainer", id=trainer_user))
            conn.close()
            return redirect(url_for("profile_page"))

        # Fetch trainer record
        cursor.execute("SELECT * FROM trainers WHERE username = %s", (trainer_user,))
        t_row = cursor.fetchone()

        if not t_row:
            conn.close()
            flash("Trainer account not found.", "error")
            return redirect(url_for("index"))

        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'trainers' ORDER BY ordinal_position")
        t_cols = [c[0] for c in cursor.fetchall()]
        trainer_dict = dict(zip(t_cols, t_row))

        trainer_id_number = trainer_dict.get("id_number") or ""
        profile_pic = ""
        if trainer_id_number:
            cursor.execute("SELECT filename FROM profile_pictures WHERE id_number = %s", (trainer_id_number,))
            pic_row = cursor.fetchone()
            if pic_row and pic_row[0]:
                profile_pic = pic_row[0]

        # Coach uploaded gallery photos
        coach_gallery_photos = []
        try:
            cursor.execute("""
                SELECT id, photo_url, section, caption, is_published, created_at
                FROM gallery_photos
                WHERE coach_username = %s
                ORDER BY created_at DESC
            """, (trainer_user,))
            for grow in cursor.fetchall():
                coach_gallery_photos.append({
                    'id': grow[0],
                    'url': grow[1],
                    'section': grow[2],
                    'caption': grow[3] or '',
                    'is_published': bool(grow[4]),
                    'created_at': grow[5].strftime('%Y-%m-%d') if grow[5] else ''
                })
        except Exception as ge:
            conn.rollback()

        conn.close()

        specialties_arr = [s.strip() for s in (trainer_dict.get("specialties") or "").split(",") if s.strip()]
        levels_arr = [l.strip() for l in (trainer_dict.get("coaching_levels") or "").split(",") if l.strip()]
        languages_arr = [lang.strip() for lang in (trainer_dict.get("languages") or "").split(",") if lang.strip()]
        days_arr = [d.strip() for d in (trainer_dict.get("preferred_training_days") or "").split(",") if d.strip()]

        return render_template(
            "profile.html",
            role="trainer",
            profile_type="trainer",
            trainer=trainer_dict,
            trainer_specialties=specialties_arr,
            trainer_levels=levels_arr,
            trainer_languages=languages_arr,
            trainer_days=days_arr,
            id_number=trainer_id_number,
            profile_pic=profile_pic,
            coach_photos=coach_gallery_photos,
            is_admin_override=(current_role == "admin"),
            admin_target_id=trainer_user
        )

    # -------------------------------------------------------------
    # 3. ADMIN PROFILE OVERVIEW & DIRECTORY
    # -------------------------------------------------------------
    elif current_role == "admin":
        # Load all swimmers and trainers for the Admin Directory
        cursor.execute("""
            SELECT sp.phone, sp.name, sp.city, sp.skill_level, sp.account_status, sp.created_at,
                   COALESCE(pp.filename, '') as photo
            FROM swimmer_profiles sp
            LEFT JOIN user_activity ua ON ua.phone = sp.phone
            LEFT JOIN profile_pictures pp ON pp.id_number = ua.id_number
            ORDER BY sp.updated_at DESC
        """)
        all_swimmers = [
            {
                "phone": r[0],
                "name": r[1] or "Swimmer",
                "city": r[2] or "Hyderabad",
                "skill_level": r[3] or "Beginner",
                "account_status": r[4] or "Active",
                "registered": r[5].strftime("%b %Y") if r[5] else "2026",
                "photo": r[6]
            }
            for r in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT t.username, t.name, t.phone, t.experience, t.qualification, t.is_blocked, t.profile_approval_status,
                   COALESCE(pp.filename, '') as photo, t.id_number
            FROM trainers t
            LEFT JOIN profile_pictures pp ON pp.id_number = t.id_number
            ORDER BY t.name ASC
        """)
        all_trainers = [
            {
                "username": r[0],
                "name": r[1],
                "phone": r[2] or "",
                "experience": r[3] or "5+ yrs",
                "qualification": r[4] or "Certified Coach",
                "is_blocked": bool(r[5]),
                "status": r[6] or "Approved",
                "photo": r[7],
                "id_number": r[8] or ""
            }
            for r in cursor.fetchall()
        ]

        admin_id_num = session.get("id_number", "STPA0001")
        admin_pic = ""
        cursor.execute("SELECT filename FROM profile_pictures WHERE id_number = %s", (admin_id_num,))
        pic_row = cursor.fetchone()
        if pic_row and pic_row[0]:
            admin_pic = pic_row[0]

        conn.close()

        return render_template(
            "profile.html",
            role="admin",
            profile_type="admin",
            admin_name=session.get("user_name", "Super Admin"),
            admin_username="admin",
            id_number=admin_id_num,
            profile_pic=admin_pic,
            all_swimmers=all_swimmers,
            all_trainers=all_trainers
        )

    conn.close()
    flash("Please log in to view your profile.", "warning")
    return redirect(url_for("index"))


@login_required
def profile_upload_photo():
    current_role = session.get("role", "guest")
    if current_role != "trainer":
        flash("Only trainers can upload photos.", "error")
        return redirect(url_for("index"))

    trainer_user = session.get("trainer_username") or "asdf"

    files = request.files.getlist("training_pics") or request.files.getlist("training_pic")
    if not files or all(f.filename == "" for f in files):
        if "training_pic" in request.files and request.files["training_pic"].filename != "":
            files = [request.files["training_pic"]]
        else:
            flash("No file selected.", "error")
            return redirect(url_for("profile_page"))

    section = request.form.get("section", "coaching").strip().lower()
    if section not in ("achievements", "coaching", "swimmers"):
        section = "coaching"
    caption = request.form.get("caption", "").strip()

    from services.cloudinary_service import upload_image
    folder = f"swimtrackpro/coaches/{trainer_user}_gallery"

    conn = get_pg_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name, id_number, photos FROM trainers WHERE username = %s", (trainer_user,))
    trow = cursor.fetchone()
    coach_name = trow[0] if trow else trainer_user
    coach_id = trow[1] if (trow and trow[1]) else "STP-COACH"
    current_photos = trow[2] if (trow and trow[2]) else ""

    uploaded_urls = []
    for file in files:
        if file and file.filename != "":
            cloudinary_url = upload_image(file, folder=folder)
            if cloudinary_url:
                uploaded_urls.append(cloudinary_url)
                cursor.execute("""
                    INSERT INTO gallery_photos (photo_url, coach_username, coach_name, coach_id, section, caption, is_published, uploaded_by)
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE, 'coach')
                """, (cloudinary_url, trainer_user, coach_name, coach_id, section, caption or f"Training session with Coach {coach_name}"))

    if uploaded_urls:
        new_photos_list = [p for p in current_photos.split(",") if p.strip()] + uploaded_urls
        cursor.execute("UPDATE trainers SET photos = %s WHERE username = %s", (",".join(new_photos_list), trainer_user))
        conn.commit()
        flash(f"{len(uploaded_urls)} photo(s) submitted to album! Admin will review and publish them to the public gallery.", "success")
    else:
        flash("Failed to upload photo(s). Please try again.", "error")

    conn.close()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "count": len(uploaded_urls)})
    return redirect(url_for("profile_page"))


def logout():
    session.clear()
    return redirect(url_for("index"))


@admin_required("Only super admin can approve trainers.")
def approve_trainer(username):
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE trainers SET is_approved = TRUE WHERE username = %s", (username,))
    conn.commit()
    conn.close()
    flash(f"Trainer '{username}' approved successfully.", "success")
    return redirect(url_for("index") + "?section=coaches")


@admin_required("Only super admin can reject trainers.")
def reject_trainer(username):
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trainers WHERE username = %s", (username,))
    conn.commit()
    conn.close()
    flash(f"Trainer '{username}' rejected and registration deleted.", "success")
    return redirect(url_for("index") + "?section=coaches")


@admin_required("Only super admin can verify trainer proofs.")
def verify_trainer_proof(username):
    proof_type = (request.form.get("proof_type") or (request.json.get("proof_type") if request.is_json else None) or "").strip().lower()
    raw_status = (request.form.get("status") or (request.json.get("status") if request.is_json else None) or "").strip().lower()

    if raw_status in ("accepted", "verified", "accept"):
        status_val = "Verified"
    elif raw_status in ("decline", "declined", "reject", "rejected"):
        status_val = "Declined"
    else:
        status_val = "Pending"

    if proof_type not in ("id_proof", "qualification"):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"success": False, "error": "Invalid proof type."}), 400
        flash("Invalid proof type.", "danger")
        return redirect(url_for("index") + "?section=coaches")

    conn = get_pg_connection()
    cursor = conn.cursor()
    try:
        if proof_type == "id_proof":
            cursor.execute("UPDATE trainers SET id_proof_status = %s WHERE LOWER(username) = LOWER(%s)", (status_val, username.strip()))
        else:
            cursor.execute("UPDATE trainers SET qualification_status = %s WHERE LOWER(username) = LOWER(%s)", (status_val, username.strip()))
        conn.commit()
    except Exception as e:
        conn.rollback()
        try:
            cursor.execute("ALTER TABLE trainers ADD COLUMN IF NOT EXISTS id_proof_status TEXT DEFAULT 'pending'")
            cursor.execute("ALTER TABLE trainers ADD COLUMN IF NOT EXISTS qualification_status TEXT DEFAULT 'pending'")
            conn.commit()
            if proof_type == "id_proof":
                cursor.execute("UPDATE trainers SET id_proof_status = %s WHERE LOWER(username) = LOWER(%s)", (status_val, username.strip()))
            else:
                cursor.execute("UPDATE trainers SET qualification_status = %s WHERE LOWER(username) = LOWER(%s)", (status_val, username.strip()))
            conn.commit()
        except Exception as inner_e:
            conn.rollback()
            conn.close()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                return jsonify({"success": False, "error": str(inner_e)}), 500
            flash(f"Error updating proof status: {inner_e}", "danger")
            return redirect(url_for("index") + "?section=coaches")
    conn.close()

    proof_label = "ID Proof" if proof_type == "id_proof" else "Qualification Certificate"
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({
            "success": True,
            "username": username,
            "proof_type": proof_type,
            "status": status_val,
            "message": f"{proof_label} for coach '{username}' marked as {status_val}."
        })

    flash(f"{proof_label} for coach '{username}' marked as {status_val}.", "success")
    return redirect(url_for("index") + "?section=coaches")


@admin_required("Only super admin can verify trainer proofs.")
def verify_trainer_proof_alt():
    username = request.form.get("username") or (request.json.get("username") if request.is_json else "")
    return verify_trainer_proof(username)


@admin_required("Only super admin can delete bookings.")
def admin_delete_booking(booking_id):
    conn = get_pg_connection()
    cursor = conn.cursor()
    booking_info = None
    try:
        # Load booking info for notification before deletion
        cursor.execute("""
            SELECT booking_code, student_name, owner_name, owner_phone, start_date, time, package, email
            FROM bookings WHERE id = %s OR TRIM(id::text) = TRIM(%s)
        """, (str(booking_id), str(booking_id)))
        row = cursor.fetchone()
        if row:
            booking_info = {
                'id': booking_id,
                'booking_code': row[0] or str(booking_id),
                'student': row[1] or '',
                'owner_name': row[2] or '',
                'owner_phone': row[3] or '',
                'start_date': str(row[4]) if row[4] else '',
                'time': row[5] or '',
                'package': row[6] or '',
                'email': row[7] or ''
            }

        for cleanup_query in [
            'DELETE FROM makeup_requests WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)',
            'DELETE FROM makeup_credits WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)',
            'DELETE FROM package_pause_audit WHERE booking_id = %s OR TRIM(booking_id::text) = TRIM(%s)'
        ]:
            try:
                cursor.execute(cleanup_query, (str(booking_id), str(booking_id)))
            except Exception:
                pass
        cursor.execute("DELETE FROM bookings WHERE id = %s OR TRIM(id::text) = TRIM(%s)", (str(booking_id), str(booking_id)))
        conn.commit()

        # Send booking cancellation notification email to swimmer and admin alert
        if booking_info:
            try:
                from services.email_service import send_booking_deleted_email, send_booking_deleted_alert
                send_booking_deleted_email(booking_info)
                send_booking_deleted_alert(booking_info)
            except Exception as mail_err:
                print("Admin delete booking email error:", mail_err)

        flash(f"Booking ID {booking_id} deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error deleting booking: {e}", "danger")
    finally:
        conn.close()
    return redirect(url_for("index") + "?section=bookings")


@admin_required("Only super admin can assign coaches.")
def assign_coach(booking_id):
    trainer_username = request.form.get("trainer_username")
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET trainer_username = %s WHERE id = %s", (trainer_username, booking_id))
    conn.commit()
    conn.close()
    flash(f"Coach assigned successfully for Booking #{booking_id}.", "success")
    return redirect(url_for("index"))


@login_required
def submit_coach_feedback(trainer_username):
    current_role = session.get("role", "guest")
    if current_role != "guest":
        flash("Only guests/swimmers can leave feedback.", "error")
        return redirect(request.referrer or url_for("index"))

    rating = request.form.get("rating")
    comment = request.form.get("comment", "").strip()

    if not rating:
        flash("Please provide a rating.", "warning")
        return redirect(request.referrer or url_for("index"))

    try:
        rating_val = int(rating)
        if rating_val < 1 or rating_val > 5:
            raise ValueError()
    except ValueError:
        flash("Rating must be an integer between 1 and 5.", "warning")
        return redirect(request.referrer or url_for("index"))

    guest_name = session.get("user_name")
    guest_phone = session.get("phone")

    import re
    def clean_phone(p):
        return re.sub(r"\D", "", str(p)) if p else ""
        
    user_clean_phone = clean_phone(guest_phone)
    t_target = trainer_username.strip().lower()

    # Verify that the coach is assigned to the guest via active or completed bookings
    data = load_data()
    eligible = False
    
    for b in data.get("bookings", []):
        b_owner_phone = clean_phone(b.get("owner_phone"))
        b_owner_name = (b.get("owner_name") or "").strip().lower()
        b_student = (b.get("student") or "").strip().lower()
        b_created_by = (b.get("created_by") or "").strip().lower()
        
        name_match = (
            (bool(guest_name) and b_owner_name == guest_name.lower()) or
            (bool(guest_name) and b_created_by == guest_name.lower()) or
            (bool(guest_name) and b_student == guest_name.lower())
        )
        phone_match = (
            bool(user_clean_phone) and bool(b_owner_phone) and (
                user_clean_phone == b_owner_phone or
                user_clean_phone.endswith(b_owner_phone) or
                b_owner_phone.endswith(user_clean_phone)
            )
        )
        
        if name_match or phone_match:
            b_trainer = (b.get("trainer_username") or "").strip().lower()
            if b_trainer == t_target:
                if b.get("completed_classes", 0) > 0 or b.get("is_completed", False):
                    eligible = True
                    break

    if not eligible:
        flash("You can only submit a review for an active or completed session with this coach.", "error")
        return redirect(request.referrer or url_for("index"))

    conn = get_pg_connection()
    cursor = conn.cursor()

    # Check if trainer exists and is approved
    cursor.execute("SELECT username FROM trainers WHERE LOWER(username) = LOWER(%s) AND is_approved = TRUE", (trainer_username,))
    trainer_row = cursor.fetchone()
    if not trainer_row:
        conn.close()
        flash("Coach not found or not approved.", "error")
        return redirect(request.referrer or url_for("index"))
        
    actual_trainer_username = trainer_row[0]

    # Check if guest already submitted feedback for this trainer
    cursor.execute("""
        SELECT id FROM coach_feedback 
        WHERE trainer_username = %s AND guest_phone = %s
    """, (actual_trainer_username, guest_phone))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE coach_feedback 
            SET rating = %s, comment = %s, created_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (rating_val, comment, existing[0]))
    else:
        cursor.execute("""
            INSERT INTO coach_feedback (trainer_username, guest_name, guest_phone, rating, comment)
            VALUES (%s, %s, %s, %s, %s)
        """, (actual_trainer_username, guest_name, guest_phone, rating_val, comment))

    conn.commit()

    # Recalculate and update the trainer's overall rating
    cursor.execute("""
        SELECT AVG(rating) FROM coach_feedback WHERE trainer_username = %s
    """, (actual_trainer_username,))
    avg_rating_row = cursor.fetchone()
    if avg_rating_row and avg_rating_row[0] is not None:
        new_rating = round(float(avg_rating_row[0]), 2)
        cursor.execute("""
            UPDATE trainers SET rating = %s WHERE username = %s
        """, (new_rating, actual_trainer_username))
        conn.commit()

    conn.close()
    flash("Feedback submitted successfully!", "success")
    return redirect(request.referrer or url_for("index"))


@admin_required("Only admin can block trainers.")
def toggle_block_trainer(username):
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_blocked FROM trainers WHERE username = %s", (username,))
    row = cursor.fetchone()
    if row:
        new_status = not row[0]
        cursor.execute("UPDATE trainers SET is_blocked = %s WHERE username = %s", (new_status, username))
        conn.commit()
        if new_status:
            flash(f"Trainer {username} has been blocked and suspended.", "danger")
        else:
            flash(f"Trainer {username} has been unblocked.", "success")
    conn.close()
    return redirect(url_for("index") + "?section=coaches")

@admin_required("Only admin can block students.")
def toggle_block_student(phone):
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_blocked FROM students WHERE owner_phone = %s", (phone,))
    row = cursor.fetchone()
    if row:
        new_status = not row[0]
        cursor.execute("UPDATE students SET is_blocked = %s WHERE owner_phone = %s", (new_status, phone))
        conn.commit()
        if new_status:
            flash(f"Student with phone {phone} has been blocked and suspended.", "danger")
        else:
            flash(f"Student with phone {phone} has been unblocked.", "success")
    else:
        # Create student record if not found just to block them based on phone
        cursor.execute(
            "INSERT INTO students (owner_phone, student_name, owner_name, is_blocked) VALUES (%s, %s, %s, %s)",
            (phone, "Unknown", "Unknown", True)
        )
        conn.commit()
        flash(f"Phone {phone} has been added to blocked list.", "danger")
    conn.close()
    return redirect(url_for("index") + "?section=students")

@admin_required("Only admin can delete students.")
def delete_student(phone):
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT student_name FROM students WHERE owner_phone = %s", (phone,))
    row = cursor.fetchone()
    if row:
        # Delete related bookings first (or cascade if set up, but let's do it manually just in case)
        cursor.execute("DELETE FROM bookings WHERE owner_phone = %s", (phone,))
        cursor.execute("DELETE FROM students WHERE owner_phone = %s", (phone,))
        conn.commit()
        flash(f"Student with phone {phone} has been permanently deleted.", "success")
    else:
        flash("Student not found.", "danger")
    conn.close()
    return redirect(url_for("index") + "?section=students")


@admin_required("Only admin can edit students.")
def edit_student(phone):
    if request.method == "POST":
        new_name = request.form.get("name")
        new_owner = request.form.get("owner_name")
        new_phone = request.form.get("owner_phone")
        
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE students SET student_name = %s, owner_name = %s, owner_phone = %s WHERE owner_phone = %s",
            (new_name, new_owner, new_phone, phone)
        )
        # also update bookings that might use the old phone
        cursor.execute(
            "UPDATE bookings SET owner_phone = %s WHERE owner_phone = %s",
            (new_phone, phone)
        )
        conn.commit()
        conn.close()
        flash("Student details updated successfully.", "success")
        return redirect(url_for("index"))

@admin_required("Only admin can update packages.")
def update_package():
    if request.method == "POST":
        package_id = request.form.get("package_id")
        base_price = request.form.get("base_price")
        discount_percentage = request.form.get("discount_percentage")
        
        if package_id and base_price and discount_percentage:
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE packages SET base_price = %s, discount_percentage = %s WHERE id = %s",
                (base_price, discount_percentage, package_id)
            )
            conn.commit()
            conn.close()
            flash("Package pricing updated successfully.", "success")
        else:
            flash("Missing pricing fields.", "danger")
    return redirect(url_for("index"))


@admin_required("Only admin can update promotions.")
def update_promotion():
    if request.method == "POST":
        from services.promotion_service import save_promotion
        event_name = request.form.get("event_name", "").strip()
        badge_text = request.form.get("badge_text", "SPECIAL OFFER").strip()
        message = request.form.get("message", "").strip()
        cta_text = request.form.get("cta_text", "Explore Plans").strip()
        cta_url = request.form.get("cta_url", "/#plans").strip()
        banner_theme = request.form.get("banner_theme", "ocean").strip()
        is_active = request.form.get("is_active") in ["on", "true", "1", True]

        if not message:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                return jsonify({"success": False, "message": "Banner announcement message cannot be empty."}), 400
            flash("Banner announcement message cannot be empty.", "warning")
            return redirect(url_for("index"))

        saved_promo = save_promotion(
            event_name=event_name or "Special Offer",
            badge_text=badge_text,
            message=message,
            cta_text=cta_text,
            cta_url=cta_url,
            banner_theme=banner_theme,
            is_active=is_active
        )

        msg = f"Promotional banner for '{saved_promo['event_name']}' updated successfully!"
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"success": True, "message": msg, "promotion": saved_promo})

        flash(msg, "success")
    return redirect(url_for("index"))


@admin_required("Only admin can toggle promotions.")
def toggle_promotion():
    if request.method == "POST":
        from services.promotion_service import toggle_promotion_status
        is_active_val = None
        if "is_active" in request.form:
            is_active_val = request.form.get("is_active") in ["on", "true", "1", True]
        elif request.is_json and request.get_json(silent=True) and "is_active" in request.get_json(silent=True):
            is_active_val = bool(request.get_json(silent=True).get("is_active"))

        updated = toggle_promotion_status(is_active_val)
        status_text = "activated (LIVE on site)" if updated.get("is_active") else "paused / hidden"
        msg = f"Promotional banner is now {status_text}."

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"success": True, "message": msg, "is_active": updated.get("is_active"), "promotion": updated})

        flash(msg, "success")
    return redirect(url_for("index"))


def get_pricing_quote_api():
    """
    Decoupled pricing quote API endpoint.
    Returns calculated batch fee, per-person fee, discount %, and coach yield.
    """
    from services.pricing_service import get_package_quote
    data = request.get_json(silent=True) or {}
    package = request.args.get("package") or request.form.get("package") or data.get("package", "monthly_3d")
    persons = request.args.get("persons") or request.args.get("swimmer_count") or request.form.get("persons") or data.get("persons", 1)
    session_count = request.args.get("session_count") or request.form.get("session_count") or data.get("session_count")
    weekly_days = request.args.get("weekly_days") or request.form.get("weekly_days") or data.get("weekly_days")

    quote = get_package_quote(
        package_key=package,
        swimmer_count=persons,
        session_count=session_count,
        weekly_days=weekly_days
    )
    return jsonify({"success": True, "quote": quote})


def get_pricing_config_api():
    """
    Returns active pricing configuration (base rates, multipliers, discounts).
    """
    from services.pricing_service import get_pricing_config_dict
    return jsonify({"success": True, "config": get_pricing_config_dict()})


@admin_required("Only admin can update pricing configuration.")
def admin_update_pricing():
    """
    Admin endpoint to dynamically update base prices without code rewrites.
    """
    if request.method == "POST":
        from services.pricing_service import update_base_prices, get_base_prices
        data = request.get_json(silent=True) or request.form
        base_prices = {}
        for key in ["demo", "single", "monthly_2d", "monthly_3d", "3_months", "custom"]:
            if key in data and str(data.get(key)).strip() != "":
                try:
                    base_prices[key] = int(float(data.get(key)))
                except (ValueError, TypeError):
                    pass

        if base_prices:
            update_base_prices(base_prices)
            current_prices = get_base_prices()
            msg = "Base pricing rates updated successfully."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                return jsonify({"success": True, "message": msg, "base_prices": current_prices})
            flash(msg, "success")
        else:
            flash("No valid base price values provided.", "danger")
    return redirect(url_for("index"))


@admin_required("Only admin can edit trainers.")
def edit_trainer(username):
    if request.method == "POST":
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE trainers 
            SET name = %s, phone = %s, email = %s, experience = %s, 
                qualification = %s, currently_working = %s, residence_location = %s, rating = %s,
                bio = %s, specialties = %s, instagram = %s, facebook = %s, twitter = %s, youtube = %s
            WHERE username = %s
            """,
            (
                request.form.get("name"),
                request.form.get("phone"),
                request.form.get("email"),
                request.form.get("experience"),
                request.form.get("qualification"),
                request.form.get("currently_working"),
                request.form.get("residence_location"),
                request.form.get("rating"),
                request.form.get("bio", ""),
                request.form.get("specialties", ""),
                request.form.get("instagram", ""),
                request.form.get("facebook", ""),
                request.form.get("twitter", ""),
                request.form.get("youtube", ""),
                username
            )
        )
        conn.commit()
        conn.close()
        flash("Trainer details updated successfully.", "success")
        return redirect(url_for("index"))

@admin_required("Only admin can delete trainer images.")
def delete_trainer_image(username):
    filename = request.form.get("filename")
    if not filename:
        flash("Filename not provided.", "error")
        return redirect(url_for("index"))
        
    if request.method == "POST":
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT photos FROM trainers WHERE username = %s", (username,))
        row = cursor.fetchone()
        
        if row and row[0]:
            photos = row[0].split(",")
            if filename in photos:
                photos.remove(filename)
                new_photos_str = ",".join(photos)
                
                # Delete from database
                cursor.execute("UPDATE trainers SET photos = %s WHERE username = %s", (new_photos_str, username))
                
                # Delete from Cloudinary or local disk
                if filename.startswith('http'):
                    from services.cloudinary_service import delete_image
                    delete_image(filename)
                else:
                    import os
                    album_dir = os.path.join("static", "images", "Album")
                    filepath = os.path.join(album_dir, filename)
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    except Exception:
                        pass
                
                conn.commit()
                flash("Image deleted successfully.", "success")
            else:
                flash("Image not found in trainer's album.", "warning")
        
        conn.close()
    return redirect(url_for("index") + "?section=coaches")

@trainer_required("Only trainers can update their profile")
def update_trainer_profile():
    if request.method == "POST":
        username = session.get("trainer_username") or session.get("user_name")
        
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        experience = request.form.get("experience", "").strip()
        qualification = request.form.get("qualification", "").strip()
        currently_working = request.form.get("currently_working", "").strip()
        residence_location = request.form.get("residence_location", "").strip()
        whatsapp = request.form.get("whatsapp", "").strip()
        bio = request.form.get("bio", "").strip()
        specialties = request.form.get("specialties", "").strip()
        instagram = request.form.get("instagram", "").strip()
        facebook = request.form.get("facebook", "").strip()
        twitter = request.form.get("twitter", "").strip()
        youtube = request.form.get("youtube", "").strip()
        
        conn = get_pg_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE trainers SET
                    name = %s, phone = %s, email = %s, experience = %s,
                    qualification = %s, currently_working = %s, residence_location = %s, whatsapp = %s,
                    bio = %s, specialties = %s, instagram = %s, facebook = %s, twitter = %s, youtube = %s
                WHERE username = %s
            """, (name, phone, email, experience, qualification, currently_working, residence_location, whatsapp, bio, specialties, instagram, facebook, twitter, youtube, username))
            conn.commit()
            flash("Profile updated successfully!", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Error updating profile: {str(e)}", "danger")
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for("about_trainer"))

@login_required
def save_trainer_slots():
    current_role = session.get("role", "guest")
    if current_role != "trainer":
        return jsonify({"success": False, "error": "Unauthorized"}), 403
        
    trainer_user = session.get("trainer_username") or "asdf"
    import json
    try:
        data = request.get_json()
        slots = data.get("slots", [])
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE trainers
            SET available_slots = %s
            WHERE username = %s
        """, (json.dumps(slots), trainer_user))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@admin_required("Only admin can view marketing materials.")
def marketing_materials():
    return render_template("marketing_materials.html", role=session.get("role", "guest"))

@admin_required("Only admin can manage carousel.")
def upload_carousel_image():
    if "carousel_img" not in request.files:
        flash("No file part in the request.", "error")
        return redirect(url_for("index"))

    file = request.files["carousel_img"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    if file:
        from services.cloudinary_service import upload_image
        folder = "swimtrackpro/admin_carousel"
        cloudinary_url = upload_image(file, folder=folder)
        
        if not cloudinary_url:
            flash("Failed to upload image to Cloudinary.", "error")
            return redirect(url_for("index"))

        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO homepage_carousel (image_url) VALUES (%s)", (cloudinary_url,))
        conn.commit()
        conn.close()
        flash("Carousel image uploaded successfully!", "success")

    return redirect(url_for("index"))

@admin_required("Only admin can manage carousel.")
def delete_carousel_image(img_id):
    if request.method == "POST":
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT image_url FROM homepage_carousel WHERE id = %s", (img_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            image_url = row[0]
            from services.cloudinary_service import delete_image
            delete_image(image_url)
            
            cursor.execute("DELETE FROM homepage_carousel WHERE id = %s", (img_id,))
            conn.commit()
            flash("Carousel image deleted successfully.", "success")
        else:
            flash("Image not found.", "warning")
            
        conn.close()
    return redirect(url_for("index") + "?section=promotions")


@admin_required("Only admin can manage gallery photos.")
def admin_gallery_upload():
    """Upload photos directly to gallery by Admin."""
    files = request.files.getlist("photos") or request.files.getlist("photo")
    if not files or all(f.filename == "" for f in files):
        if "photo" in request.files and request.files["photo"].filename != "":
            files = [request.files["photo"]]
        else:
            flash("Please select at least one photo to upload.", "error")
            return redirect(url_for("index") + "?section=gallery")

    section = request.form.get("section", "swimmers").strip().lower()
    if section not in ("achievements", "coaching", "swimmers"):
        section = "swimmers"
    caption = request.form.get("caption", "").strip()

    from services.cloudinary_service import upload_image
    conn = get_pg_connection()
    cursor = conn.cursor()
    uploaded_count = 0

    for file in files:
        if file and file.filename != "":
            folder = f"swimtrackpro/admin_gallery/{section}"
            cloudinary_url = upload_image(file, folder=folder)
            if cloudinary_url:
                cursor.execute("""
                    INSERT INTO gallery_photos (photo_url, coach_username, coach_name, coach_id, section, caption, is_published, uploaded_by)
                    VALUES (%s, '', 'SwimTrackPro Academy', 'STP-ADMIN', %s, %s, TRUE, 'admin')
                """, (cloudinary_url, section, caption or "Doorstep Swimming Training in Hyderabad"))
                uploaded_count += 1

    conn.commit()
    conn.close()

    if uploaded_count > 0:
        flash(f"{uploaded_count} photo(s) added to gallery and published successfully!", "success")
    else:
        flash("Failed to upload photos. Please check file format and try again.", "error")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "count": uploaded_count})
    return redirect(url_for("index") + "?section=gallery")


@admin_required("Only admin can manage gallery photos.")
def admin_gallery_toggle_publish(photo_id):
    """Toggle publish status for a gallery photo."""
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_published FROM gallery_photos WHERE id = %s", (photo_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": "Photo not found"}), 404
        flash("Photo not found.", "warning")
        return redirect(url_for("index") + "?section=gallery")

    new_status = not bool(row[0])
    cursor.execute("UPDATE gallery_photos SET is_published = %s WHERE id = %s", (new_status, photo_id))
    conn.commit()
    conn.close()

    action_text = "published to landing page" if new_status else "unpublished from landing page"
    flash(f"Photo successfully {action_text}.", "success")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "is_published": new_status})
    return redirect(url_for("index") + "?section=gallery")


@admin_required("Only admin can manage gallery photos.")
def admin_gallery_delete(photo_id):
    """Delete a gallery photo."""
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT photo_url FROM gallery_photos WHERE id = %s", (photo_id,))
    row = cursor.fetchone()
    if row and row[0]:
        photo_url = row[0]
        if photo_url.startswith("http"):
            from services.cloudinary_service import delete_image
            delete_image(photo_url)
        cursor.execute("DELETE FROM gallery_photos WHERE id = %s", (photo_id,))
        conn.commit()
        flash("Gallery photo deleted successfully.", "success")
    else:
        flash("Photo not found.", "warning")
    conn.close()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True})
    return redirect(url_for("index") + "?section=gallery")


@admin_required("Only admin can manage gallery photos.")
def admin_gallery_bulk_action():
    """Bulk action on selected gallery photos: publish, unpublish, delete, change_section."""
    action = request.form.get("action", "").strip()
    photo_ids_raw = request.form.get("photo_ids", "")
    
    if not photo_ids_raw and request.is_json:
        data = request.get_json() or {}
        action = data.get("action", "")
        photo_ids_raw = data.get("photo_ids", [])

    if isinstance(photo_ids_raw, str):
        photo_ids = [int(x.strip()) for x in photo_ids_raw.split(",") if x.strip().isdigit()]
    elif isinstance(photo_ids_raw, list):
        photo_ids = [int(x) for x in photo_ids_raw if str(x).isdigit()]
    else:
        photo_ids = []

    if not photo_ids:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"success": False, "error": "No photos selected."}), 400
        flash("Please select at least one photo.", "warning")
        return redirect(url_for("index") + "?section=gallery")

    conn = get_pg_connection()
    cursor = conn.cursor()

    if action == "publish":
        cursor.execute("UPDATE gallery_photos SET is_published = TRUE WHERE id = ANY(%s)", (photo_ids,))
        conn.commit()
        msg = f"Published {len(photo_ids)} photo(s) to landing page gallery."
    elif action == "unpublish":
        cursor.execute("UPDATE gallery_photos SET is_published = FALSE WHERE id = ANY(%s)", (photo_ids,))
        conn.commit()
        msg = f"Unpublished {len(photo_ids)} photo(s) from landing page gallery."
    elif action == "delete":
        cursor.execute("SELECT photo_url FROM gallery_photos WHERE id = ANY(%s)", (photo_ids,))
        rows = cursor.fetchall()
        from services.cloudinary_service import delete_image
        for r in rows:
            if r[0] and r[0].startswith("http"):
                delete_image(r[0])
        cursor.execute("DELETE FROM gallery_photos WHERE id = ANY(%s)", (photo_ids,))
        conn.commit()
        msg = f"Deleted {len(photo_ids)} photo(s) permanently."
    elif action == "change_section":
        target_section = request.form.get("target_section", "coaching").strip()
        if target_section in ("achievements", "coaching", "swimmers"):
            cursor.execute("UPDATE gallery_photos SET section = %s WHERE id = ANY(%s)", (target_section, photo_ids))
            conn.commit()
            msg = f"Moved {len(photo_ids)} photo(s) to {target_section} section."
        else:
            msg = "Invalid target section."
    else:
        msg = "Unknown action."

    conn.close()
    flash(msg, "success")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"success": True, "message": msg, "count": len(photo_ids)})
    return redirect(url_for("index") + "?section=gallery")

@login_required
def delete_account():
    """Permanently delete a swimmer/guest account, personal data, and preferences.
    Preserves coach earnings and completed booking records under swimmer's real name.
    """
    import os
    import re

    current_role = session.get("role", "guest")
    if current_role != "guest":
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({
                "success": False,
                "message": "Only swimmer/guest accounts can be deleted via this option."
            }), 403
        flash("Only swimmer accounts can be self-deleted.", "danger")
        return redirect(url_for("index"))

    current_user = (session.get("user_name") or "").strip()
    current_phone = (session.get("phone") or "").strip()
    user_clean_phone = re.sub(r"\D", "", current_phone)
    user_norm = current_user.lower()
    user_id_number = (session.get("id_number") or "").strip()

    if not current_user and not user_clean_phone:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({
                "success": False,
                "message": "User session is invalid or expired."
            }), 400
        return redirect(url_for("index"))

    # 1. Active Bookings Guard: Check if swimmer has any active or ongoing classes with remaining sessions
    data = load_data()
    active_packages = []

    for b in data.get("bookings", []):
        if str(b.get("owner_phone") or "").startswith("ARCHIVED"):
            continue

        b_phone = re.sub(r"\D", "", str(b.get("owner_phone") or ""))
        b_owner = (b.get("owner_name") or "").strip().lower()
        b_created = (b.get("created_by") or "").strip().lower()

        matches = False
        if user_clean_phone and b_phone and (
            user_clean_phone == b_phone or
            user_clean_phone.endswith(b_phone) or
            b_phone.endswith(user_clean_phone)
        ):
            matches = True
        elif user_norm and (b_owner == user_norm or b_created == user_norm):
            matches = True

        if matches:
            is_comp = b.get("is_completed", False)
            rem_classes = b.get("remaining_classes", 0) or 0
            b_status = str(b.get("status") or "").strip().lower()
            pay_req = str(b.get("payment_request") or "").strip().lower()

            # Active package with remaining classes
            if not is_comp and rem_classes > 0 and (b_status in ("paid", "active", "confirmed", "pending") or pay_req == "approved"):
                pkg_name = b.get("package") or "Package"
                active_packages.append(f"{pkg_name} ({rem_classes} sessions remaining)")

    if active_packages:
        msg = (
            "Cannot delete account: You have ongoing swimming classes with remaining sessions: "
            + ", ".join(active_packages)
            + ". Please complete or cancel your classes before deleting your account."
        )
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"success": False, "message": msg}), 400
        flash(msg, "danger")
        return redirect(url_for("index"))

    # 2. Database Cleanup & Anonymization
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()

        # Delete any unconfirmed or draft bookings
        cursor.execute(r"""
            DELETE FROM bookings
            WHERE ((%s <> '' AND regexp_replace(COALESCE(owner_phone, ''), '\D', '', 'g') = %s)
               OR (%s <> '' AND LOWER(COALESCE(owner_name, '')) = %s))
              AND (status = 'unconfirmed' OR payment_request = 'unconfirmed')
        """, (user_clean_phone, user_clean_phone, user_norm, user_norm))

        # Archive completed bookings: anonymize phone and email, keep student_name and fee intact for coach
        cursor.execute(r"""
            UPDATE bookings
            SET owner_phone = 'ARCHIVED',
                email = ''
            WHERE ((%s <> '' AND regexp_replace(COALESCE(owner_phone, ''), '\D', '', 'g') = %s)
               OR (%s <> '' AND LOWER(COALESCE(owner_name, '')) = %s))
        """, (user_clean_phone, user_clean_phone, user_norm, user_norm))

        # Remove student profiles
        cursor.execute(r"""
            DELETE FROM students
            WHERE (%s <> '' AND regexp_replace(COALESCE(owner_phone, ''), '\D', '', 'g') = %s)
               OR (%s <> '' AND LOWER(COALESCE(owner_name, '')) = %s)
        """, (user_clean_phone, user_clean_phone, user_norm, user_norm))

        # Remove user_activity record (resets login history, tour status, and STPS ID for clean slate)
        cursor.execute(r"""
            DELETE FROM user_activity
            WHERE role = 'guest'
              AND ((%s <> '' AND regexp_replace(COALESCE(phone, ''), '\D', '', 'g') = %s)
               OR (%s <> '' AND LOWER(COALESCE(user_name, '')) = %s))
        """, (user_clean_phone, user_clean_phone, user_norm, user_norm))

        # Remove guest favorites
        if user_clean_phone or current_phone:
            cursor.execute(r"""
                DELETE FROM guest_favorites
                WHERE (%s <> '' AND regexp_replace(COALESCE(guest_phone, ''), '\D', '', 'g') = %s)
                   OR (%s <> '' AND guest_phone = %s)
            """, (user_clean_phone, user_clean_phone, current_phone, current_phone))

        # Remove notice reads
        cursor.execute("""
            DELETE FROM notice_reads
            WHERE user_type = 'student'
              AND (user_id = %s OR user_id = %s OR LOWER(user_id) = %s)
        """, (user_id_number, current_phone, user_norm))

        # Anonymize coach feedback phone while keeping real name and rating for coach
        cursor.execute(r"""
            UPDATE coach_feedback
            SET guest_phone = 'ARCHIVED_' || id::text
            WHERE (%s <> '' AND regexp_replace(COALESCE(guest_phone, ''), '\D', '', 'g') = %s)
               OR (%s <> '' AND guest_phone = %s)
        """, (user_clean_phone, user_clean_phone, current_phone, current_phone))

        # Remove ID card profile picture if stored
        if user_id_number:
            cursor.execute("SELECT filename FROM profile_pictures WHERE id_number = %s", (user_id_number,))
            pic_row = cursor.fetchone()
            if pic_row and pic_row[0]:
                pic_file = pic_row[0]
                if pic_file.startswith("http"):
                    try:
                        from services.cloudinary_service import delete_image
                        delete_image(pic_file)
                    except Exception:
                        pass
                else:
                    filepath = os.path.join("static", "profile_pictures", pic_file)
                    if os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                        except Exception:
                            pass
            cursor.execute("DELETE FROM profile_pictures WHERE id_number = %s", (user_id_number,))

        conn.commit()
        conn.close()

    except Exception as e:
        print("Error during account deletion:", e)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({
                "success": False,
                "message": "A database error occurred while deleting your account. Please try again."
            }), 500
        flash("An error occurred while deleting your account. Please try again.", "danger")
        return redirect(url_for("index"))

    # 3. Clear session
    session.clear()
    flash("Your account and personal data have been permanently deleted.", "success")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({
            "success": True,
            "message": "Your account has been deleted successfully.",
            "redirect": url_for("index")
        })

    return redirect(url_for("index"))


def register_general_routes(app):
    """Register routes with their legacy endpoint names unchanged."""

    app.add_url_rule(
        "/about-trainer",
        endpoint="about_trainer",
        view_func=about_trainer,
    )
    app.add_url_rule(
        "/trainer/update_profile",
        endpoint="update_trainer_profile",
        view_func=update_trainer_profile,
        methods=["POST"]
    )

    # SEO Landing Pages
    SEO_PAGES = {
        'swimming-coaches-hyderabad': {
            'title': 'Swimming Coaches in Hyderabad | SwimTrackPro',
            'h1': 'Find Elite Swimming Coaches in Hyderabad',
            'description': 'Looking for certified swimming coaches in Hyderabad? SwimTrackPro connects you with elite private trainers who teach at your apartment or community pool.',
            'content_html': '<p>Hyderabad has a growing demand for high-quality aquatic fitness. Whether you are a beginner looking to overcome water phobia or an advanced swimmer aiming to perfect your stroke, our verified swimming coaches in Hyderabad are here to help.</p><p>We specialize in doorstep coaching—meaning our trainers travel to your apartment, villa, or community club pool. Skip the traffic and learn in the privacy and comfort of your own facility.</p><ul><li>Certified & background-checked professionals</li><li>Flexible timings for adults and kids</li><li>Personalized 1-on-1 and group coaching</li></ul>'
        },
        'swimming-classes-hyderabad': {
            'title': 'Private Swimming Classes in Hyderabad | SwimTrackPro',
            'h1': 'Premium Swimming Classes in Hyderabad',
            'description': 'Book private swimming classes in Hyderabad. Learn swimming at your own apartment or villa pool with our professional, certified swimming instructors.',
            'content_html': '<p>Finding the right swimming classes in Hyderabad is easier than ever. SwimTrackPro brings the classes to you. Our experienced instructors conduct sessions directly at your residential pool.</p><p>Our structured curriculum covers water safety, basic survival strokes, advanced competitive strokes (freestyle, breaststroke, backstroke, butterfly), and endurance training.</p><ul><li>Monthly and custom coaching packages</li><li>Real-time progress tracking</li><li>Makeup sessions for missed classes</li></ul>'
        },
        'swimming-coach-gachibowli': {
            'title': 'Swimming Coach in Gachibowli, Hyderabad | SwimTrackPro',
            'h1': 'Private Swimming Coach in Gachibowli',
            'description': 'Hire a private swimming coach in Gachibowli. SwimTrackPro offers elite doorstep swimming instruction for residents of Gachibowli and nearby areas.',
            'content_html': '<p>If you live in Gachibowli or the surrounding IT corridor, navigating traffic to reach a public pool can be a hassle. SwimTrackPro provides dedicated swimming coaches in Gachibowli who travel to your residential society pool.</p><p>We partner with residents of major apartment complexes and villas in Gachibowli to provide safe, hygienic, and professional swimming instruction.</p>'
        },
        'private-swimming-coaching': {
            'title': 'Private Swimming Coaching | Doorstep Trainers | SwimTrackPro',
            'h1': 'Exclusive Private Swimming Coaching',
            'description': 'Experience the benefits of private swimming coaching. Our elite trainers provide personalized 1-on-1 instruction at your own pool.',
            'content_html': '<p>Private swimming coaching offers unparalleled focus and rapid skill acquisition. Unlike crowded public batches, our 1-on-1 sessions ensure the coach is entirely focused on your technique, breathing, and safety.</p><p>Our private coaches evaluate your current fitness level and customize a training plan that aligns with your specific goals—whether that is weight loss, triathlon preparation, or basic water survival.</p>'
        },
        'kids-swimming-classes-hyderabad': {
            'title': 'Kids Swimming Classes in Hyderabad | Safe & Fun | SwimTrackPro',
            'h1': 'Kids Swimming Classes in Hyderabad',
            'description': 'Enroll your children in safe, fun kids swimming classes in Hyderabad. Our verified coaches teach water safety and swimming skills at your apartment pool.',
            'content_html': '<p>Water safety is an essential life skill for every child. SwimTrackPro offers specialized kids swimming classes in Hyderabad, conducted safely in the familiar environment of your own community pool.</p><p>Our coaches are trained in child-friendly teaching methodologies, ensuring that your kids overcome their fear of water while having fun. We maintain strict safety standards and encourage parents to watch the sessions from the comfort of their own pool deck.</p><ul><li>Focus on water safety and survival techniques</li><li>Engaging, game-based learning for younger kids</li><li>Strict verification process for all kids coaches</li></ul>'
        }
    }

    def create_seo_route(slug):
        def seo_landing():
            page_data = SEO_PAGES[slug]
            return render_template('seo_landing.html', page_data=page_data, page_slug=slug)
        # Ensure unique function names for flask
        seo_landing.__name__ = f"seo_landing_{slug.replace('-', '_')}"
        app.add_url_rule(f'/{slug}', view_func=seo_landing)

    for slug in SEO_PAGES.keys():
        create_seo_route(slug)

    @app.route('/robots.txt')
    def robots_txt():
        lines = [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin",
            "Disallow: /dashboard",
            "Disallow: /api/",
            "Disallow: /profile",
            "Sitemap: https://swimtrackpro.onrender.com/sitemap.xml"
        ]
        from flask import Response
        return Response("\n".join(lines), mimetype="text/plain")

    @app.route('/sitemap.xml')
    def sitemap_xml():
        urls = [
            "https://swimtrackpro.onrender.com/",
            "https://swimtrackpro.onrender.com/about-swimming",
            "https://swimtrackpro.onrender.com/about",
            "https://swimtrackpro.onrender.com/help",
            "https://swimtrackpro.onrender.com/register",
        ]
        # Add SEO landing pages
        for slug in SEO_PAGES.keys():
            urls.append(f"https://swimtrackpro.onrender.com/{slug}")
            
        # Dynamically fetch coaches if possible? We will just keep it static-ish for now to avoid db calls in sitemap unless easy
        xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for url in urls:
            xml.append(f"  <url>\n    <loc>{url}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>")
        xml.append('</urlset>')
        
        from flask import Response
        return Response("\n".join(xml), mimetype="application/xml")

    # Add dynamic route at the end of register_general_routes

    app.add_url_rule(
        "/help",
        endpoint="help_page",
        view_func=help_page,
    )
    app.add_url_rule(
        "/about-swimming",
        endpoint="about_swimming",
        view_func=about_swimming,
    )
    app.add_url_rule(
        "/about",
        endpoint="about_page",
        view_func=about_page,
    )
    app.add_url_rule(
        "/promo",
        endpoint="marketing_materials",
        view_func=marketing_materials,
    )
    app.add_url_rule(
        "/faq",
        endpoint="faq_page",
        view_func=faq_page,
    )
    app.add_url_rule(
        "/update_notice",
        endpoint="update_notice",
        view_func=update_notice,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/update_package",
        endpoint="update_package",
        view_func=update_package,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/update_promotion",
        endpoint="update_promotion",
        view_func=update_promotion,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/toggle_promotion",
        endpoint="toggle_promotion",
        view_func=toggle_promotion,
        methods=["POST"],
    )
    def profile_update_password():
        current_role = session.get("role")
        if not current_role:
            return redirect(url_for("index"))

        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not new_password or len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect(url_for("profile_page"))

        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("profile_page"))

        conn = get_pg_connection()
        cursor = conn.cursor()

        if current_role == "trainer":
            trainer_user = session.get("trainer_username")
            cursor.execute("UPDATE trainers SET password = %s WHERE username = %s", (new_password, trainer_user))
            conn.commit()
            conn.close()
            flash("Trainer password updated successfully!", "success")
            return redirect(url_for("profile_page"))

        elif current_role == "admin":
            admin_user = session.get("admin_username") or "admin"
            cursor.execute("UPDATE trainers SET password = %s WHERE LOWER(username) = LOWER(%s)", (new_password, admin_user))
            try:
                cursor.execute("UPDATE admins SET password = %s WHERE LOWER(username) = LOWER(%s)", (new_password, admin_user))
            except Exception:
                pass
            conn.commit()
            conn.close()
            flash("Super Admin password updated successfully!", "success")
            return redirect(url_for("profile_page"))

        elif current_role == "guest":
            # Swimmer security confirmation
            conn.close()
            flash("Security settings updated successfully!", "success")
            return redirect(url_for("profile_page"))

        conn.close()
        return redirect(url_for("profile_page"))

    @app.route('/api/my_id_card')
    def api_my_id_card():
        if 'user_name' not in session:
            return jsonify({'error': 'Not logged in'}), 401
            
        role = session.get('role', 'guest')
        user_name = session.get('user_name', '')
        id_number = session.get('id_number', '')
        
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        photo = None
        title = "SwimTrackPro Guest"
        phone = session.get('phone', '')
        email = ""
        address = ""
        
        if role == 'admin':
            title = "SwimTrackPro Admin"
            cursor.execute("SELECT phone, email, residence_location FROM trainers WHERE LOWER(username) = LOWER(%s)", (session.get('admin_username', 'admin'),))
            row = cursor.fetchone()
            if row:
                phone, email, address = row[0], row[1], row[2]
        elif role == 'trainer':
            title = "SwimTrackPro Coach"
            cursor.execute("SELECT phone, email, residence_location FROM trainers WHERE username = %s", (session.get('trainer_username'),))
            row = cursor.fetchone()
            if row:
                phone, email, address = row[0], row[1], row[2]
        else:
            title = "SwimTrackPro Student"
            
        # Fetch from profile_pictures table
        cursor.execute("SELECT filename FROM profile_pictures WHERE id_number = %s", (id_number,))
        pic_row = cursor.fetchone()
        if pic_row and pic_row[0]:
            # If it's a Cloudinary URL, use it directly, otherwise keep old static path for backwards compatibility
            filename = pic_row[0]
            if filename.startswith('http'):
                photo = filename
            else:
                photo = url_for('static', filename='profile_pictures/' + filename)
            
        conn.close()

        return jsonify({
            'name': user_name.title(),
            'title': title,
            'id_number': id_number,
            'phone': phone,
            'email': email,
            'address': address,
            'photo': photo
        })

    @app.route('/api/upload_id_card_photo', methods=['POST'])
    def api_upload_id_card_photo():
        if 'user_name' not in session or 'id_number' not in session:
            return jsonify({'error': 'Not logged in'}), 401

        if 'profile_pic' not in request.files:
            return jsonify({'error': 'No file part in the request.'}), 400

        file = request.files['profile_pic']
        if file.filename == '':
            return jsonify({'error': 'No file selected.'}), 400

        if file:
            id_number = session.get('id_number', 'UNKNOWN')
            role = session.get('role', 'students')
            if role == 'admin' and request.form.get('target_id_number'):
                id_number = request.form.get('target_id_number')
            folder = f"swimtrackpro/{role}_id_cards"
            
            from services.cloudinary_service import upload_image, delete_image
            
            # Fetch existing to delete from Cloudinary if replacing
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT filename FROM profile_pictures WHERE id_number = %s", (id_number,))
            old_pic = cursor.fetchone()
            if old_pic and old_pic[0] and old_pic[0].startswith('http'):
                delete_image(old_pic[0])
            
            # Upload new image
            cloudinary_url = upload_image(file, folder=folder)
            if not cloudinary_url:
                conn.close()
                return jsonify({'error': 'Failed to upload image to Cloudinary'}), 500
            
            # Upsert into profile_pictures
            cursor.execute("""
                INSERT INTO profile_pictures (id_number, filename, updated_at) 
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (id_number) 
                DO UPDATE SET filename = EXCLUDED.filename, updated_at = EXCLUDED.updated_at
            """, (id_number, cloudinary_url))

            conn.commit()
            conn.close()

            return jsonify({'success': True, 'photo': cloudinary_url})
            
        return jsonify({'error': 'Upload failed'}), 500

    @app.route('/api/remove_id_card_photo', methods=['POST'])
    def api_remove_id_card_photo():
        if 'user_name' not in session or 'id_number' not in session:
            return jsonify({'error': 'Not logged in'}), 401
            
        id_number = session.get('id_number')
        if session.get('role') == 'admin' and request.form.get('target_id_number'):
            id_number = request.form.get('target_id_number')
        
        conn = get_pg_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT filename FROM profile_pictures WHERE id_number = %s", (id_number,))
        row = cursor.fetchone()
        
        if row and row[0]:
            filename = row[0]
            if filename.startswith('http'):
                from services.cloudinary_service import delete_image
                delete_image(filename)
            else:
                import os
                filepath = os.path.join("static", "profile_pictures", filename)
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
            
            cursor.execute("DELETE FROM profile_pictures WHERE id_number = %s", (id_number,))
            conn.commit()
        
        conn.close()
        
        return jsonify({'success': True})

    app.add_url_rule(
        "/profile",
        endpoint="profile_page",
        view_func=profile_page,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/trainer/save_slots",
        endpoint="save_trainer_slots",
        view_func=save_trainer_slots,
        methods=["POST"]
    )
    app.add_url_rule(
        "/profile/update_password",
        endpoint="profile_update_password",
        view_func=profile_update_password,
        methods=["POST"],
    )
    app.add_url_rule(
        "/profile/upload-photo",
        endpoint="profile_upload_photo",
        view_func=profile_upload_photo,
        methods=["POST"],
    )
    app.add_url_rule(
        "/logout",
        endpoint="logout",
        view_func=logout,
    )
    app.add_url_rule(
        "/admin/approve_trainer/<username>",
        endpoint="approve_trainer",
        view_func=approve_trainer,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/reject_trainer/<username>",
        endpoint="reject_trainer",
        view_func=reject_trainer,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/verify_trainer_proof/<username>",
        endpoint="verify_trainer_proof",
        view_func=verify_trainer_proof,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/trainer/verify_proof",
        endpoint="verify_trainer_proof_alt",
        view_func=verify_trainer_proof_alt,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/delete_booking/<booking_id>",
        endpoint="admin_delete_booking",
        view_func=admin_delete_booking,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/assign_coach/<booking_id>",
        endpoint="assign_coach",
        view_func=assign_coach,
        methods=["POST"],
    )
    app.add_url_rule(
        "/coach/feedback/<trainer_username>",
        endpoint="submit_coach_feedback",
        view_func=submit_coach_feedback,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/toggle_block_trainer/<username>",
        endpoint="toggle_block_trainer",
        view_func=toggle_block_trainer,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/toggle_block_student/<phone>",
        endpoint="toggle_block_student",
        view_func=toggle_block_student,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/delete_student/<phone>",
        endpoint="delete_student",
        view_func=delete_student,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/edit_student/<phone>",
        endpoint="edit_student",
        view_func=edit_student,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/edit_trainer/<username>",
        endpoint="edit_trainer",
        view_func=edit_trainer,
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/delete_trainer_image/<username>",
        endpoint="delete_trainer_image",
        view_func=delete_trainer_image,
        methods=["POST"]
    )


    app.add_url_rule(
        "/admin/carousel/upload",
        endpoint="upload_carousel_image",
        view_func=upload_carousel_image,
        methods=["POST"]
    )
    app.add_url_rule(
        "/admin/carousel/delete/<int:img_id>",
        endpoint="delete_carousel_image",
        view_func=delete_carousel_image,
        methods=["POST"]
    )
    app.add_url_rule(
        "/api/pricing/quote",
        endpoint="get_pricing_quote_api",
        view_func=get_pricing_quote_api,
        methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/api/pricing/config",
        endpoint="get_pricing_config_api",
        view_func=get_pricing_config_api,
        methods=["GET"]
    )
    app.add_url_rule(
        "/admin/pricing/update",
        endpoint="admin_update_pricing",
        view_func=admin_update_pricing,
        methods=["POST"]
    )
    app.add_url_rule(
        "/account/delete",
        endpoint="delete_account",
        view_func=delete_account,
        methods=["POST"]
    )
    app.add_url_rule(
        "/admin/gallery/upload",
        endpoint="admin_gallery_upload",
        view_func=admin_gallery_upload,
        methods=["POST"]
    )
    app.add_url_rule(
        "/admin/gallery/toggle_publish/<int:photo_id>",
        endpoint="admin_gallery_toggle_publish",
        view_func=admin_gallery_toggle_publish,
        methods=["POST"]
    )
    app.add_url_rule(
        "/admin/gallery/delete/<int:photo_id>",
        endpoint="admin_gallery_delete",
        view_func=admin_gallery_delete,
        methods=["POST"]
    )
    app.add_url_rule(
        "/admin/gallery/bulk-action",
        endpoint="admin_gallery_bulk_action",
        view_func=admin_gallery_bulk_action,
        methods=["POST"]
    )
