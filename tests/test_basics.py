import unittest
from flask import current_app
from app import create_app, db


class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()  # get context
        self.app_context.push()  # activate context
        db.create_all()  # create database

    def tearDown(self):
        db.session.remove()
        db.drop_all()  # delete database
        self.app_context.pop()  # deactivate context

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
