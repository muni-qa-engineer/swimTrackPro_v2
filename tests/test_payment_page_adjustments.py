import unittest
from unittest.mock import patch, MagicMock
from flask import render_template
from app import app


class PaymentPageAdjustmentTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch("psycopg2.connect")
    def test_payment_page_trainer_rendering(self, mock_connect):
        """
        Verify Payment page for trainer has:
        1. Scrollable Payment Records container (.payment-records-scroll) for displaying ~15 records with scroll
        2. Right-aligned download button with PDF, PNG, JPEG, CSV options
        3. Serial number (#) column header in table
        4. Payment Calculations section under My Payment Settings with filter pills, search, and total sum
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_conn

        mock_bookings = [
            {
                "id": str(i),
                "owner": f"Parent_{i}",
                "student": f"Swimmer_{i}",
                "package": "Monthly",
                "status": "Paid" if i % 2 == 0 else "Not Paid",
                "fee": 5000,
            }
            for i in range(1, 20)
        ]

        context = {
            "role": "trainer",
            "user_name": "coach_john",
            "bookings": mock_bookings,
            "total_pending_amount": 45000,
            "account_holder_name": "Coach John",
            "trainer_phone": "9999999999",
            "upi_id": "coach@upi",
            "trainer_payment_settings": {
                "upi_id": "coach@upi",
                "account_holder_name": "Coach John",
                "qr_code": ""
            }
        }

        with app.test_request_context():
            from flask import session
            session["role"] = "trainer"
            session["user_name"] = "coach_john"
            html = render_template("payments.html", **context)

        # 1. Height limitation / scrollable table container for ~15 records
        self.assertIn("payment-records-scroll", html, "Payment records table must have scrollable wrapper class")
        self.assertIn("overflow-y: auto", html, "CSS must provide smooth vertical scroll for records")

        # 2. Download button beside Payment Records
        self.assertIn("Download Payment Records", html, "Download button must exist in Payment Records")
        self.assertIn("downloadPaymentRecords('pdf')", html, "Must offer PDF download option")
        self.assertIn("downloadPaymentRecords('png')", html, "Must offer PNG download option")
        self.assertIn("downloadPaymentRecordsCSV()", html, "Must offer CSV download option")

        # 3. Serial Number column in table
        self.assertIn("<th style=\"width: 50px; text-align: center;\">#</th>", html, "Table header must include serial number column #")

        # 4. Payment Calculations section under My Payment Settings
        self.assertIn("My Payment Settings", html, "Trainer view must have My Payment Settings")
        self.assertIn("Payment Calculations", html, "Must have Payment Calculations section")
        self.assertIn("paymentCalculationsCard", html, "Must have paymentCalculationsCard panel")
        self.assertIn("calcCountAll", html, "Must have All filter counter")
        self.assertIn("calcCountReceived", html, "Must have Received filter counter")
        self.assertIn("calcCountPending", html, "Must have Pending filter counter")
        self.assertIn("memberCalculationSearch", html, "Must have member search filter input")
        self.assertIn("calcTotalReceived", html, "Must have total received element")
        self.assertIn("calcTotalPending", html, "Must have total pending element")
        self.assertIn("calcGrandTotal", html, "Must have grand total sum element")

    @patch("psycopg2.connect")
    def test_payment_page_guest_rendering(self, mock_connect):
        """
        Verify Payment page for guest also renders calculations and payment records correctly.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_conn

        context = {
            "role": "guest",
            "user_name": "parent_user",
            "bookings": [
                {
                    "id": "101",
                    "owner": "parent_user",
                    "student": "Aryan",
                    "package": "Monthly",
                    "status": "Paid",
                    "fee": 5000,
                }
            ],
            "total_pending_amount": 0,
            "account_holder_name": "Coach",
            "trainer_phone": "9999999999",
            "upi_id": "coach@upi",
            "trainer_payment_settings": {
                "upi_id": "coach@upi",
                "account_holder_name": "Coach",
                "qr_code": ""
            }
        }

        with app.test_request_context():
            from flask import session
            session["role"] = "guest"
            session["user_name"] = "parent_user"
            html = render_template("payments.html", **context)

        self.assertIn("Payment Calculations", html)
        self.assertIn("payment-records-scroll", html)
        self.assertIn("downloadPaymentRecords", html)


if __name__ == "__main__":
    unittest.main()
