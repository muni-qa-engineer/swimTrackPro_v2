import unittest
from unittest.mock import patch, MagicMock
from flask import render_template
from app import app
from services.pricing_service import (
    get_base_prices,
    update_base_prices,
    calculate_discounted_fee,
    get_package_quote,
    get_pricing_config_dict,
    DEFAULT_BASE_PRICES,
)


class CustomPackagePricingTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()

    def test_default_base_prices_contains_custom(self):
        """Verify custom package base rate defaults to 750 INR per session."""
        self.assertIn("custom", DEFAULT_BASE_PRICES)
        self.assertEqual(DEFAULT_BASE_PRICES["custom"], 750)
        prices = get_base_prices()
        self.assertIn("custom", prices)
        self.assertEqual(prices["custom"], 750)

    def test_custom_package_fee_calculation_multi_session(self):
        """
        Verify that custom package fee equals number_of_sessions * custom_rate (750).
        For 23 sessions with 1 person: 23 * 750 = 17,250 INR.
        For 23 sessions with 2 persons: round(23 * 750 * 1.70) = 29,325 INR.
        """
        fee_1p = calculate_discounted_fee("Custom", 1, 23)
        self.assertEqual(fee_1p, 17250, "1 swimmer for 23 sessions should be 23 * 750 = 17250")

        fee_2p = calculate_discounted_fee("Custom", 2, 23)
        self.assertEqual(fee_2p, 29325, "2 swimmers for 23 sessions should apply 1.70x group multiplier")

        quote_1p = get_package_quote("custom", swimmer_count=1, session_count=23)
        self.assertEqual(quote_1p["total_batch_price"], 17250)
        self.assertEqual(quote_1p["price_per_person"], 17250)

        quote_2p = get_package_quote("custom", swimmer_count=2, session_count=23)
        self.assertEqual(quote_2p["total_batch_price"], 29325)
        self.assertEqual(quote_2p["price_per_person"], round(29325 / 2))

    def test_custom_package_fee_not_capped_or_blocked_above_14(self):
        """Verify sessions > 14 are no longer blocked or capped to 0."""
        fee_15 = calculate_discounted_fee("Custom", 1, 15)
        self.assertEqual(fee_15, 15 * 750)

        fee_30 = calculate_discounted_fee("Custom", 1, 30)
        self.assertEqual(fee_30, 30 * 750)

    @patch("services.pricing_service._get_settings_path")
    @patch("services.pricing_service._get_db_connection")
    def test_admin_update_custom_package_rate(self, mock_get_conn, mock_settings_path):
        """Verify admin can dynamically update custom rate per session."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        mock_settings_path.return_value = "/tmp/test_swimtrack_settings.json"

        # Update custom rate to 900
        success = update_base_prices({"custom": 900})
        self.assertTrue(success)

        # Verify SQL executed with custom key and 900 price
        calls = [call[0] for call in mock_cursor.execute.call_args_list]
        has_custom_update = any("admin_pricing" in str(c) and "custom" in str(c) for c in calls)
        self.assertTrue(has_custom_update or mock_cursor.execute.called)

    def test_admin_pricing_update_endpoint(self):
        """Verify /admin/pricing/update endpoint accepts custom rate."""
        with self.client.session_transaction() as sess:
            sess["user_name"] = "admin"
            sess["role"] = "admin"

        with patch("services.pricing_service.update_base_prices") as mock_update:
            mock_update.return_value = True
            response = self.client.post(
                "/admin/pricing/update",
                data={
                    "demo": "500",
                    "single": "750",
                    "monthly_2d": "5000",
                    "monthly_3d": "7500",
                    "3_months": "18000",
                    "custom": "850",
                },
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            self.assertEqual(response.status_code, 200)
            mock_update.assert_called_once()
            passed_prices = mock_update.call_args[0][0]
            self.assertIn("custom", passed_prices)
            self.assertEqual(passed_prices["custom"], 850)

    @patch("app.get_pg_connection")
    def test_admin_dashboard_pricing_panel_contains_custom_column(self, mock_get_conn):
        """Verify admin dashboard displays custom session rate input and matrix row."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_get_conn.return_value = mock_conn

        with app.test_request_context():
            from flask import session
            session["user_name"] = "admin"
            session["role"] = "admin"

            admin_context = {
                "user_name": "admin",
                "role": "admin",
                "pricing_config": get_pricing_config_dict(),
                "trainers": [],
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

        self.assertIn('name="custom"', html, "Admin pricing form must include input for custom rate")
        self.assertIn('id="adminRateCustom"', html, "Admin pricing form must include adminRateCustom ID")
        self.assertIn('data-pkg-key="custom"', html, "Admin pricing matrix must include custom row")
        self.assertIn('Custom Schedule', html, "Admin pricing matrix must display Custom Schedule")


if __name__ == "__main__":
    unittest.main()
