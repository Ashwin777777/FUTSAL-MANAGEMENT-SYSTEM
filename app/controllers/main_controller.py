from app import db, bcrypt
from app.models import Announcement, Review, User, Court
from datetime import datetime

class MainController:
    @staticmethod
    def get_homepage_data():
        """
        Retrieves announcements and top reviews for the landing page.
        """
        announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
        recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(3).all()
        featured_courts = Court.query.filter_by(status='active').limit(3).all()
        return {
            'announcements': announcements,
            'reviews': recent_reviews,
            'featured_courts': featured_courts
        }

    @staticmethod
    def update_profile(user_id, username, email, phone, current_password=None, new_password=None):
        user = User.query.get(user_id)
        if not user:
            return False, "User not found."
            
        # Check username and email uniqueness
        existing_user = User.query.filter(User.username == username, User.id != user_id).first()
        if existing_user:
            return False, "Username is already taken."
            
        existing_email = User.query.filter(User.email == email, User.id != user_id).first()
        if existing_email:
            return False, "Email is already registered by another user."
            
        user.username = username
        user.email = email
        user.phone = phone
        
        # Change password if requested
        if current_password and new_password:
            if not bcrypt.check_password_hash(user.password_hash, current_password):
                return False, "Incorrect current password."
            user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            
        db.session.commit()
        return True, "Profile updated successfully."

    @staticmethod
    def add_review(user_id, court_id, rating, comment):
        if not (1 <= int(rating) <= 5):
            return False, "Rating must be between 1 and 5."
            
        review = Review(
            user_id=user_id,
            court_id=int(court_id),
            rating=int(rating),
            comment=comment
        )
        db.session.add(review)
        db.session.commit()
        return True, "Thank you for your feedback!"

# Git simulation edit: doc_main
