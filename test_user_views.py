"""User views tests."""

# run these tests like:
#
#    python -m unittest test_user_views.py


from app import app, do_login
import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follow

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"
app.config['WTF_CSRF_ENABLED'] = False

# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_signup_form(self):
        """Tests if signup page is loaded correctly"""
        with self.client as client:
            resp = client.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today', html)

    def test_user_signup(self):
        """Tests if user signup is successful"""
        with self.client as client:
            resp = client.post('/signup',
                               data={'username': 'cat',
                                     'email': 'cat@gmail.com',
                                     'password': 'password',
                                     'image_url': '',
                                     'header_image_url': '',
                                     'location': 'LA'})

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, '/')

    def test_user_signup_fail(self):
        """Tests if user signup fails"""
        with self.client as client:
            resp = client.post('/signup',
                               data={'username': 'u1',
                                     'email': 'cat@gmail.com',
                                     'password': 'password',
                                     'image_url': '',
                                     'header_image_url': '',
                                     'location': 'LA'})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Username already taken', html)
            self.assertIn('Join Warbler today', html)

    def test_user_signup_redirect(self):
        """Tests if successful user signup redirects to homepage."""
        with self.client as client:
            resp = client.post('/signup',
                               data={'username': 'cat',
                                     'email': 'cat@gmail.com',
                                     'password': 'password',
                                     'image_url': '',
                                     'header_image_url': '',
                                     'location': 'LA'},
                               follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<!-- Test for /users route.", html)

    def test_user_login_success(self):
        """Tests if user is able to login with valid credentials"""
        with self.client as client:
            resp = client.post('/login',
                               data={'username': 'u1',
                                     'password': 'password'},
                               follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello, u1!", html)

    def test_user_login_fail(self):
        """Tests if login fails with incorrect credentials"""
        with self.client as client:
            resp = client.post('/login',
                               data={'username': 'u1',
                                     'password': 'password1'})
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials", html)

    def test_logout(self):
        """Tests for logout if user is logged in"""
        with self.client as client:
            resp = client.post('/login',
                               data={'username': 'u1',
                                     'password': 'password'})

            logout_resp = client.post('/logout',
                                      follow_redirects=True)
            html = logout_resp.get_data(as_text=True)

            self.assertEqual(logout_resp.status_code, 200)
            self.assertIn("Welcome back.", html)

    def test_logout_fail(self):
        """Tests for failed logout if no user is logged in"""
        with self.client as client:
            logout_resp = client.post('/logout',
                                      follow_redirects=True)
            html = logout_resp.get_data(as_text=True)

            self.assertEqual(logout_resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_show_users_list(self):
        """Tests if user listing page is loaded correctly"""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp_search = client.get('/users')
            html = resp_search.get_data(as_text=True)

            self.assertEqual(resp_search.status_code, 200)
            self.assertIn('<!-- tests for search user', html)

    def test_show_user_profile(self):
        """Tests if user profile is being displayed"""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp = client.get(f'/users/{self.u1_id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<!-- tests for user profile', html)

    def test_user_following_success(self):
        """Tests if user following is displayed when logged in"""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp = client.get(f'/users/{self.u1_id}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<!-- test for following', html)

    def test_user_following_fail(self):
        """Tests if user following fails to show when not logged in"""
        with self.client as client:
            resp = client.get(f'/users/{self.u1_id}/following',
                              follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_user_follower(self):
        """Tests if user followers is displayed when logged in"""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp = client.get(f'/users/{self.u1_id}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<!-- test for followers', html)

    def test_show_likes_success(self):
        """Tests showing likes for user"""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp = client.get(f'/users/{self.u1_id}/likes')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<!-- test for showing likes', html)

    def test_show_likes_fail(self):
        """Tests for likes page if user is not logged in. Should result in authorization error"""
        with self.client as client:
            resp = client.get(f'/users/{self.u1_id}/likes',
                              follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_start_following_success(self):
        """Tests to start following another user if user is logged in."""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp = client.post(f'/users/follow/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<!-- test for following', html)

    def test_start_following_fail(self):
        """Tests to start following another user if no user is logged in."""
        with self.client as client:
            resp = client.post(f'/users/follow/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', html)

    def test_stop_following_success(self):
        """Tests to stop following another user if user is logged in."""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp_start_following = client.post(f'/users/follow/{self.u2_id}', follow_redirects=True)

            resp = client.post(f'/users/stop-following/{self.u2_id}', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<!-- test for following', html)

    def test_edit_profile_form(self):
        """Tests to update profile form displays."""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp = client.get('/users/profile')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Edit Your Profile', html)

    def test_edit_profile_success(self):
        """Tests to update profile."""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp = client.post('/users/profile',
                               data={
                                   'username': 'u12',
                                   'email': 'u12@email.com',
                                   'password': 'password'
                               }, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<!-- tests for user profile', html)

    def test_edit_profile_fail(self):
        """Tests to update profile with existing username."""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp = client.post('/users/profile',
                               data={
                                   'username': 'u2',
                                   'email': 'u@email.com',
                                   'password': 'password'
                               })
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Username already exists!', html)

    def test_delete_user(self):
        """Tests to delete user."""
        with self.client as client:
            resp_login = client.post('/login',
                                     data={'username': 'u1',
                                           'password': 'password'})

            resp = client.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today', html)

            users = [ user.username for user in User.query.all() ]
            self.assertNotIn("u1", users)