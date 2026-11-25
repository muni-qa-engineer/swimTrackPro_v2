import unittest
from unittest.mock import patch, MagicMock
from app import app


class LoginPasswordToggleTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()

    @patch("psycopg2.connect")
    @patch("swimtrackpro.routes.dashboard.load_data")
    def test_login_page_renders_password_toggle_elements(self, mock_load_data, mock_connect):
        """
        Verify that:
        1. password input (#passwordInput) exists with type="password"
        2. toggle password button (#togglePasswordBtn) exists with onclick="toggleLoginPasswordVisibility()"
        3. toggle password icon (#togglePasswordIcon) exists with class fa-solid fa-eye
        4. toggleLoginPasswordVisibility JavaScript function is present and toggles between 'password' and 'text',
           and switches between fa-eye and fa-eye-slash.
        """
        mock_load_data.return_value = {"bookings": []}

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_conn

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # 1. Elements
        self.assertIn('id="passwordInput"', html)
        self.assertIn('id="togglePasswordBtn"', html)
        self.assertIn('id="togglePasswordIcon"', html)
        self.assertIn('class="fa-solid fa-eye"', html)
        self.assertIn('class="toggle-pass-btn"', html)

        # 2. onclick attribute & event handler
        self.assertIn('onclick="toggleLoginPasswordVisibility()"', html)
        self.assertIn('function toggleLoginPasswordVisibility()', html)
        self.assertIn("pwdInput.type = 'text'", html)
        self.assertIn("pwdInput.type = 'password'", html)
        self.assertIn("pwdIcon.classList.add('fa-eye-slash')", html)
        self.assertIn("pwdIcon.classList.add('fa-eye')", html)

        # 3. Reset function
        self.assertIn('function resetPasswordVisibility()', html)
