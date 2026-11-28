import unittest
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app

class TestProfileUIEnhancements(unittest.TestCase):

    def setUp(self):
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.app.test_client()

    def test_item_5_profile_dropdown_in_base_navbar(self):
        """Item 5: Profile dropdown has circular avatar, bold name, ID with spacing, no cramped tags."""
        with self.client.session_transaction() as sess:
            sess['role'] = 'guest'
            sess['phone'] = '9886641631'
            sess['user_name'] = 'Devansh Sharma'
            sess['id_number'] = 'STPS0088'

        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Check navbar avatar dropdown structure
        self.assertIn('id="avatarDropdown"', html)
        self.assertIn('STPS0088', html)
        self.assertIn('Devansh Sharma', html)
        # Ensure cramped tags like SWIMMING COACH / ACTIVE SWIMMER are removed from dropdown header
        self.assertNotIn('SWIMMING COACH', html.split('id="avatarDropdown"')[1].split('dropdown-menu')[0])

    def test_items_1_2_3_4_swimmer_profile_enhancements(self):
        """Verify Items 1, 2, 3, 4 for Swimmer Role."""
        with self.client.session_transaction() as sess:
            sess['role'] = 'guest'
            sess['phone'] = '9886641631'
            sess['user_name'] = 'Devansh'
            sess['id_number'] = 'STPS0088'

        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        # Item 1: Beside the name, no duplicate role tag, only single status badge
        hero_section = html.split('class="profile-hero-card"')[1].split('<!-- ============================================================= -->')[0] if 'class="profile-hero-card"' in html else html
        self.assertNotIn('SWIMMING COACH', hero_section)
        self.assertNotIn('ACTIVE SWIMMER', hero_section)
        self.assertIn('Active', hero_section)

        # Item 2: View Digital ID wires to showMyIdCard()
        self.assertIn('showMyIdCard()', html)
        self.assertIn('View Digital ID', html)

        # Item 3: Account & Security auto-fills mobile & email
        self.assertIn('Registered Mobile Number', html)
        self.assertIn('Registered Email Address', html)
        self.assertIn('9886641631', html)
        self.assertIn('VERIFIED', html)

        # Item 4: Dynamic pool location with Maps locator & datalist
        self.assertIn('statePoolDatalist', html)
        self.assertIn('locatePoolOnMaps()', html)
        self.assertIn('detectCurrentLocationPool()', html)
        self.assertIn('Locate Pool on Maps', html)

    def test_items_6_7_8_trainer_profile_enhancements(self):
        """Verify Items 6, 7, 8 for Trainer Role."""
        with self.client.session_transaction() as sess:
            sess['role'] = 'trainer'
            sess['trainer_username'] = 'asdf'
            sess['user_name'] = 'Munisekhar'
            sess['id_number'] = 'STPA0001'

        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')

        # Item 6: Coach Full Name is locked/readonly; username is editable input
        self.assertIn('Coach Full Name', html)
        self.assertIn('Locked', html)
        self.assertIn('name="username"', html)
        self.assertIn('id="trainerUsername"', html)

        # Item 7: Uploaded Photos redesign - no unwanted default text
        self.assertNotIn('Training session with Coach Munisekhar', html)
        self.assertIn('Uploaded Photos', html)

        # Item 8: Label updated to Coaching Available Location and Available Time Slots with 15-min pill picker
        self.assertIn('Coaching Available Location', html)
        self.assertIn('Available Time Slots', html)
        self.assertIn('morningSlotsContainer', html)
        self.assertIn('afternoonSlotsContainer', html)
        self.assertIn('eveningSlotsContainer', html)
        self.assertIn('applyTimePreset', html)
        self.assertIn('toggleRangeSlots', html)

    def test_trainer_update_username_and_availability_post(self):
        """Verify Trainer POST updates username and available time slots."""
        with self.client.session_transaction() as sess:
            sess['role'] = 'trainer'
            sess['trainer_username'] = 'asdf'
            sess['user_name'] = 'Munisekhar'
            sess['id_number'] = 'STPA0001'

        post_data = {
            'username': 'asdf',
            'name': 'Hacked Name Attempt', # Should be ignored because trainer name is locked
            'phone': '9876543210',
            'experience': '10+ Years',
            'qualification': 'ASCA Level 2 Certified Coach',
            'currently_working': 'SwimTrackPro Academy',
            'residence_location': 'Gachibowli, Hyderabad',
            'training_locations': 'Gachibowli Stadium Pool',
            'available_slots': '06:00 AM - 09:00 AM, 05:00 PM - 08:00 PM',
            'training_type': 'Hybrid (Both)'
        }
        res_post = self.client.post('/profile', data=post_data, follow_redirects=True)
        self.assertEqual(res_post.status_code, 200)
        post_html = res_post.data.decode('utf-8')
        self.assertIn("Trainer Profile updated successfully!", post_html)
        self.assertIn("06:00 AM - 09:00 AM, 05:00 PM - 08:00 PM", post_html)

if __name__ == '__main__':
    unittest.main()
