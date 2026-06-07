from datetime import datetime
from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # admin, staff, customer
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='customer', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='author', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

class Court(db.Model):
    __tablename__ = 'courts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # Indoor, Outdoor
    turf_type = db.Column(db.String(50), nullable=False)  # Rubberized, Artificial Turf, Hybrid
    hourly_rate = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')  # active, inactive
    image_url = db.Column(db.String(255), nullable=True)
    
    # Relationships
    bookings = db.relationship('Booking', backref='court', lazy=True)
    maintenance = db.relationship('Maintenance', backref='court', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='court', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'turf_type': self.turf_type,
            'hourly_rate': self.hourly_rate,
            'status': self.status,
            'image_url': self.image_url
        }

    def __repr__(self):
        return f"<Court {self.name}>"

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Integer, nullable=False)  # 24-hour format, e.g., 14 for 2:00 PM
