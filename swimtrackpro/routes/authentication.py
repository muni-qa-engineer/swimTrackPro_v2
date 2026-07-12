"""Authentication routes with legacy URL and endpoint compatibility."""

from flask import flash, redirect, request, render_template, session, url_for


def register_authentication_routes(
    app,
    *,
    get_pg_connection,
    admin_username,
    admin_password,
):
    def login():
        role = (request.form.get("role") or "").lower()
        name = (request.form.get("name") or "").strip()
        password = (request.form.get("password") or "").strip()
        phone = (request.form.get("phone") or "").strip()

        if role == "trainer":
            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, password, name, is_approved FROM trainers WHERE LOWER(username) = LOWER(%s)",
                (name.lower(),)
            )
            trainer_row = cursor.fetchone()
            conn.close()

            if trainer_row and trainer_row[1] == password:
                if not trainer_row[3]:
                    flash("Your trainer registration is pending admin approval.", "warning")
                    return redirect(url_for("index"))

                session["user_name"] = trainer_row[2]
                session["role"] = "trainer"
                session["trainer_username"] = trainer_row[0]

                conn = get_pg_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, current_login FROM user_activity WHERE LOWER(user_name) = LOWER(%s) AND role = %s",
                    (trainer_row[2], "trainer")
                )
                act_row = cursor.fetchone()
                if act_row:
                    cursor.execute(
                        "UPDATE user_activity SET previous_login = %s, current_login = CURRENT_TIMESTAMP, phone = %s WHERE id = %s",
                        (act_row[1], "", act_row[0])
                    )
                else:
                    cursor.execute(
                        "INSERT INTO user_activity (user_name, phone, role, current_login, previous_login) VALUES (%s, %s, %s, CURRENT_TIMESTAMP, NULL)",
                        (trainer_row[2], "", "trainer")
                    )
                conn.commit()
                conn.close()
                return redirect(url_for("index"))

            flash("Invalid trainer credentials")
            return redirect(url_for("index"))

        if role == "admin":
            if name.upper() == "M1400" and password == "51400":
                session["user_name"] = "Super Admin"
                session["role"] = "admin"
                session["admin_username"] = "admin"

                conn = get_pg_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, current_login FROM user_activity WHERE LOWER(user_name) = 'super admin' AND role = 'admin'"
                )
                act_row = cursor.fetchone()
                if act_row:
                    cursor.execute(
                        "UPDATE user_activity SET previous_login = %s, current_login = CURRENT_TIMESTAMP, phone = %s WHERE id = %s",
                        (act_row[1], "", act_row[0])
                    )
                else:
                    cursor.execute(
                        "INSERT INTO user_activity (user_name, phone, role, current_login, previous_login) VALUES (%s, %s, %s, CURRENT_TIMESTAMP, NULL)",
                        ("Super Admin", "", "admin")
                    )
                conn.commit()
                conn.close()
                return redirect(url_for("index"))

            flash("Invalid admin credentials")
            return redirect(url_for("index"))

        if role == "guest" and name:
            normalized_name = name.lower()
            phone = "".join(character for character in phone if character.isdigit())

            if len(phone) != 10:
                flash("Please enter a valid 10-digit mobile number.")
                return redirect(url_for("index"))

            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT owner_name
                FROM students
                WHERE owner_phone = %s

                UNION

                SELECT owner_name
                FROM bookings
                WHERE owner_phone = %s

                LIMIT 1
                """,
                (phone, phone),
            )
            existing_row = cursor.fetchone()
            conn.close()

            if existing_row:
                existing_name = (existing_row[0] or "").strip().lower()
                if existing_name != normalized_name:
                    flash("User already exists with this mobile number.")
                    return redirect(url_for("index"))

            session["role"] = "guest"
            session["user_name"] = normalized_name
            session["phone"] = phone

            conn = get_pg_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, current_login FROM user_activity WHERE LOWER(user_name) = LOWER(%s) AND role = %s",
                (normalized_name, "guest")
            )
            act_row = cursor.fetchone()
            if act_row:
                cursor.execute(
                    "UPDATE user_activity SET previous_login = %s, current_login = CURRENT_TIMESTAMP, phone = %s WHERE id = %s",
                    (act_row[1], phone, act_row[0])
                )
            else:
                cursor.execute(
                    "INSERT INTO user_activity (user_name, phone, role, current_login, previous_login) VALUES (%s, %s, %s, CURRENT_TIMESTAMP, NULL)",
                    (normalized_name, phone, "guest")
                )
            conn.commit()
            conn.close()
            return redirect(url_for("index"))

        flash("Please enter all required fields.")
        return redirect(url_for("index"))

    def register_page():
        return render_template("registration.html")

    def register_trainer():
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        name = (request.form.get("name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        email = (request.form.get("email") or "").strip()
        experience = (request.form.get("experience") or "").strip()
        qualification = (request.form.get("qualification") or "").strip()
        currently_working = (request.form.get("currently_working") or "").strip()
        residence_location = (request.form.get("residence_location") or "").strip()
        id_proof = (request.form.get("id_proof") or "").strip()
        whatsapp = (request.form.get("whatsapp") or "").strip()
        consent_accepted = request.form.get("consent_accepted") == "on"

        if not username or not password or not name or not phone or not email or not whatsapp:
            flash("Please fill in all mandatory fields (marked with *).")
            return redirect(url_for("register_page"))

        if not consent_accepted:
            flash("You must accept the Coach Terms & Agreement to register.")
            return redirect(url_for("register_page"))

        import random
        rating = round(random.uniform(4.5, 5.0), 1)

        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM trainers WHERE LOWER(username) = LOWER(%s)", (username.lower(),))
        if cursor.fetchone():
            conn.close()
            flash("Trainer username already exists.")
            return redirect(url_for("register_page"))

        cursor.execute(
            """
            INSERT INTO trainers (username, password, name, phone, email, experience, qualification, currently_working, residence_location, id_proof, consent_accepted, rating, is_approved, whatsapp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (username.lower(), password, name, phone, email, experience, qualification, currently_working, residence_location, id_proof, True, rating, False, whatsapp)
        )
        conn.commit()
        conn.close()
        flash("Trainer registered successfully! Your account is pending Super Admin approval before you can log in.")
        return redirect(url_for("index"))

    app.add_url_rule(
        "/login",
        endpoint="login",
        view_func=login,
        methods=["POST"],
    )
    app.add_url_rule(
        "/register",
        endpoint="register_page",
        view_func=register_page,
        methods=["GET"],
    )
    app.add_url_rule(
        "/register_trainer",
        endpoint="register_trainer",
        view_func=register_trainer,
        methods=["POST"],
    )
