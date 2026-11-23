import unittest
from unittest.mock import patch, MagicMock
from flask import render_template
from app import app
from services.pricing_service import get_pricing_config_dict


class AdminCoachProofVerificationTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()

    @patch("swimtrackpro.routes.general.get_pg_connection")
    def test_verify_trainer_id_proof_accepted(self, mock_get_conn):
        """Verify admin can accept ID proof and update status to 'Verified'."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with self.client.session_transaction() as sess:
            sess["user_name"] = "admin"
            sess["role"] = "admin"

        response = self.client.post(
            "/admin/verify_trainer_proof/haribabu1762",
            data={"proof_type": "id_proof", "status": "Accepted"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "Verified")
        self.assertEqual(data["proof_type"], "id_proof")

        # Verify UPDATE query executed
        calls = [str(call[0]) for call in mock_cursor.execute.call_args_list]
        self.assertTrue(any("UPDATE trainers SET id_proof_status = %s" in c for c in calls))

    @patch("swimtrackpro.routes.general.get_pg_connection")
    def test_verify_trainer_qualification_declined(self, mock_get_conn):
        """Verify admin can decline qualification and update status to 'Declined'."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with self.client.session_transaction() as sess:
            sess["user_name"] = "admin"
            sess["role"] = "admin"

        response = self.client.post(
            "/admin/verify_trainer_proof/haribabu1762",
            data={"proof_type": "qualification", "status": "Decline"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "Declined")
        self.assertEqual(data["proof_type"], "qualification")

        calls = [str(call[0]) for call in mock_cursor.execute.call_args_list]
        self.assertTrue(any("UPDATE trainers SET qualification_status = %s" in c for c in calls))

    def test_verify_trainer_proof_unauthorized(self):
        """Verify non-admin cannot verify trainer proof."""
        with self.client.session_transaction() as sess:
            sess["user_name"] = "guest1"
            sess["role"] = "guest"

        response = self.client.post(
            "/admin/verify_trainer_proof/haribabu1762",
            data={"proof_type": "id_proof", "status": "Accepted"},
        )
        # Should redirect or reject
        self.assertIn(response.status_code, [302, 403])

    @patch("app.get_pg_connection")
    def test_admin_dashboard_renders_proof_badges_and_modals(self, mock_get_conn):
        """Verify admin dashboard template renders Verified/Declined badges and modals outside table."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_get_conn.return_value = mock_conn

        with app.test_request_context():
            from flask import session
            session["user_name"] = "admin"
            session["role"] = "admin"

            trainers_sample = [
                {
                    "username": "haribabu1762",
                    "name": "Haribabu Bandi",
                    "phone": "9398886838",
                    "email": "haribabuswim@gmail.com",
                    "experience": "5 years",
                    "qualification": "NIS Certified",
                    "currently_working": "Independent",
                    "residence_location": "Bengaluru",
                    "rating": 4.7,
                    "is_approved": False,
                    "is_blocked": False,
                    "photos": [],
                    "id_proof": "adhaar",
                    "id_proof_file": "haribabu_id.jpg",
                    "qualification_file": "haribabu_cert.jpg",
                    "id_proof_status": "Verified",
                    "qualification_status": "Declined",
                }
            ]

            admin_context = {
                "user_name": "admin",
                "role": "admin",
                "pricing_config": get_pricing_config_dict(),
                "trainers": trainers_sample,
                "bookings": [],
                "students": [],
                "today_sessions": [],
                "activities": [],
                "chart_data": {},
                "paused_packages_count": 0,
                "auto_resume_today_count": 0,
                "paused_this_week_count": 0,
                "resume_pending_count": 0,
                "audit_logs": [],
                "packages": [],
                "carousel_images": [],
                "promo_banner": {},
            }

            html = render_template("admin_dashboard.html", **admin_context)

        # Badges beside proof buttons
        self.assertIn('badge-id-proof-haribabu1762', html)
        self.assertIn('badge-qualification-haribabu1762', html)
        self.assertIn('Verified', html)
        self.assertIn('Declined', html)

        # Modals have Accepted and Decline buttons
        self.assertIn('idProofModal-1', html)
        self.assertIn('qualModal-1', html)
        self.assertIn('Accepted', html)
        self.assertIn('Decline', html)
        self.assertIn('updateTrainerProofStatus', html)


if __name__ == "__main__":
    unittest.main()
