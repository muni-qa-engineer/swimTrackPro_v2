import unittest
from unittest.mock import patch, MagicMock
from app import app
from swimtrackpro.routes.pages import _bookings_for_session
from services.dashboard_service import get_guest_dashboard_data


class DeleteAccountTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()

    def test_unauthenticated_request_is_blocked(self):
        response = self.client.post("/account/delete", headers={"X-Requested-With": "XMLHttpRequest"})
        # login_required decorator redirects or returns unauth
        self.assertIn(response.status_code, (302, 401))

    def test_admin_cannot_delete_account(self):
        with self.client.session_transaction() as sess:
            sess["user_name"] = "admin"
            sess["role"] = "admin"
        response = self.client.post("/account/delete", headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertFalse(data.get("success"))

    def test_trainer_cannot_delete_account(self):
        with self.client.session_transaction() as sess:
            sess["user_name"] = "trainer1"
            sess["role"] = "trainer"
            sess["trainer_username"] = "trainer1"
        response = self.client.post("/account/delete", headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertFalse(data.get("success"))

    @patch("swimtrackpro.routes.general.load_data")
    def test_active_bookings_guard_blocks_deletion(self, mock_load):
        # Swimmer has an ongoing active package with 5 sessions remaining
        mock_load.return_value = {
            "bookings": [
                {
                    "id": "b101",
                    "student": "Swimmer One",
                    "student_name": "Swimmer One",
                    "owner_name": "test_guest",
                    "owner_phone": "9133851444",
                    "package": "Monthly 12 Classes",
                    "status": "paid",
                    "payment_request": "approved",
                    "is_completed": False,
                    "remaining_classes": 5,
                    "completed_classes": 7
                }
            ]
        }
        with self.client.session_transaction() as sess:
            sess["user_name"] = "test_guest"
            sess["phone"] = "9133851444"
            sess["role"] = "guest"
            sess["id_number"] = "STPS0042"

        response = self.client.post("/account/delete", headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("5 sessions remaining", data.get("message"))
        self.assertIn("ongoing swimming classes", data.get("message").lower())

    @patch("swimtrackpro.routes.general.get_pg_connection")
    @patch("swimtrackpro.routes.general.load_data")
    def test_successful_deletion_when_no_active_bookings(self, mock_load, mock_get_conn):
        # Swimmer has only a completed package
        mock_load.return_value = {
            "bookings": [
                {
                    "id": "b102",
                    "student": "Swimmer One",
                    "student_name": "Swimmer One",
                    "owner_name": "test_guest",
                    "owner_phone": "9133851444",
                    "package": "Monthly 12 Classes",
                    "status": "paid",
                    "payment_request": "approved",
                    "is_completed": True,
                    "remaining_classes": 0,
                    "completed_classes": 12
                }
            ]
        }
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # No profile picture file
        mock_get_conn.return_value = mock_conn

        with self.client.session_transaction() as sess:
            sess["user_name"] = "test_guest"
            sess["phone"] = "9133851444"
            sess["role"] = "guest"
            sess["id_number"] = "STPS0042"

        response = self.client.post("/account/delete", headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))

        # Verify DB operations executed:
        # Check that executed SQL statements archive bookings and delete user_activity
        calls = [str(call[0][0]) for call in mock_cursor.execute.call_args_list]
        self.assertTrue(any("UPDATE bookings" in sql and "ARCHIVED" in sql for sql in calls), "Bookings not archived")
        self.assertTrue(any("DELETE FROM user_activity" in sql for sql in calls), "user_activity not deleted")
        self.assertTrue(any("DELETE FROM students" in sql for sql in calls), "students not deleted")
        self.assertTrue(any("DELETE FROM guest_favorites" in sql for sql in calls), "guest_favorites not deleted")
        self.assertTrue(any("UPDATE coach_feedback" in sql and "ARCHIVED" in sql for sql in calls), "coach_feedback not anonymized")
        mock_conn.commit.assert_called()

    @patch("swimtrackpro.runtime._get_pg_connection")
    def test_archived_bookings_are_hidden_from_guest_and_shown_to_coach(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_get_conn.return_value = mock_conn

        # Setup sample data with an archived booking
        sample_data = {
            "bookings": [
                {
                    "id": "b201",
                    "student": "Swimmer Real Name",
                    "student_name": "Swimmer Real Name",
                    "owner_name": "re_registered_user",
                    "created_by": "re_registered_user",
                    "owner_phone": "ARCHIVED",
                    "trainer_username": "coach_john",
                    "fee": 5000,
                    "status": "paid",
                    "payment_request": "approved",
                    "is_completed": True,
                    "remaining_classes": 0
                }
            ],
            "students": []
        }

        # 1. Guest Session: even with matching name 're_registered_user', archived booking is ignored
        with self.client.session_transaction() as sess:
            sess["user_name"] = "re_registered_user"
            sess["phone"] = "9133851444"
            sess["role"] = "guest"

        with app.test_request_context():
            from flask import session as flask_sess
            flask_sess["user_name"] = "re_registered_user"
            flask_sess["phone"] = "9133851444"
            flask_sess["role"] = "guest"

            guest_bookings = _bookings_for_session(sample_data)
            self.assertEqual(len(guest_bookings), 0, "Guest should NOT see archived booking")

            guest_dash = get_guest_dashboard_data("re_registered_user", "9133851444", sample_data)
            self.assertEqual(len(guest_dash.get("bookings", [])), 0, "Guest dashboard should have 0 bookings")

        # 2. Coach Session: coach sees the completed booking with the real student name intact
        with app.test_request_context():
            from flask import session as flask_sess
            flask_sess["user_name"] = "coach_john"
            flask_sess["trainer_username"] = "coach_john"
            flask_sess["role"] = "trainer"

            coach_bookings = _bookings_for_session(sample_data)
            self.assertEqual(len(coach_bookings), 1, "Coach MUST see the booking")
            self.assertEqual(coach_bookings[0]["student"], "Swimmer Real Name")
            self.assertEqual(coach_bookings[0]["fee"], 5000)

    @patch("swimtrackpro.routes.dashboard.get_pg_connection")
    @patch("swimtrackpro.routes.dashboard.load_data")
    @patch("swimtrackpro.routes.dashboard.get_all_packages")
    def test_deletion_flash_message_renders_with_5s_auto_dismiss(self, mock_pkgs, mock_load, mock_get_conn):
        mock_pkgs.return_value = []
        mock_load.return_value = {"bookings": []}
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_get_conn.return_value = mock_conn

        # Set flashed message simulating after account deletion redirect
        with self.client.session_transaction() as sess:
            sess["_flashes"] = [("success", "Your account and personal data have been permanently deleted.")]

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Assert flash message is present
        self.assertIn("Your account and personal data have been permanently deleted.", html)
        self.assertIn("flash-messages-container", html)
        self.assertIn("auto-dismiss-alert", html)

        # Assert 5-second auto-dismiss timer and removal logic are present
        self.assertIn("startFlashAutoDismiss", html)
        self.assertIn("5000", html)
        self.assertIn("opacity = '0'", html)
        self.assertIn("translateY(-10px)", html)
        self.assertIn("alertElem.remove()", html)
        self.assertIn("container.remove()", html)

        # Assert login modal flash message has 5-second auto-dismiss and modal hide logic
        self.assertIn("loginModalFlashMessage", html)
        self.assertIn("dismissLoginModalFlash", html)
        self.assertIn("msgElem.remove()", html)


if __name__ == "__main__":
    unittest.main()
