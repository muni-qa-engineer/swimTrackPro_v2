import unittest
from unittest.mock import patch

from app import app


class GeneralRouteAccessTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()

    def login(self, role="guest"):
        with self.client.session_transaction() as flask_session:
            flask_session["user_name"] = "test user"
            flask_session["phone"] = "9999999999"
            flask_session["role"] = role

    def test_legacy_urls_and_endpoint_names_are_preserved(self):
        expected_routes = {
            "booking_page": ("/booking", {"GET"}),
            "my_bookings_page": ("/my-bookings", {"GET"}),
            "calendar_page": ("/calendar", {"GET"}),
            "payments_page": ("/payments", {"GET"}),
            "login": ("/login", {"POST"}),
            "add_swimmer": ("/add_swimmer", {"POST"}),
            "delete_swimmer": ("/delete_swimmer/<name>", {"POST"}),
            "book": ("/book", {"POST"}),
            "edit_booking": ("/edit/<booking_id>", {"GET"}),
            "update_booking": ("/update/<booking_id>", {"POST"}),
            "update_payment_status": (
                "/update_payment_status/<booking_id>",
                {"POST"},
            ),
            "delete_booking": ("/delete/<booking_id>", {"POST"}),
            "approve_delete": ("/approve_delete/<booking_id>", {"POST"}),
            "reject_delete": ("/reject_delete/<booking_id>", {"POST"}),
            "skip_session": (
                "/skip_session/<booking_id>/<session_date>",
                {"POST"},
            ),
            "undo_skip_session": (
                "/undo_skip_session/<booking_id>/<session_date>",
                {"POST"},
            ),
            "makeup_request_form": (
                "/makeup_request/<booking_id>",
                {"GET"},
            ),
            "submit_makeup_request": ("/submit_makeup_request", {"POST"}),
            "approve_makeup_request": (
                "/approve_makeup_request/<int:request_id>",
                {"POST"},
            ),
            "reject_makeup_request": (
                "/reject_makeup_request/<int:request_id>",
                {"POST"},
            ),
            "about_trainer": ("/about-trainer", {"GET"}),
            "help_page": ("/help", {"GET"}),
            "update_notice": ("/update_notice", {"POST"}),
            "logout": ("/logout", {"GET"}),
        }
        rules_by_endpoint = {
            rule.endpoint: rule
            for rule in app.url_map.iter_rules()
            if rule.endpoint in expected_routes
        }

        self.assertEqual(set(rules_by_endpoint), set(expected_routes))
        for endpoint, (path, methods) in expected_routes.items():
            with self.subTest(endpoint=endpoint):
                rule = rules_by_endpoint[endpoint]
                self.assertEqual(rule.rule, path)
                self.assertTrue(methods.issubset(rule.methods))

    def test_anonymous_user_is_redirected_from_authenticated_pages(self):
        for path in (
            "/my-bookings",
            "/calendar",
            "/payments",
            "/about-trainer",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers["Location"], "/")

    def test_trainer_cannot_add_swimmer(self):
        self.login("trainer")
        response = self.client.post("/add_swimmer", data={"name": "New Swimmer"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    def test_invalid_trainer_login_does_not_create_session(self):
        response = self.client.post(
            "/login",
            data={
                "role": "trainer",
                "name": "invalid",
                "password": "invalid",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/?role=trainer")
        with self.client.session_transaction() as flask_session:
            self.assertNotIn("user_name", flask_session)

    def test_guest_login_requires_ten_digit_phone(self):
        response = self.client.post(
            "/login",
            data={"role": "guest", "name": "Guest", "phone": "123"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as flask_session:
            self.assertNotIn("user_name", flask_session)

    def test_guest_can_open_general_authenticated_pages(self):
        self.login("guest")

        for path in ("/about-trainer", "/help"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_guest_cannot_update_notice(self):
        self.login("guest")
        response = self.client.post(
            "/update_notice",
            data={"notice_message": "Guest message"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    def test_trainer_can_update_notice(self):
        self.login("trainer")
        response = self.client.post(
            "/update_notice",
            data={"notice_message": "Training starts at 6 AM"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        
        from swimtrackpro.runtime import get_pg_connection
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT notice FROM trainers WHERE username = 'asdf'")
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "Training starts at 6 AM")

    def test_logout_clears_existing_session(self):
        self.login("guest")
        response = self.client.get("/logout")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as flask_session:
            self.assertNotIn("user_name", flask_session)
            self.assertNotIn("role", flask_session)

    def test_admin_login_success(self):
        from config import ADMIN_USERNAME, ADMIN_PASSWORD
        response = self.client.post(
            "/login",
            data={
                "role": "admin",
                "name": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as flask_session:
            self.assertEqual(flask_session.get("role"), "admin")
            self.assertEqual(flask_session.get("user_name"), "Super Admin")

    def test_admin_login_failure(self):
        from config import ADMIN_USERNAME
        response = self.client.post(
            "/login",
            data={
                "role": "admin",
                "name": ADMIN_USERNAME,
                "password": "wrongpassword",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/?role=admin")
        with self.client.session_transaction() as flask_session:
            self.assertNotIn("role", flask_session)

    def test_admin_dashboard_rendering(self):
        self.login("admin")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"super admin", response.data.lower())
        self.assertIn(b"coaches", response.data.lower())

    def test_admin_required_decorator_protection(self):
        self.login("guest")
        response = self.client.post("/admin/approve_trainer/test_coach")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    def test_terms_agreement_view(self):
        response = self.client.get("/terms-agreement")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SwimTrackPro Coach Agreement", response.data)

    def test_trainer_cannot_pause_booking(self):
        self.login("trainer")
        response = self.client.post("/booking/pause", data={"booking_id": "123", "reason": "Health Issues"})
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Coaches cannot pause bookings", response.data)

    def test_trainer_cannot_resume_booking(self):
        self.login("trainer")
        response = self.client.post("/booking/resume", data={"booking_id": "123"})
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Coaches cannot resume bookings", response.data)

    def test_unauthenticated_cannot_pause_booking(self):
        response = self.client.post("/booking/pause", data={"booking_id": "123", "reason": "Health Issues"})
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_cannot_approve_pause(self):
        response = self.client.post("/booking/approve_pause", data={"booking_id": "123"})
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_cannot_reject_pause(self):
        response = self.client.post("/booking/reject_pause", data={"booking_id": "123", "rejection_reason": "Test"})
        self.assertEqual(response.status_code, 302)

    def test_guest_cannot_approve_pause(self):
        self.login("guest")
        response = self.client.post("/booking/approve_pause", data={"booking_id": "123"})
        self.assertEqual(response.status_code, 403)

    def test_guest_cannot_reject_pause(self):
        self.login("guest")
        response = self.client.post("/booking/reject_pause", data={"booking_id": "123", "rejection_reason": "Test"})
        self.assertEqual(response.status_code, 403)

    def test_approve_pause_fails_for_missing_booking_id(self):
        self.login("trainer")
        response = self.client.post("/booking/approve_pause", data={})
        self.assertEqual(response.status_code, 400)

    def test_reject_pause_fails_without_rejection_reason(self):
        self.login("trainer")
        response = self.client.post("/booking/reject_pause", data={"booking_id": "123"})
        self.assertEqual(response.status_code, 400)

    def test_dashboard_guest_context_contains_all_future(self):
        with patch('swimtrackpro.routes.dashboard.get_guest_dashboard_data') as mock_get_data:
            mock_get_data.return_value = {
                'guest_all_future': [{'name': 'Test Swimmer', 'date': '21 Jul 2026', 'time': '06:00 AM', 'booking_id': '123', 'raw_date': '2026-07-21'}],
                'guest_upcoming_sessions': [],
                'next_session_name': '--',
                'active_package_name': 'Test Package',
                'total_sessions': 10,
                'completed_sessions': 5,
                'bookings': []
            }
            self.login("guest")
            response = self.client.get("/")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Skip Session', response.data)
            self.assertIn(b'Confirm Skip', response.data)

    def test_skip_session_unauthenticated_fails(self):
        response = self.client.post("/skip_session/123/2026-07-21")
        self.assertEqual(response.status_code, 302)

    def test_trainer_available_slots_retrieval_and_update(self):
        self.login("trainer")
        with self.client.session_transaction() as flask_session:
            flask_session["trainer_username"] = "asdf"

        import json
        test_slots = ["07:15 AM", "07:30 AM", "06:45 PM"]
        response = self.client.post(
            "/trainer/save_slots",
            data=json.dumps({"slots": test_slots}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertTrue(res_data["success"])

        from app import get_pg_connection
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT available_slots FROM trainers WHERE username = 'asdf'")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(json.loads(row[0]), test_slots)

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"value='[&#34;07:15 AM&#34;, &#34;07:30 AM&#34;, &#34;06:45 PM&#34;]'", response.data)

        response = self.client.get("/booking")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'data-slots=\'[&#34;07:15 AM&#34;, &#34;07:30 AM&#34;, &#34;06:45 PM&#34;]\'', response.data)

    def test_renew_booking_flow(self):
        self.login("guest")
        
        from app import get_pg_connection
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookings WHERE id = 'test-bk-123' OR student_name = 'Swimmer Name'")
        cursor.execute("""
            INSERT INTO bookings (
                id, booking_code, student_name, created_by, start_date, end_date,
                package, selected_days, location, persons, time, fee, status,
                payment_request, owner_name, owner_phone, email, trainer_username
            ) VALUES (
                'test-bk-123', 'STP123', 'Swimmer Name', 'test user', '2026-07-01', '2026-07-31',
                'Monthly', 'Monday,Wednesday', 'Gachibowli', 1, '06:00 AM', 9000, 'Paid',
                'Paid', 'test user', '9999999999', 'swimmer@example.com', 'asdf'
            )
        """)
        conn.commit()
        
        response = self.client.get("/my-bookings")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"openRenewModal('test-bk-123'", response.data)
        
        new_start_date = "2026-08-01"
        response = self.client.post(
            "/booking/renew",
            data={
                "booking_id": "test-bk-123",
                "start_date": new_start_date
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].startswith("/payment_options/"))
        
        cursor.execute("SELECT id, start_date, end_date, package, trainer_username FROM bookings WHERE student_name = 'Swimmer Name' AND id != 'test-bk-123'")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], new_start_date)
        self.assertEqual(row[3], "Monthly")
        self.assertEqual(row[4], "asdf")
        
        cursor.execute("DELETE FROM bookings WHERE id IN ('test-bk-123', %s)", (row[0],))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    unittest.main()
