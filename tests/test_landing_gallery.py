import unittest
from unittest.mock import patch, MagicMock
from app import app


class LandingGalleryTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()

    @patch("psycopg2.connect")
    @patch("swimtrackpro.routes.dashboard.load_data")
    def test_landing_page_renders_gallery_section(self, mock_load_data, mock_connect):
        mock_load_data.return_value = {"bookings": []}

        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock sequential fetchall calls in index():
        mock_cursor.fetchall.side_effect = [
            # 1. get_all_packages(): SELECT id, category, package_name, base_price, discount_percentage FROM packages
            [(1, "individual", "Monthly", 6000, 10)],
            # 2. homepage_carousel: SELECT id, image_url FROM homepage_carousel
            [(1, "https://res.cloudinary.com/demo/image/upload/sample_pool.jpg")],
            # 3. trainers: SELECT username, name, experience, qualification, currently_working, residence_location, rating, student_count, review_count, available_slots, photos
            [("coach_rajesh", "Rajesh Kumar", 8, "ASCA Level 2", "Gachibowli Stadium", "Hyderabad", 4.9, 15, 8, "[]", "https://res.cloudinary.com/demo/image/upload/coach_drill.jpg")],
            # 4. coach_feedback: SELECT guest_name, rating, comment, trainer_name
            [("Amit", 5, "Great coaching!", "Rajesh Kumar")],
            # Fallbacks / notices
            []
        ]
        mock_connect.return_value = mock_conn

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # 1. Verify Gallery section is present
        self.assertIn('id="gallery"', html)
        self.assertIn("Training Moments & Facilities", html)
        self.assertIn("Protected Gallery:", html)

        # 2. Verify filter tabs are rendered
        self.assertIn('data-filter="all"', html)
        self.assertIn('data-filter="facilities"', html)
        self.assertIn('data-filter="coaching"', html)

        # 3. Verify Privacy and Anti-Download Protection attributes are in place
        self.assertIn('class="gallery-photo-shield"', html)
        self.assertIn('oncontextmenu="return false;"', html)
        self.assertIn('draggable="false"', html)
        self.assertIn('class="gallery-watermark"', html)

        # 4. Verify Lightbox Modal and protective shield are present
        self.assertIn('id="galleryLightboxModal"', html)
        self.assertIn('class="lightbox-photo-shield"', html)
        self.assertIn("Read-Only View", html)

        # 5. Verify Navigation bar link to Gallery is rendered for visitors
        self.assertIn('href="#gallery"', html)
        self.assertIn("Gallery</a>", html)


if __name__ == "__main__":
    unittest.main()
