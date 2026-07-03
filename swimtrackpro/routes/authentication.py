"""Authentication routes with legacy URL and endpoint compatibility."""

from flask import flash, redirect, request, session, url_for


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
            if (
                admin_username
                and admin_password
                and name.lower() == admin_username.lower()
                and password == admin_password
            ):
                session["user_name"] = "Trainer"
                session["role"] = "trainer"

                conn = get_pg_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO user_activity (user_name, phone, role)
                    VALUES (%s, %s, %s)
                    """,
                    ("Trainer", "", "trainer"),
                )
                conn.commit()
                conn.close()
                return redirect(url_for("index"))

            flash("Invalid trainer credentials")
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
                """
                INSERT INTO user_activity (user_name, phone, role)
                VALUES (%s, %s, %s)
                """,
                (normalized_name, phone, "guest"),
            )
            conn.commit()
            conn.close()
            return redirect(url_for("index"))

        flash("Please enter all required fields.")
        return redirect(url_for("index"))

    app.add_url_rule(
        "/login",
        endpoint="login",
        view_func=login,
        methods=["POST"],
    )
