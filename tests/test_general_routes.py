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
            "/booking",
            "/my-bookings",
            "/calendar",
            "/payments",
            "/about-trainer",
            "/help",
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
        self.assertEqual(response.headers["Location"], "/")
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

    @patch("swimtrackpro.routes.general.set_setting")
    def test_trainer_can_update_notice(self, set_setting_mock):
        self.login("trainer")
        response = self.client.post(
            "/update_notice",
            data={"notice_message": "Training starts at 6 AM"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        set_setting_mock.assert_called_once_with(
            "notice_message",
            "Training starts at 6 AM",
        )

    def test_logout_clears_existing_session(self):
        self.login("guest")
        response = self.client.get("/logout")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        with self.client.session_transaction() as flask_session:
            self.assertNotIn("user_name", flask_session)
            self.assertNotIn("role", flask_session)

    def test_anonymous_index_still_renders_login(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"login", response.data.lower())


if __name__ == "__main__":
    unittest.main()
