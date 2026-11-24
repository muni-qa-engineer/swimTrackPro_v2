import unittest
from unittest.mock import patch, MagicMock
from app import app
from services.email_service import (
    send_coach_registration_email,
    send_coach_registration_admin_alert,
)


class CoachRegistrationEmailTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch("services.email_service.send_email")
    def test_send_coach_registration_email_success(self, mock_send_email):
        mock_send_email.return_value = True

        coach_info = {
            "name": "Michael Phelps",
            "username": "mphelps",
            "phone": "9876543210",
            "email": "mphelps@swimtrackpro.test",
            "experience": "10 years",
            "qualification": "Olympic Gold Medalist / NIS Certified",
            "currently_working": "Elite Aquatic Academy",
            "residence_location": "Hyderabad",
            "id_proof": "Aadhaar Card",
            "id_number": "STPC0005",
        }

        result = send_coach_registration_email(coach_info)
        self.assertTrue(result)
        mock_send_email.assert_called_once()

        kwargs = mock_send_email.call_args.kwargs
        self.assertEqual(kwargs.get("to_email"), "mphelps@swimtrackpro.test")
        self.assertIn("STPC0005", kwargs.get("subject", ""))
        self.assertIn("Coach Application Under Progress", kwargs.get("subject", ""))

        html = kwargs.get("html_content", "")
        self.assertIn("Michael Phelps", html)
        self.assertIn("mphelps", html)
        self.assertIn("STPC0005", html)
        self.assertIn("Your application is currently under progress", html)
        self.assertIn("notified once an Admin / recruiter accepts", html)
        self.assertIn("Olympic Gold Medalist / NIS Certified", html)
        self.assertIn("Hyderabad", html)

    @patch("services.email_service.send_email")
    def test_send_coach_registration_email_skips_when_no_email(self, mock_send_email):
        coach_info = {
            "name": "No Email Coach",
            "username": "noemail",
            "email": "",
            "id_number": "STPC0006",
        }
        result = send_coach_registration_email(coach_info)
        self.assertFalse(result)
        mock_send_email.assert_not_called()

    @patch("services.email_service.send_email")
    def test_send_coach_registration_admin_alert_success(self, mock_send_email):
        mock_send_email.return_value = True

        coach_info = {
            "name": "Katie Ledecky",
            "username": "kledecky",
            "phone": "9123456789",
            "email": "kledecky@swimtrackpro.test",
            "experience": "8 years",
            "qualification": "FINA Certified Coach",
            "currently_working": "Swim Club",
            "residence_location": "Bengaluru",
            "id_proof": "Passport",
            "id_number": "STPC0007",
        }

        result = send_coach_registration_admin_alert(coach_info)
        self.assertTrue(result)
        mock_send_email.assert_called_once()

        kwargs = mock_send_email.call_args.kwargs
        # Admin alert defaults to recipient configured in email_service or ADMIN_ALERT_EMAIL
        subject = kwargs.get("subject", "")
        self.assertIn("New Coach Register - Yet to pending with verification", subject)
        self.assertIn("Katie Ledecky", subject)
        self.assertIn("STPC0007", subject)

        html = kwargs.get("html_content", "")
        self.assertIn("New coach register - Yet to pending with verification", html)
        self.assertIn("https://swimtrackpro.onrender.com/?section=coaches", html)
        self.assertIn("Katie Ledecky", html)
        self.assertIn("kledecky@swimtrackpro.test", html)
        self.assertIn("9123456789", html)
        self.assertIn("FINA Certified Coach", html)
        self.assertIn("Bengaluru", html)

    @patch("services.email_service.send_coach_registration_admin_alert")
    @patch("services.email_service.send_coach_registration_email")
    @patch("psycopg2.connect")
    def test_register_coach_route_triggers_emails(
        self, mock_connect, mock_coach_email, mock_admin_alert
    ):
        import io
        import os
        import shutil
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # 1. Check existing username -> None
        # 2. SELECT MAX ID -> (3,)
        mock_cursor.fetchone.side_effect = [
            None,      # username exists check
            (3,),      # max STPC number -> will become STPC0004
        ]

        try:
            client = app.test_client()
            response = client.post(
                "/register_trainer",
                data={
                    "username": "newcoach",
                    "password": "Password123!",
                    "name": "New Coach",
                    "phone": "9876500000",
                    "email": "newcoach@example.com",
                    "experience": "5 years",
                    "qualification": "Level 2 Certified",
                    "currently_working": "Self-employed",
                    "residence_location": "Mumbai",
                    "id_proof": "Aadhaar",
                    "terms_agreed": "on",
                    "id_proof_file": (io.BytesIO(b"dummy id bytes"), "test_id.png"),
                    "qualification_file": (io.BytesIO(b"dummy qual bytes"), "test_qual.png"),
                },
                content_type="multipart/form-data",
                follow_redirects=False,
            )

            self.assertEqual(response.status_code, 302)
            mock_coach_email.assert_called_once()
            mock_admin_alert.assert_called_once()

            passed_info = mock_coach_email.call_args[0][0]
            self.assertEqual(passed_info["name"], "New Coach")
            self.assertEqual(passed_info["username"], "newcoach")
            self.assertEqual(passed_info["email"], "newcoach@example.com")
            self.assertEqual(passed_info["id_number"], "STPC0004")
        finally:
            for path in [
                os.path.join("static", "uploads", "id_proofs"),
                os.path.join("static", "uploads", "qualifications"),
            ]:
                if os.path.exists(path):
                    shutil.rmtree(path, ignore_errors=True)
