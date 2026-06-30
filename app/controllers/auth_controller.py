from app import db, bcrypt
from app.models import User
from flask_login import login_user, logout_user
from flask import current_app

class AuthController:
    @staticmethod
    def register_user(username, email, password, phone=None, role='customer', admin_key=None):
        # Validate unique username and email
        if User.query.filter_by(username=username).first():
            return False, "Username already exists."
        if User.query.filter_by(email=email).first():
            return False, "Email already registered."
        
        # Admin validation
        if role == 'admin':
            expected_key = current_app.config.get('ADMIN_REGISTRATION_KEY', 'FUTSAL_ADMIN_2026')
            if admin_key != expected_key:
                return False, "Invalid Admin Registration Key."
        elif role == 'staff':
            # For simplicity, we can let them register if they have the admin key, or just default to customer
            expected_key = current_app.config.get('ADMIN_REGISTRATION_KEY', 'FUTSAL_ADMIN_2026')
            if admin_key != expected_key:
                return False, "Invalid Staff Registration Key."
        else:
            role = 'customer'
            
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_pw,
            phone=phone,
            role=role
        )
        
        db.session.add(new_user)
        db.session.commit()
        return True, "Registration successful! You can now log in."

    @staticmethod
    def login_user_check(username, password, remember=False):
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            return True, user
        return False, "Invalid username or password."

    @staticmethod
    def logout():
        logout_user()
        return True, "Logged out successfully."

# Git simulation edit: doc_auth
