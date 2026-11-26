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
        self.assertTrue("Highlights & Achievements" in html or "Training Moments & Achievements" in html)
        self.assertNotIn("Olympic Standard", html)
        self.assertNotIn("Pool Facility & Academy", html)
        
        # Verify removed subtitle and "Protected Gallery:" pill are absent
        self.assertNotIn("Explore real coaching moments", html)
        self.assertNotIn("Protected Gallery:", html)

        # 2. Verify filter tabs are rendered
        self.assertIn('data-filter="all"', html)
        self.assertIn('data-filter="achievements"', html)
        self.assertIn('data-filter="coaching"', html)
        self.assertIn('data-filter="swimmers"', html)

        # 3. Verify Privacy and Anti-Download Protection attributes are in place, but visual tags and heading overlays are removed
        self.assertIn('class="gallery-photo-shield"', html)
        self.assertIn('oncontextmenu="return false;"', html)
        self.assertIn('draggable="false"', html)
        self.assertNotIn('class="gallery-watermark"', html)
        self.assertNotIn('class="gallery-caption', html)

        # 4. Verify Lightbox Modal and protective shield are present, but "Read-Only View" tag is removed
        self.assertIn('id="galleryLightboxModal"', html)
        self.assertIn('class="lightbox-photo-shield"', html)
        self.assertNotIn("Read-Only View", html)

        # 5. Verify Navigation bar link to Gallery is rendered for visitors
        self.assertIn('href="#gallery"', html)
        self.assertIn("Gallery</a>", html)

        # 6. Verify section order: Coaches -> Gallery -> Coaching Plans
        coaches_idx = html.find('id="coaches"')
        gallery_idx = html.find('id="gallery"')
        plans_idx = html.find('id="plans"')
        self.assertTrue(coaches_idx != -1 and gallery_idx != -1 and plans_idx != -1)
        self.assertTrue(coaches_idx < gallery_idx < plans_idx)


        # 7. Verify desktop and mobile responsive optimizations
        # Hidden on mobile view, shown on desktop
        self.assertIn('d-none d-md-flex', html)
        self.assertNotIn('Swipe horizontally', html)
        # Desktop 3-row layout and mobile 2-row layout in CSS
        self.assertIn('grid-template-rows: repeat(3, 210px)', html)
        self.assertIn('grid-template-rows: repeat(2, 160px)', html)
        self.assertIn('grid-auto-flow: column', html)
        self.assertIn('overflow-x: auto', html)
        # Desktop navigation controls
        self.assertIn('id="galleryScrollPrev"', html)
        self.assertIn('id="galleryScrollNext"', html)


        # 8. Verify Long Term Coaching mobile horizontal view
        self.assertIn('class="long-term-grid', html)
        self.assertIn('.long-term-grid', html)


        # 9. Verify What You Will Get redesigned cards and mobile layout
        self.assertIn('class="levels-grid"', html)
        self.assertIn('class="level-icon-circle mb-3"', html)
        self.assertIn('.levels-grid', html)

    @patch("psycopg2.connect")
    @patch("swimtrackpro.routes.dashboard.load_data")
    def test_empty_gallery_sync_when_no_published_photos(self, mock_load_data, mock_connect):
        """Verify that when gallery is emptied in Admin, landing page has 0 photos and shows in-sync empty state."""
        mock_load_data.return_value = {"bookings": []}

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock database queries:
        # 1. packages
        # 2. homepage_carousel
        # 3. trainers
        # 4. gallery_photos -> 0 rows (admin deleted all photos)
        # 5. coach_feedback
        mock_cursor.fetchall.side_effect = [
            [(1, "individual", "Monthly", 6000, 10)],
            [],  # carousel
            [],  # trainers
            [],  # gallery_photos (EMPTY)
            []   # feedback
        ]
        mock_connect.return_value = mock_conn

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # 1. Verify Gallery section is present
        self.assertIn('id="gallery"', html)

        # 2. Verify count says 0 moments, matching 0 published photos in Admin
        self.assertIn('All Moments (<span id="galleryCountAll">0</span>)', html)

        # 3. Verify clean empty state message is shown
        self.assertIn('No photos published in the gallery yet', html)

        # 4. Verify hardcoded fallback photos are NOT injected
        self.assertNotIn('Underwater Freestyle Form & Stroke Correction Drill', html)
        self.assertNotIn('State & National Championship Merit Certificates', html)
        self.assertNotIn('Butterfly Stroke Rhythm & Technique Drill at Student Pool', html)
        self.assertNotIn('class="gallery-item-card"', html)


if __name__ == "__main__":
    unittest.main()
