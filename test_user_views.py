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

        db.session.commit()
        self.u1_id = u1.id

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





    # def test_show_users_list(self):
    #     """Tests if user listing page is loaded correctly"""
    #     with self.client as client:
    #         user = User.query.get(self.u1_id)
    #         do_login(user)

    #         resp = client.get('/users')
    #         html = resp.get_data(as_text=True)

    #         self.assertEqual(resp.status_code, 200)
    #         self.assertIn('<!-- Test for /users route.', html)