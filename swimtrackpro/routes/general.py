"""General authenticated pages and session routes."""

from flask import flash, redirect, render_template, request, session, url_for

from services.settings_service import set_setting
from swimtrackpro.auth import login_required, trainer_required, admin_required
from swimtrackpro.runtime import get_pg_connection, load_data


@login_required
def about_trainer():
    current_user = session.get("user_name")
    current_phone = session.get("phone")
    current_role = session.get("role", "guest")

    conn = get_pg_connection()
    cursor = conn.cursor()

    if current_role == "trainer":
        trainer_user = session.get("trainer_username") or "asdf"
        cursor.execute("""
            SELECT username, name, phone, email, experience, qualification, currently_working, residence_location, rating, photos 
            FROM trainers WHERE username = %s
        """, (trainer_user,))
        trainers = cursor.fetchall()
    else:
        # Swimmer/Guest: find trainer usernames from bookings
        data = load_data()
        bookings = [
            b for b in data.get("bookings", [])
            if (b.get("owner_name") or "").strip().lower() == current_user
            and b.get("owner_phone") == current_phone
        ]
        assigned_usernames = list(set([b.get("trainer_username", "asdf") for b in bookings if b.get("trainer_username")]))
        if not assigned_usernames:
            assigned_usernames = ["asdf"]

        placeholders = ", ".join(["%s"] * len(assigned_usernames))
        cursor.execute(f"""
            SELECT username, name, phone, email, experience, qualification, currently_working, residence_location, rating, photos 
            FROM trainers WHERE username IN ({placeholders})
        """, tuple(assigned_usernames))
        trainers = cursor.fetchall()

        if not trainers:
            cursor.execute("""
                SELECT username, name, phone, email, experience, qualification, currently_working, residence_location, rating, photos 
                FROM trainers
            """)
            trainers = cursor.fetchall()

    conn.close()

    coaches_list = []
    for r in trainers:
        coaches_list.append({
            "username": r[0],
            "name": r[1],
            "phone": r[2] or "",
            "email": r[3] or "",
            "experience": r[4] or "5+ Years",
            "qualification": r[5] or "Certified Swim Coach",
            "currently_working": r[6] or "SwimTrackPro Academy",
            "residence_location": r[7] or "Local Camp",
            "rating": float(r[8]) if r[8] is not None else 5.0,
            "photos": [p.strip() for p in (r[9] or "").split(",") if p.strip()]
        })

    return render_template("about_trainer.html", coaches=coaches_list, role=current_role)


@login_required
def help_page():
    return render_template("help.html", role=session.get("role", "guest"))


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
    if current_role != "trainer":
        flash("Only trainers have a profile page.", "error")
        return redirect(url_for("index"))

    trainer_user = session.get("trainer_username") or "asdf"
    conn = get_pg_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        experience = request.form.get("experience")
        qualification = request.form.get("qualification")
        currently_working = request.form.get("currently_working")
        residence_location = request.form.get("residence_location")

        cursor.execute("""
            UPDATE trainers 
            SET name = %s, phone = %s, email = %s, experience = %s, qualification = %s, currently_working = %s, residence_location = %s
            WHERE username = %s
        """, (name, phone, email, experience, qualification, currently_working, residence_location, trainer_user))
        conn.commit()
        flash("Profile updated successfully!", "success")

    cursor.execute("""
        SELECT username, name, phone, email, experience, qualification, currently_working, residence_location, id_proof, rating 
        FROM trainers WHERE username = %s
    """, (trainer_user,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        flash("Trainer not found.", "error")
        return redirect(url_for("index"))

    trainer_data = {
        "username": row[0],
        "name": row[1],
        "phone": row[2] or "",
        "email": row[3] or "",
        "experience": row[4] or "",
        "qualification": row[5] or "",
        "currently_working": row[6] or "",
        "residence_location": row[7] or "",
        "id_proof": row[8] or "",
        "rating": float(row[9]) if row[9] is not None else 5.0
    }

    return render_template("profile.html", trainer=trainer_data, role=current_role)


@login_required
def profile_upload_photo():
    import os
    import time
    from werkzeug.utils import secure_filename

    current_role = session.get("role", "guest")
    if current_role != "trainer":
        flash("Only trainers can upload photos.", "error")
        return redirect(url_for("index"))

    trainer_user = session.get("trainer_username") or "asdf"

    if "training_pic" not in request.files:
        flash("No file part in the request.", "error")
        return redirect(url_for("profile_page"))

    file = request.files["training_pic"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("profile_page"))

    if file:
        filename = secure_filename(file.filename)
        filename = f"{trainer_user}_{int(time.time())}_{filename}"

        album_dir = os.path.join("static", "images", "Album")
        os.makedirs(album_dir, exist_ok=True)

        filepath = os.path.join(album_dir, filename)
        file.save(filepath)

        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT photos FROM trainers WHERE username = %s", (trainer_user,))
        row = cursor.fetchone()

        current_photos = row[0] if (row and row[0]) else ""
        if current_photos:
            new_photos = f"{current_photos},{filename}"
        else:
            new_photos = filename

        cursor.execute("UPDATE trainers SET photos = %s WHERE username = %s", (new_photos, trainer_user))
        conn.commit()
        conn.close()

        flash("Photo uploaded and added to your album successfully!", "success")

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
    return redirect(url_for("index"))


@admin_required("Only super admin can reject trainers.")
def reject_trainer(username):
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trainers WHERE username = %s", (username,))
    conn.commit()
    conn.close()
    flash(f"Trainer '{username}' rejected and registration deleted.", "success")
    return redirect(url_for("index"))


@admin_required("Only super admin can delete bookings.")
def admin_delete_booking(booking_id):
    conn = get_pg_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
    conn.commit()
    conn.close()
    flash(f"Booking ID {booking_id} deleted successfully.", "success")
    return redirect(url_for("index"))


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


def register_general_routes(app):
    """Register routes with their legacy endpoint names unchanged."""

    app.add_url_rule(
        "/about-trainer",
        endpoint="about_trainer",
        view_func=about_trainer,
    )
    app.add_url_rule(
        "/help",
        endpoint="help_page",
        view_func=help_page,
    )
    app.add_url_rule(
        "/update_notice",
        endpoint="update_notice",
        view_func=update_notice,
        methods=["POST"],
    )
    app.add_url_rule(
        "/profile",
        endpoint="profile_page",
        view_func=profile_page,
        methods=["GET", "POST"],
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
