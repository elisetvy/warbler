"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


from app import app
import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follow

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()
        Message.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        db.session.commit()

        m1 = Message(text='Hello', user_id=u1.id)
        db.session.add(m1)

        db.session.commit()
        self.u1_id = u1.id
        self.m1_id = m1.id

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Tests if message is created"""
        m1 = Message.query.get(self.m1_id)

        self.assertEqual(len(m1.text), 5)
        self.assertNotEqual(len(m1.text), 0)
        self.assertEqual(m1.user_id, self.u1_id)

    def test_message_fail(self):
        """Tests message creation if not nullable fields are left empty"""
        m2 = Message()

        db.session.add(m2)

        self.assertRaises(IntegrityError, db.session.commit)
