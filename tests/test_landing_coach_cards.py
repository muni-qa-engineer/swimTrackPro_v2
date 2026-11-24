import unittest
from unittest.mock import patch, MagicMock
from app import app


class LandingCoachCardsTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = app.test_client()

    @patch("psycopg2.connect")
    @patch("swimtrackpro.routes.dashboard.load_data")
    def test_landing_page_coach_cards_horizontal_scroll_and_details(self, mock_load_data, mock_connect):
        """
        Verify:
        1. Meet Our Coaches section uses horizontal scroll track (.coaches-scroll-track)
        2. Desktop scroll arrows are present (#coachScrollPrev, #coachScrollNext)
        3. Coach profile photo is rendered instead of generic icon
        4. Detail rows show only icon and value without extra text labels
        """
        mock_load_data.return_value = {"bookings": []}

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Mock sequence of fetchall calls in index():
        mock_cursor.fetchall.side_effect = [
            # 1. get_all_packages()
            [(1, "individual", "Monthly", 6000, 10)],
            # 2. homepage_carousel
            [(1, "https://res.cloudinary.com/demo/image/upload/sample.jpg")],
            # 3. trainers with profile_pictures join
            # (username, name, experience, qualification, currently_working, residence_location, rating,
            #  student_count, review_count, available_slots, photos, id_number, id_proof_file, profile_pic)
            [
                (
                    "coach_vikram",
                    "Vikram Seth",
                    "7 Years Experience",
                    "FINA Level 3 Certified",
                    "Sports Authority Pool",
                    "Bengaluru",
                    4.9,
                    42,
                    15,
                    "[]",
                    "https://res.cloudinary.com/demo/image/upload/coach_swim.jpg",
                    "STPC0001",
                    "id_proof_vikram.png",
                    "https://res.cloudinary.com/demo/image/upload/vikram_avatar.jpg",
                ),
                (
                    "coach_ananya",
                    "Ananya Sharma",
                    "4 Years",
                    "ASCA Level 2",
                    "Aquatic Complex",
                    "Hyderabad",
                    4.8,
                    28,
                    0,
                    "[]",
                    "",
                    "STPC0002",
                    "ananya_id.png",
                    "ananya_profile.jpg",
                ),
            ],
            # 4. coach_feedback
            [],
            # 5. any fallbacks
            [],
        ]
        mock_connect.return_value = mock_conn

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # 1. Horizontal scrolling track and navigation
        self.assertIn('class="coaches-scroll-track', html)
        self.assertIn('id="coachesScrollTrack"', html)
        self.assertIn('id="coachScrollPrev"', html)
        self.assertIn('id="coachScrollNext"', html)
        self.assertIn('class="coach-card-item', html)

        # 2. Coach photo rendered
        self.assertIn('class="coach-profile-photo"', html)
        self.assertIn("vikram_avatar.jpg", html)
        self.assertIn("/static/profile_pictures/ananya_profile.jpg", html)
        # Generic user-tie icon should no longer be used as the profile icon
        self.assertNotIn('fa-user-tie', html)

        # 3. Card details: Icon + Value only (No redundant labels)
        self.assertIn("Vikram Seth", html)
        self.assertIn("7 Years Experience", html)
        self.assertIn("FINA Level 3 Certified", html)
        self.assertIn("Bengaluru", html)
        self.assertIn("42", html)

        self.assertIn("Ananya Sharma", html)
        self.assertIn("4 Years", html)
        self.assertIn("ASCA Level 2", html)
        self.assertIn("Hyderabad", html)
        self.assertIn("28", html)

        # Verify old text labels are absent from detail lines:
        self.assertNotIn('<i class="fa-solid fa-briefcase text-primary me-2"></i> Experience', html)
        self.assertNotIn('<i class="fa-solid fa-graduation-cap text-primary me-2"></i> Qualification', html)
        self.assertNotIn('<i class="fa-solid fa-users text-primary me-2"></i> Swimmers Trained', html)
        self.assertNotIn('<i class="fa-solid fa-location-dot text-danger me-2"></i> Location', html)

    @patch("psycopg2.connect")
    @patch("swimtrackpro.routes.dashboard.load_data")
    def test_landing_page_coach_card_initial_fallback_when_no_photo(self, mock_load_data, mock_connect):
        """
        Verify that when a coach has no profile picture or photos uploaded,
        it cleanly renders the initial letter without broken image tags.
        """
        mock_load_data.return_value = {"bookings": []}

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchall.side_effect = [
            [(1, "individual", "Monthly", 6000, 10)],
            [],
            [
                (
                    "coach_rohit",
                    "Rohit Verma",
                    "3 Years",
                    "NIS Diploma",
                    "Club",
                    "Mumbai",
                    5.0,
                    10,
                    2,
                    "[]",
                    "",
                    "STPC0003",
                    "",
                    "",
                )
            ],
            [],
            [],
        ]
        mock_connect.return_value = mock_conn

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn("Rohit Verma", html)
        # Should render initial "R" inside avatar container
        self.assertIn("R</span>", html)
