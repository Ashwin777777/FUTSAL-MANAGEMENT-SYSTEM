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
    end_time = db.Column(db.Integer, nullable=False)    # 24-hour format, e.g., 15 for 3:00 PM
    base_price = db.Column(db.Float, nullable=False)
    discount_applied = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rentals = db.relationship('Rental', backref='booking', lazy=True, cascade="all, delete-orphan")
    payment = db.relationship('Payment', backref='booking', uselist=False, lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Booking {self.id} | Court {self.court_id} | {self.date} {self.start_time}:00-{self.end_time}:00>"

class Equipment(db.Model):
    __tablename__ = 'equipments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rental_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='available')  # available, unavailable

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'rental_price': self.rental_price,
            'stock': self.stock,
            'status': self.status
        }

    def __repr__(self):
        return f"<Equipment {self.name}>"

class Rental(db.Model):
    __tablename__ = 'rentals'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipments.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)  # Rate per unit at the time of booking
    
    # Relationships
    equipment = db.relationship('Equipment')

    def __repr__(self):
        return f"<Rental {self.quantity}x {self.equipment_id} for Booking {self.booking_id}>"

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # Cash, Card, Digital Wallet
    transaction_id = db.Column(db.String(100), unique=True, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, completed, refunded
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment {self.id} | Booking {self.booking_id} | {self.status}>"

class PromoCode(db.Model):
    __tablename__ = 'promo_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    discount_percent = db.Column(db.Integer, nullable=False)  # e.g., 10 for 10%
    valid_until = db.Column(db.Date, nullable=False)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<PromoCode {self.code} (-{self.discount_percent}%)>"

class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    
    id = db.Column(db.Integer, primary_key=True)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Integer, nullable=False)  # 24-hour format
    end_time = db.Column(db.Integer, nullable=False)    # 24-hour format
    reason = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Maintenance Court {self.court_id} on {self.date}>"

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Review {self.rating}* by User {self.user_id} for Court {self.court_id}>"

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    important = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Announcement {self.title}>"

# Git simulation edit: model_to_dict
