import unittest
from unittest.mock import patch, MagicMock
from app import app


class MobileFooterTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("swimtrackpro.routes.dashboard.get_pg_connection")
    @patch("swimtrackpro.routes.dashboard.load_data")
    @patch("swimtrackpro.routes.dashboard.get_all_packages")
    def test_landing_page_footer_remains_visible_on_mobile(self, mock_packages, mock_load_data, mock_conn):
        """Verify landing page (/) retains the footer on mobile view (no footer-mobile-hidden/d-none)."""
        mock_packages.return_value = []
        mock_load_data.return_value = {'bookings': []}
        
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = []
        conn_mock = MagicMock()
        conn_mock.cursor.return_value = cursor_mock
        mock_conn.return_value = conn_mock

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        # 1. Landing page body has 'landing-page' class
        self.assertIn('landing-page', html)

        # 2. Footer is present
        self.assertIn('SwimTrackPro', html)
        self.assertIn('<footer class="footer', html)

        # 3. Footer wrapper on landing page does NOT hide on mobile
        self.assertIn('class="site-footer-section"', html)
        self.assertNotIn('site-footer-section footer-mobile-hidden', html)
        self.assertNotIn('site-footer-section d-none', html)

    def test_register_page_footer_hidden_on_mobile(self):
        """Verify coach registration page (/register) hides footer on mobile view."""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        # Footer must have mobile hidden classes
        self.assertIn('footer-mobile-hidden', html)
        self.assertIn('d-none d-md-block', html)
        self.assertIn('site-footer-section footer-mobile-hidden d-none d-md-block', html)

    def test_about_page_footer_hidden_on_mobile(self):
        """Verify about page (/about) hides footer on mobile view."""
        response = self.client.get('/about')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        self.assertIn('footer-mobile-hidden', html)
        self.assertIn('d-none d-md-block', html)

    def test_help_page_footer_hidden_on_mobile(self):
        """Verify help page (/help) hides footer on mobile view."""
        response = self.client.get('/help')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        self.assertIn('footer-mobile-hidden', html)
        self.assertIn('d-none d-md-block', html)

    def test_faq_page_footer_hidden_on_mobile(self):
        """Verify FAQ page (/faq) hides footer on mobile view."""
        response = self.client.get('/faq')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        self.assertIn('footer-mobile-hidden', html)
        self.assertIn('d-none d-md-block', html)

    def test_terms_page_footer_hidden_on_mobile(self):
        """Verify terms page (/terms-agreement) hides footer on mobile view."""
        response = self.client.get('/terms-agreement')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        self.assertIn('footer-mobile-hidden', html)
        self.assertIn('d-none d-md-block', html)

    def test_global_css_contains_mobile_footer_rule(self):
        """Verify static/css/global.css contains @media rule hiding footer on mobile."""
        with open('static/css/global.css', 'r', encoding='utf-8') as f:
            css = f.read()

        self.assertIn('.footer-mobile-hidden', css)
        self.assertIn('@media (max-width: 768px)', css)
        self.assertIn('display: none !important', css)

    def test_trainer_nav_profile_text_and_icon(self):
        """Verify trainer navbar displays 'My Profile' and highlighted profile icon."""
        with self.client.session_transaction() as sess:
            sess['user_name'] = 'Rajesh'
            sess['role'] = 'trainer'

        response = self.client.get('/help')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        # Link must be 'My Profile', not 'Update My Profile'
        self.assertIn('My Profile', html)
        self.assertNotIn('Update My Profile', html)

        # Profile avatar badge must have fa-solid fa-user icon
        self.assertIn('user-avatar-badge', html)
        self.assertIn('fa-solid fa-user', html)


if __name__ == '__main__':
    unittest.main()
