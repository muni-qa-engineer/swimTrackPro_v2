import os
import unittest
from unittest.mock import patch, MagicMock
from flask import render_template
from app import app


class GalleryTabTests(unittest.TestCase):
    def setUp(self):
        app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret-key",
            WTF_CSRF_ENABLED=False
        )
        self.client = app.test_client()

    def test_file_uploader_static_assets_exist(self):
        """Verify modern file uploader CSS and JS static files exist and contain required classes."""
        css_path = os.path.join(app.root_path, "static", "css", "fileUploader.css")
        js_path = os.path.join(app.root_path, "static", "js", "fileUploader.js")
        
        self.assertTrue(os.path.exists(css_path), "fileUploader.css must exist")
        self.assertTrue(os.path.exists(js_path), "fileUploader.js must exist")

        with open(css_path, "r") as f:
            css_content = f.read()
            self.assertIn(".stp-uploader-card", css_content)
            self.assertIn(".stp-file-badge", css_content)
            self.assertIn(".stp-dropzone", css_content)

        with open(js_path, "r") as f:
            js_content = f.read()
            self.assertIn("STPFileUploader", js_content)
            self.assertIn("addFiles", js_content)
            self.assertIn("removeFile", js_content)

    def test_admin_dashboard_template_renders_gallery_tab(self):
        """Verify admin_dashboard.html renders Gallery tab, views, controls, and modals."""
        with app.test_request_context():
            mock_photos = [
                {
                    'id': 101,
                    'url': 'https://res.cloudinary.com/demo/image/upload/sample1.jpg',
                    'coach_username': 'coach_rajesh',
                    'coach_name': 'Rajesh Kumar',
                    'coach_id': 'STP-COACH-101',
                    'section': 'coaching',
                    'caption': 'Freestyle technique training',
                    'is_published': True,
                    'uploaded_by': 'coach',
                    'created_at': '2026-11-25 10:00'
                },
                {
                    'id': 102,
                    'url': 'https://res.cloudinary.com/demo/image/upload/sample2.jpg',
                    'coach_username': 'coach_ananya',
                    'coach_name': 'Ananya Sharma',
                    'coach_id': 'STP-COACH-102',
                    'section': 'achievements',
                    'caption': 'Gold Medal State Meet',
                    'is_published': False,
                    'uploaded_by': 'coach',
                    'created_at': '2026-11-25 11:30'
                }
            ]
            mock_by_coach = {
                'Rajesh Kumar • STP-COACH-101': {
                    'coach_name': 'Rajesh Kumar',
                    'coach_id': 'STP-COACH-101',
                    'coach_username': 'coach_rajesh',
                    'photos': [mock_photos[0]]
                },
                'Ananya Sharma • STP-COACH-102': {
                    'coach_name': 'Ananya Sharma',
                    'coach_id': 'STP-COACH-102',
                    'coach_username': 'coach_ananya',
                    'photos': [mock_photos[1]]
                }
            }

            context = {
                'user_name': 'admin',
                'current_user': {'username': 'admin', 'role': 'admin'},
                'role': 'admin',
                'students': [],
                'trainers': [],
                'bookings': [],
                'sessions': [],
                'today_sessions': [],
                'activities': [],
                'chart_data': {},
                'pricing_packages': [],
                'pricing_config': {},
                'packages': [],
                'carousel_images': [],
                'gallery_photos': mock_photos,
                'gallery_by_coach': mock_by_coach,
                'published_gallery_count': 1,
                'pending_gallery_count': 1,
                'active_promotion': None
            }

            html = render_template('admin_dashboard.html', **context)

            # 1. Navigation Tab Button
            self.assertIn("switchSection('gallery', this)", html)
            self.assertIn('data-section="gallery"', html)
            self.assertIn('Gallery', html)

            # 2. Gallery Section container & stats
            self.assertIn('id="section-gallery"', html)
            self.assertIn('Platform Photo Gallery & Landing Showcase', html)
            self.assertIn('Live on Landing', html)
            self.assertIn('Pending Review', html)

            # 3. View Switcher & Filters
            self.assertIn('id="galleryViewGridBtn"', html)
            self.assertIn('id="galleryViewCoachBtn"', html)
            self.assertIn('id="gallerySearchInput"', html)
            self.assertIn('id="gallerySectionFilter"', html)
            self.assertIn('id="galleryStatusFilter"', html)

            # 4. Multi-Select Sticky Bar
            self.assertIn('id="galleryBulkActionBar"', html)
            self.assertIn('Publish Selected', html)
            self.assertIn('Unpublish', html)
            self.assertIn('Delete Selected', html)

            # 5. Grid View Cards
            self.assertIn('id="galleryCard-101"', html)
            self.assertIn('id="galleryCard-102"', html)
            self.assertIn('Rajesh Kumar', html)
            self.assertIn('Ananya Sharma', html)
            self.assertIn('Freestyle technique training', html)

            # 6. Grouped by Coach View
            self.assertIn('id="galleryCoachViewContainer"', html)
            self.assertIn('STP-COACH-101', html)
            self.assertIn('STP-COACH-102', html)

            # 7. Modals
            self.assertIn('id="adminGalleryUploadModal"', html)
            self.assertIn('id="galleryLightboxModal"', html)
            self.assertIn('id="adminGalleryUploaderCard"', html)
            self.assertIn('id="adminDropzone"', html)

    def test_coach_profile_renders_album_uploader(self):
        """Verify coach profile template renders the album uploader dropzone card."""
        with app.test_request_context():
            trainer_context = {
                'trainer': {
                    'username': 'coach_rajesh',
                    'name': 'Rajesh Kumar',
                    'phone': '9876543210',
                    'email': 'rajesh@example.com',
                    'whatsapp': '9876543210',
                    'experience': 5,
                    'qualification': 'Certified Coach',
                    'currently_working': 'SwimTrackPro Academy',
                    'residence_location': 'Gachibowli, Hyderabad',
                    'id_proof': 'UID-12345'
                },
                'role': 'trainer',
                'coach_photos': []
            }
            html = render_template('profile.html', **trainer_context)
            self.assertIn('id="coachAlbumUploaderCard"', html)
            self.assertIn('id="coachDropzone"', html)
            self.assertIn('name="training_pics"', html)
            self.assertIn('Drag files here or', html)

    @patch("swimtrackpro.routes.general.get_pg_connection")
    def test_admin_gallery_toggle_publish(self, mock_get_conn):
        """Verify toggle publish endpoint flips is_published and returns JSON for AJAX."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Mock current status is False (unpublish -> publish)
        mock_cursor.fetchone.return_value = (False,)

        with self.client.session_transaction() as sess:
            sess["role"] = "admin"
            sess["user_name"] = "admin"

        response = self.client.post(
            "/admin/gallery/toggle_publish/42",
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertTrue(data.get("is_published"))

        mock_cursor.execute.assert_any_call(
            "UPDATE gallery_photos SET is_published = %s WHERE id = %s",
            (True, 42)
        )
        mock_conn.commit.assert_called()

    @patch("services.cloudinary_service.delete_image")
    @patch("swimtrackpro.routes.general.get_pg_connection")
    def test_admin_gallery_delete(self, mock_get_conn, mock_delete_image):
        """Verify delete endpoint removes photo from gallery_photos."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn
        mock_delete_image.return_value = True

        mock_cursor.fetchone.return_value = ("https://res.cloudinary.com/demo/image/upload/test.jpg",)

        with self.client.session_transaction() as sess:
            sess["role"] = "admin"
            sess["user_name"] = "admin"

        response = self.client.post(
            "/admin/gallery/delete/42",
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))

        mock_cursor.execute.assert_any_call(
            "DELETE FROM gallery_photos WHERE id = %s",
            (42,)
        )
        mock_conn.commit.assert_called()

    @patch("swimtrackpro.routes.general.get_pg_connection")
    def test_admin_gallery_bulk_action_publish(self, mock_get_conn):
        """Verify bulk action can publish multiple selected photos."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with self.client.session_transaction() as sess:
            sess["role"] = "admin"
            sess["user_name"] = "admin"

        response = self.client.post(
            "/admin/gallery/bulk-action",
            json={"action": "publish", "photo_ids": [10, 20, 30]},
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("count"), 3)

        mock_cursor.execute.assert_called_with(
            "UPDATE gallery_photos SET is_published = TRUE WHERE id = ANY(%s)",
            ([10, 20, 30],)
        )
        mock_conn.commit.assert_called()

    def test_gallery_routes_require_admin(self):
        """Verify non-admin users cannot trigger admin gallery management actions."""
        # Unauthenticated user
        resp1 = self.client.post("/admin/gallery/toggle_publish/1")
        self.assertEqual(resp1.status_code, 302)

        # Regular trainer role
        with self.client.session_transaction() as sess:
            sess["role"] = "trainer"
            sess["trainer_username"] = "coach1"

        resp2 = self.client.post("/admin/gallery/delete/1")
        self.assertEqual(resp2.status_code, 302)


if __name__ == "__main__":
    unittest.main()
