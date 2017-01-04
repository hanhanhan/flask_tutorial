import unittest
import time
from datetime import datetime
from app import create_app, db
from app.models import User, Anonymous, Role, Permission

class UserModelTestCase(unittest.TestCase):
    def test_roles_and_permissions(self):
        Role.insert_roles()
        u = User(email="jon@example.com", password="cat")
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS)
