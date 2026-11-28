import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app

class TestProfileRedesign(unittest.TestCase):

    def setUp(self):
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.app.test_client()

    def test_swimmer_profile_flow(self):
        # 1. Simulate Swimmer Login
        with self.client.session_transaction() as sess:
            sess['role'] = 'guest'
            sess['phone'] = '9886641631'
            sess['user_name'] = 'Devansh'
            sess['id_number'] = 'STPS0001'

        # GET /profile
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn("Personal Information", html)
        self.assertIn("Address & Location", html)
        self.assertIn("Swimming Information", html)
        self.assertIn("Swimmer Details & Safety", html)
        self.assertIn("Account & Security", html)
        self.assertIn("STPS0001", html)

        # POST /profile (Update Swimmer Profile)
        post_data = {
            'name': 'Devansh Sharma',
            'dob': '2000-05-15',
            'gender': 'Male',
            'email': 'devansh@example.com',
            'phone': '9886641631',
            'address': 'Plot 42, Silicon Valley, Madhapur',
            'city': 'Hyderabad',
            'state': 'Telangana',
            'pincode': '500081',
            'preferred_location': 'Gachibowli Stadium Pool',
            'skill_level': 'Intermediate',
            'experience': '1-3 Years',
            'swimming_goals': ['Learn to Swim', 'General Fitness'],
            'training_type': '1-on-1 Personal',
            'preferred_days': ['Mon', 'Wed', 'Fri'],
            'preferred_time': 'Morning 6:00 AM - 7:00 AM',
            'swimmer_type': 'Adult Learner',
            'height': '175',
            'emergency_name': 'Rajesh Sharma',
            'emergency_phone': '9886641630',
            'medical_notes': 'Mild dust allergy, none in water'
        }
        res_post = self.client.post('/profile', data=post_data, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        post_html = res_post.data.decode('utf-8')
        self.assertIn("Swimmer Profile updated successfully!", post_html)
        self.assertIn("Devansh Sharma", post_html)

    def test_trainer_profile_flow(self):
        # 2. Simulate Trainer Login
        with self.client.session_transaction() as sess:
            sess['role'] = 'trainer'
            sess['trainer_username'] = 'asdf'
            sess['user_name'] = 'Munisekhar'
            sess['id_number'] = 'STPC0001'

        # GET /profile
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn("Personal Information", html)
        self.assertIn("Professional Information", html)
        self.assertIn("Qualifications & Certifications", html)
        self.assertIn("Training Availability", html)
        self.assertIn("Public Profile & Visibility", html)
        self.assertIn("Training Album & Gallery", html)

        # POST /profile (Update Trainer Profile)
        post_data = {
            'name': 'Munisekhar Coach',
            'phone': '9876543210',
            'whatsapp': '9876543210',
            'email': 'coach@swimtrackpro.com',
            'dob': '1990-01-01',
            'gender': 'Male',
            'professional_title': 'Head Aquatic Coach & Specialist',
            'bio': 'Passionate coach with 10+ years helping swimmers succeed.',
            'experience': '10+ Years',
            'specialties': ['Freestyle & Stroke Tech', 'Breathing & Endurance'],
            'coaching_levels': ['Beginner', 'Intermediate', 'Advanced'],
            'languages': ['English', 'Telugu', 'Hindi'],
            'qualification': 'ASCA Level 2 Certified Coach',
            'certificate_validity': '2028-12-31',
            'currently_working': 'SwimTrackPro Academy',
            'residence_location': 'Gachibowli, Hyderabad',
            'training_locations': 'Gachibowli, Kondapur',
            'available_slots': '6:00 AM - 9:00 AM, 5:00 PM - 8:00 PM',
            'training_type': 'Hybrid (Both)',
            'max_students': '6',
            'preferred_training_days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            'public_profile_visible': 'true',
            'show_experience': 'true',
            'show_qualifications': 'true',
            'show_profile_photo': 'true'
        }
        res_post = self.client.post('/profile', data=post_data, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        post_html = res_post.data.decode('utf-8')
        self.assertIn("Trainer Profile updated successfully!", post_html)

    def test_admin_directory_and_override_flow(self):
        # 3. Simulate Admin Login
        with self.client.session_transaction() as sess:
            sess['role'] = 'admin'
            sess['admin_username'] = 'admin'
            sess['user_name'] = 'Super Admin'
            sess['id_number'] = 'STPA0001'

        # GET /profile (Admin Directory View)
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        self.assertIn("Super Admin Credentials", html)
        self.assertIn("User Directory & Override", html)
        self.assertIn("Swimmers (", html)
        self.assertIn("Coaches (", html)

        # GET /profile?user_type=swimmer&id=9886641631 (Admin Review & Override Swimmer)
        res_swimmer_override = self.client.get('/profile?user_type=swimmer&id=9886641631')
        self.assertEqual(res_swimmer_override.status_code, 200)
        sw_html = res_swimmer_override.data.decode('utf-8')
        self.assertIn("ADMIN OVERRIDE MODE", sw_html)
        self.assertIn("Swimmer Details & Safety", sw_html)
        self.assertIn("account_status", sw_html)

        # POST /profile?user_type=swimmer&id=9886641631 (Admin overrides Swimmer status)
        admin_post_data = {
            'name': 'Devansh Sharma Override',
            'phone': '9886641631',
            'email': 'devansh.override@example.com',
            'skill_level': 'Advanced',
            'account_status': 'Active'
        }
        res_override_post = self.client.post('/profile?user_type=swimmer&id=9886641631', data=admin_post_data, follow_redirects=True)
        self.assertEqual(res_override_post.status_code, 200)
        override_html = res_override_post.data.decode('utf-8')
        self.assertIn("Swimmer Profile updated successfully!", override_html)

        # GET /profile?user_type=trainer&id=asdf (Admin Review & Override Trainer)
        res_trainer_override = self.client.get('/profile?user_type=trainer&id=asdf')
        self.assertEqual(res_trainer_override.status_code, 200)
        tr_html = res_trainer_override.data.decode('utf-8')
        self.assertIn("ADMIN OVERRIDE MODE", tr_html)
        self.assertIn("Professional Coaching Title", tr_html)

if __name__ == '__main__':
    unittest.main()
