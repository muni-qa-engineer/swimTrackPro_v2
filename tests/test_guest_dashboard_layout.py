import unittest
from unittest.mock import patch, MagicMock
from flask import render_template
from app import app


class GuestDashboardLayoutTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch("psycopg2.connect")
    def test_guest_dashboard_cards_rearranged_in_pairs(self, mock_connect):
        """
        Verify the 6 guest dashboard cards are paired in a 2-column grid:
        Row 1: Progress Tracker (1) & Mini Calendar (2)
        Row 2: Make-up Sessions Credit (1) & Membership & Flexibility (2)
        Row 3: My Swimmers (1) & Payment Overview (2)
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_conn
        context = {
            'role': 'guest',
            'user_name': 'test_guest',
            'guest_upcoming_sessions': [],
            'next_session_name': '--',
            'active_packages': 1,
            'total_makeup_credits': 2,
            'expired_makeup_credits': 0,
            'total_sessions': 10,
            'completed_sessions': 4,
            'has_active_package': True,
            'has_pausable_package': False,
            'available_makeup_cards': [],
            'expired_makeup_cards': [],
            'bookings': [],
            'students': [{'name': 'Aryan', 'color_code': '#06b6d4', 'skill_level': 'BEGINNER', 'completed_sessions': 4, 'total_sessions': 10}],
            'current_month_name': 'November 2026',
            'calendar_days': [],
            'total_packages': 1,
            'completed_packages': 0,
            'received_amount': 5000,
            'pending_amount': 0,
            'available_coaches': [],
            'notification_list': []
        }

        with app.test_request_context():
            from flask import session
            session['role'] = 'guest'
            session['user_name'] = 'test_guest'
            session['guest_phone'] = '9133851444'
            html = render_template('guest_dashboard.html', **context)

        # Verify all 6 cards exist by their unique anchors/ids
        idx_progress = html.find('id="tourProgressTracker"')
        idx_calendar = html.find('id="tourMiniCalendar"')
        idx_makeup = html.find('id="tourMakeupSessionsCard"')
        idx_membership = html.find('id="tourMembershipCard"')
        idx_swimmers = html.find('id="tourMySwimmersCard"')
        idx_payment = html.find('id="tourPaymentOverviewCard"')

        self.assertNotEqual(idx_progress, -1, "Progress Tracker card must exist")
        self.assertNotEqual(idx_calendar, -1, "Mini Calendar card must exist")
        self.assertNotEqual(idx_makeup, -1, "Make-up Sessions card must exist")
        self.assertNotEqual(idx_membership, -1, "Membership & Flexibility card must exist")
        self.assertNotEqual(idx_swimmers, -1, "My Swimmers card must exist")
        self.assertNotEqual(idx_payment, -1, "Payment Overview card must exist")

        # Verify ordered sequence: (1, 2), (1, 2), (1, 2)
        # Row 1: Progress Tracker -> Mini Calendar
        # Row 2: Make-up Sessions -> Membership
        # Row 3: My Swimmers -> Payment Overview
        self.assertTrue(
            idx_progress < idx_calendar < idx_makeup < idx_membership < idx_swimmers < idx_payment,
            f"Expected order: Progress < Calendar < Makeup < Membership < Swimmers < Payment. Found indices: "
            f"progress={idx_progress}, calendar={idx_calendar}, makeup={idx_makeup}, "
            f"membership={idx_membership}, swimmers={idx_swimmers}, payment={idx_payment}"
        )


if __name__ == '__main__':
    unittest.main()
