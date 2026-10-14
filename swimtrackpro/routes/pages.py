"""Authenticated booking, calendar, and payment page routes."""

from flask import flash, redirect, render_template, session, url_for, request

from services.email_service import (
    send_package_completion_email,
    send_payment_reminder_email,
)
from services.settings_service import get_setting
from services.dashboard_service import get_all_packages
from services.pricing_service import get_pricing_config_dict
from datetime import datetime
import json
import re


def sort_bookings_latest_active_first(bookings):
    """
    Sort bookings such that:
    1. Active bookings appear first (latest active start_date first).
    2. Booked (upcoming / not yet started) bookings follow (latest start_date first).
    3. Completed / Expired bookings appear last (latest start_date first).
    """
    def _sort_key(b):
        is_completed = bool(b.get('is_completed', False))
        completed_classes = int(b.get('completed_classes', 0) or 0)
        remaining_classes = int(b.get('remaining_classes', 0) or 0)
        status_str = str(b.get('status', '')).strip().lower()

        # Status rank:
        # 0 = Active (has classes remaining, not completed, and classes attended or active status)
        # 1 = Booked (upcoming, not yet started, 0 classes attended)
        # 2 = Completed / Expired
        if not is_completed and (remaining_classes > 0 or b.get('package') == 'Single') and (completed_classes > 0 or status_str in ('active', 'confirmed', 'paid')):
            status_rank = 0
        elif not is_completed:
            status_rank = 1
        else:
            status_rank = 2

        start_date_str = str(b.get('start_date') or '1970-01-01')
        try:
            date_obj = datetime.strptime(start_date_str[:10], '%Y-%m-%d')
            timestamp = date_obj.timestamp()
        except Exception:
            timestamp = 0.0

        try:
            b_id = int(b.get('id', 0) or 0)
        except Exception:
            b_id = 0

        # Status rank ascending (0 < 1 < 2), timestamp descending (-timestamp), id descending (-b_id)
        return (status_rank, -timestamp, -b_id)

    return sorted(bookings, key=_sort_key)


def _bookings_for_session(data):
    current_user = (session.get("user_name") or "").strip().lower()
    current_phone = (session.get("phone") or "").strip()
    current_role = session.get("role", "guest")

    if current_role == "trainer":
        trainer_user = (session.get("trainer_username") or "asdf").strip().lower()
        trainer_bookings = [
            booking
            for booking in data.get("bookings", [])
            if (booking.get("trainer_username") or "asdf").strip().lower() == trainer_user
        ]
        return sort_bookings_latest_active_first(trainer_bookings)

    def clean_phone(p):
        if not p:
            return ""
        return re.sub(r"\D", "", str(p))

    user_clean_phone = clean_phone(current_phone)

    result = []
    for booking in data.get("bookings", []):
        b_owner_name = (booking.get("owner_name") or "").strip().lower()
        b_created_by = (booking.get("created_by") or "").strip().lower()
        b_student = (booking.get("student") or "").strip().lower()
        b_owner_phone = clean_phone(booking.get("owner_phone"))

        name_match = (
            (bool(current_user) and b_owner_name == current_user) or
            (bool(current_user) and b_created_by == current_user) or
            (bool(current_user) and b_student == current_user)
        )
        phone_match = (
            bool(user_clean_phone) and bool(b_owner_phone) and (
                user_clean_phone == b_owner_phone or
                user_clean_phone.endswith(b_owner_phone) or
                b_owner_phone.endswith(user_clean_phone)
            )
        )

        if name_match or phone_match:
            if booking.get('payment_request') == 'unconfirmed' or booking.get('status') == 'unconfirmed':
                continue
            result.append(booking)

    return sort_bookings_latest_active_first(result)


def register_page_routes(app, *, get_pg_connection, load_data):
    def booking_page():
        check_and_perform_auto_resumes()
        data = load_data()
        current_user = session.get("user_name")
        current_phone = session.get("phone")
        current_role = session.get("role", "guest")

        if current_role == "trainer":
            user_students = data.get("students", [])
        else:
            user_students = [
                swimmer
                for swimmer in data.get("students", [])
                if isinstance(swimmer, dict)
                and (swimmer.get("owner_name") or "").strip().lower()
                == current_user
                and swimmer.get("owner_phone") == current_phone
            ]

        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT location
            FROM bookings
            WHERE location IS NOT NULL
              AND TRIM(location) <> ''
            ORDER BY location
            """
        )
        location_suggestions = [row[0] for row in cursor.fetchall() if row[0]]

        cursor.execute("""
            SELECT username, name, experience, qualification, currently_working, residence_location, rating, phone, email, whatsapp, available_slots
            FROM trainers 
            WHERE is_approved = TRUE
            ORDER BY rating DESC, name
        """)
        trainers = [
            {
                "username": row[0],
                "name": row[1],
                "experience": row[2] or "N/A",
                "qualification": row[3] or "N/A",
                "currently_working": row[4] or "N/A",
                "residence_location": row[5] or "N/A",
                "rating": float(row[6]) if row[6] is not None else 5.0,
                "phone": row[7] or "N/A",
                "email": row[8] or "N/A",
                "whatsapp": row[9] or "N/A",
                "available_slots": row[10] or "[]"
            }
            for row in cursor.fetchall()
        ]
        conn.close()

        renew_booking = None
        renew_from_id = request.args.get('renew_from')
        renew_start_date = request.args.get('start_date')
        if renew_from_id:
            booking_obj = next((b for b in data.get('bookings', []) if str(b.get('id')) == str(renew_from_id)), None)
            if booking_obj:
                renew_booking = {
                    'package': booking_obj.get('package'),
                    'start_date': renew_start_date or booking_obj.get('start_date'),
                    'end_date': booking_obj.get('end_date'),
                    'time': booking_obj.get('time'),
                    'selected_days': booking_obj.get('selected_days', ''),
                    'location': booking_obj.get('location'),
                    'student': booking_obj.get('student'),
                    'email': booking_obj.get('email'),
                    'persons': booking_obj.get('persons', 1),
                    'trainer_username': booking_obj.get('trainer_username'),
                    'fee': booking_obj.get('fee')
                }

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
            packages_json=json.dumps(packages),
            pricing_config=get_pricing_config_dict()
        )

    @login_required
    def my_bookings_page():
        check_and_perform_auto_resumes()
        data = load_data()
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, name FROM trainers")
        trainer_map = {row[0].lower().strip(): row[1] for row in cursor.fetchall() if row[0]}
        
        guest_reviews = {}
        if session.get("role") == "guest" and session.get("phone"):
            cursor.execute(
                "SELECT trainer_username, rating, comment FROM coach_feedback WHERE guest_phone = %s",
                (session.get("phone"),)
            )
            for r in cursor.fetchall():
                guest_reviews[r[0]] = {
                    "rating": r[1],
                    "comment": r[2] or ""
                }
        conn.close()

        return render_template(
            "my_bookings.html",
            bookings=_bookings_for_session(data),
            role=session.get("role", "guest"),
            user_name=session.get("user_name"),
            account_holder_name=get_setting("account_holder_name", ""),
            trainer_phone=get_setting("trainer_phone", ""),
            upi_id=get_setting("upi_id", ""),
            trainer_map=trainer_map,
            guest_reviews=guest_reviews,
        )

    @login_required
    def calendar_page():
        data = load_data()
        return render_template(
            "calendar.html",
            bookings=_bookings_for_session(data),
            role=session.get("role", "guest"),
            user_name=session.get("user_name"),
        )

    @login_required
    def payments_page():
        data = load_data()
        current_role = session.get("role", "guest")
        user_bookings = _bookings_for_session(data)

        if current_role == "trainer":
            reminder_conn = get_pg_connection()
            reminder_cursor = reminder_conn.cursor()

            for booking in user_bookings:
                try:
                    payment_status = str(booking.get("status", "")).strip().lower()
                    remaining_classes = booking.get("remaining_classes", 0)
                    is_completed = booking.get("is_completed", False)

                    if payment_status == "paid" and remaining_classes == 0 and is_completed:
                        try:
                            send_package_completion_email(booking)
                        except Exception:
                            pass
                        continue

                    if (
                        remaining_classes <= 3
                        and payment_status != "paid"
                        and not booking.get("payment_reminder_sent", False)
                    ):
                        send_payment_reminder_email(booking)
                        reminder_cursor.execute(
                            """
                            UPDATE bookings
                            SET payment_reminder_sent = TRUE,
                                payment_reminder_sent_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                            """,
                            (booking.get("id"),),
                        )
                except Exception as exc:
                    print("PAYMENT REMINDER ERROR:", exc)

            reminder_conn.commit()
            reminder_conn.close()

        total_pending_amount = sum(
            int(booking.get("fee", 0) or 0)
            for booking in user_bookings
            if str(booking.get("status", "")).strip().lower() != "paid"
        )
        
        trainer_payment_settings = {}
        if current_role == "trainer":
            try:
                conn = get_pg_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT upi_id, account_holder_name, qr_code FROM trainers WHERE LOWER(username) = LOWER(%s)", 
                    (session.get("user_name"),)
                )
                row = cursor.fetchone()
                if row:
                    trainer_payment_settings = {
                        "upi_id": row[0] or "",
                        "account_holder_name": row[1] or "",
                        "qr_code": row[2] or ""
                    }
                conn.close()
            except Exception as e:
                print("Error fetching trainer payment settings:", e)
        elif current_role == "guest" and user_bookings:
            # Find the trainer from the most recent unpaid booking, or fallback to the first booking
            unpaid_bookings = [b for b in user_bookings if str(b.get("status", "")).strip().lower() != "paid"]
            target_booking = unpaid_bookings[0] if unpaid_bookings else user_bookings[0]
            trainer_username = target_booking.get("trainer_username")
            
            if trainer_username:
                try:
                    conn = get_pg_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT upi_id, account_holder_name, qr_code FROM trainers WHERE LOWER(username) = LOWER(%s)", 
                        (trainer_username,)
                    )
                    row = cursor.fetchone()
                    if row:
                        trainer_payment_settings = {
                            "upi_id": row[0] or "",
                            "account_holder_name": row[1] or "",
                            "qr_code": row[2] or ""
                        }
                    conn.close()
                except Exception as e:
                    print("Error fetching trainer payment settings for guest:", e)

        return render_template(
            "payments.html",
            bookings=user_bookings,
            role=current_role,
            user_name=session.get("user_name"),
            total_pending_amount=total_pending_amount,
            account_holder_name=get_setting("account_holder_name", ""),
            trainer_phone=get_setting("trainer_phone", ""),
            upi_id=get_setting("upi_id", ""),
            trainer_payment_settings=trainer_payment_settings,
        )

    def payment_options_page(booking_id):
        current_role = session.get("role", "guest")
        data = load_data()
        booking = next((b for b in data.get("bookings", []) if str(b["id"]) == str(booking_id)), None)
        
        if not booking:
            flash("Booking not found.")
            return redirect(url_for("index"))
            
        return render_template(
            "payment_options.html",
            role=current_role,
            user_name=session.get("user_name") or session.get("pending_guest_name"),
            booking=booking,
            upi_id=get_setting("upi_id", ""),
            account_holder_name=get_setting("account_holder_name", "")
        )

    app.add_url_rule("/payment_options/<booking_id>", endpoint="payment_options_page", view_func=payment_options_page)
    app.add_url_rule("/booking", endpoint="booking_page", view_func=booking_page)
    app.add_url_rule(
        "/my-bookings",
        endpoint="my_bookings_page",
        view_func=my_bookings_page,
    )
    app.add_url_rule("/calendar", endpoint="calendar_page", view_func=calendar_page)
    app.add_url_rule("/payments", endpoint="payments_page", view_func=payments_page)
