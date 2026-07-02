import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    BCRYPT_LOG_ROUNDS = 4  # Speed up password hashing for tests
    WTF_CSRF_ENABLED = False

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_registration(self):
        # 1. Test standard customer registration
        from app.controllers.auth_controller import AuthController
        success, message = AuthController.register_user(
            username="test_customer",
            email="customer@test.com",
            password="password123",
            phone="9876543210",
            role="customer"
        )
        self.assertTrue(success)
        self.assertEqual(message, "Registration successful! You can now log in.")

        # Verify user exists in database
        user = User.query.filter_by(username="test_customer").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, "customer")

    def test_admin_registration_key_protection(self):
        from app.controllers.auth_controller import AuthController
        # 1. Register admin with wrong key (should fail)
        success, message = AuthController.register_user(
            username="malicious_admin",
            email="malicious@test.com",
            password="password123",
            role="admin",
            admin_key="WRONG_KEY"
        )
        self.assertFalse(success)
        self.assertEqual(message, "Invalid Admin Registration Key.")

        # 2. Register admin with correct key (should succeed)
        success, message = AuthController.register_user(
            username="real_admin",
            email="real@test.com",
            password="password123",
            role="admin",
            admin_key="FUTSAL_ADMIN_2026"
        )
        self.assertTrue(success)

    def test_duplicate_user_registration(self):
        from app.controllers.auth_controller import AuthController
        # Register first user
        AuthController.register_user("user1", "user1@test.com", "password", role="customer")

        # Duplicate username
        success, message = AuthController.register_user("user1", "user2@test.com", "password", role="customer")
        self.assertFalse(success)
        self.assertEqual(message, "Username already exists.")

        # Duplicate email
        success, message = AuthController.register_user("user2", "user1@test.com", "password", role="customer")
        self.assertFalse(success)
        self.assertEqual(message, "Email already registered.")

    def test_user_login(self):
        from app.controllers.auth_controller import AuthController
        # Register a test user
        AuthController.register_user("login_user", "login@test.com", "pass123", role="customer")

        # Login with wrong credentials
        success, res = AuthController.login_user_check("login_user", "wrongpass")
        self.assertFalse(success)
        self.assertEqual(res, "Invalid username or password.")

        # Login with correct credentials
        # Note: login_user_check calls flask_login.login_user which requires request context.
        # We can test via the client to simulate a full login request.
        response = self.client.post('/login', data={
            'username': 'login_user',
            'password': 'pass123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back, login_user!", response.data)

if __name__ == '__main__':
    unittest.main()
