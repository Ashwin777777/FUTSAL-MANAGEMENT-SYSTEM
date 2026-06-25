from app import create_app, db, bcrypt
from app.models import User, Court, Equipment, PromoCode, Announcement, Review, Booking, Payment, Rental
from datetime import date, timedelta, datetime

app = create_app()

def seed_database():
    # Parse connection details from config to automatically create database if it doesn't exist
    import pymysql
    from urllib.parse import urlparse
    
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    parsed = urlparse(db_uri)
    
    # Extract credentials
    username = parsed.username or 'root'
    password = parsed.password or ''
    host = parsed.hostname or 'localhost'
    port = parsed.port or 3306
    db_name = parsed.path.lstrip('/') or 'futsal_db'
    
    print(f"Connecting to MySQL server at {host}:{port}...")
    # Connect without database specified
    conn = pymysql.connect(host=host, port=port, user=username, password=password)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")
            print(f"Database '{db_name}' ensured (created or already exists).")
        conn.commit()
    except Exception as e:
        print(f"Warning: Could not auto-create database. Error: {e}")
    finally:
        conn.close()

    with app.app_context():
        # Create tables in MySQL
        db.create_all()
        
        # Check if database is already seeded
        if User.query.first():
            print("Database already seeded.")
            return
            
        print("Seeding database with Nepalese Futsal Centers...")
        
        # 1. Create Users
        admin = User(
            username="admin",
            email="admin@futsal.com.np",
            password_hash=bcrypt.generate_password_hash("admin123").decode('utf-8'),
            role="admin",
            phone="9851012345"
        )
        staff = User(
            username="staff",
            email="staff@futsal.com.np",
            password_hash=bcrypt.generate_password_hash("staff123").decode('utf-8'),
            role="staff",
            phone="9841098765"
        )
        customer = User(
            username="customer",
            email="customer@futsal.com.np",
            password_hash=bcrypt.generate_password_hash("customer123").decode('utf-8'),
            role="customer",
            phone="9801011122"
        )
        db.session.add_all([admin, staff, customer])
        db.session.flush() # Flush to get IDs
        
        # 2. Create Nepalese Courts
        court1 = Court(
            name="Velocity Arena (Baneshwor, Kathmandu)",
            type="Indoor",
            turf_type="Rubberized",
            hourly_rate=1500.0,  # Rs. 1500 per hour
            image_url="https://images.unsplash.com/photo-1575361204480-aadea25e6e68?w=500",
            status="active"
        )
        court2 = Court(
            name="Dhanwantari Futsal (Chabahil, Kathmandu)",
            type="Outdoor",
            turf_type="Artificial Turf",
            hourly_rate=1200.0,  # Rs. 1200 per hour
            image_url="https://images.unsplash.com/photo-1560272564-c83b66b1ad12?w=500",
            status="active"
        )
        court3 = Court(
            name="Lalitpur Futsal (Jhamsikhel, Lalitpur)",
            type="Indoor",
            turf_type="Hybrid",
            hourly_rate=1800.0,  # Rs. 1800 per hour
            image_url="https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=500",
            status="active"
        )
        db.session.add_all([court1, court2, court3])
        db.session.flush()
        
        # 3. Create Equipment (with Nepalese prices in Rs.)
        eq1 = Equipment(name="Premium Match Ball (Size 4)", rental_price=150.0, stock=10, status="available")
        eq2 = Equipment(name="Team Bibs (Set of 10 - Yellow/Blue)", rental_price=200.0, stock=5, status="available")
        eq3 = Equipment(name="Goalkeeper Gloves (Professional)", rental_price=100.0, stock=6, status="available")
        eq4 = Equipment(name="Futsal Shoes (Sizes 8-11)", rental_price=250.0, stock=12, status="available")
        db.session.add_all([eq1, eq2, eq3, eq4])
        
        # 4. Create Promo Codes
        promo1 = PromoCode(code="WELCOME10", discount_percent=10, valid_until=date.today() + timedelta(days=365), active=True)
        promo2 = PromoCode(code="WEEKENDPLAY", discount_percent=15, valid_until=date.today() + timedelta(days=365), active=True)
        promo3 = PromoCode(code="SAJHA15", discount_percent=15, valid_until=date.today() + timedelta(days=60), active=True)
        db.session.add_all([promo1, promo2, promo3])
        
        # 5. Create Announcements for Nepal
        ann1 = Announcement(
            title="Welcome to Futsal Hub Nepal!",
            content="Welcome to Kathmandu's premier futsal booking platform. Register now and book slots in Baneshwor, Chabahil, and Lalitpur!",
            important=False
        )
        ann2 = Announcement(
            title="Kathmandu Futsal Championship Registrations Open!",
            content="Registrations are now open for the Kathmandu Futsal Championship. Winners receive Rs. 1,00,000 cash prize! Register at the counter.",
            important=True
        )
        ann3 = Announcement(
            title="Weekend Special Offer!",
            content="Book any court in Jhamsikhel or Baneshwor on weekends and get 15% off with code: WEEKENDPLAY",
            important=False
        )
        db.session.add_all([ann1, ann2, ann3])
        
        # 6. Create Reviews
        rev1 = Review(user_id=customer.id, court_id=court1.id, rating=5, comment="Velocity Arena has the best rubberized court in Kathmandu. Excellent bounce and very safe for knees.")
        rev2 = Review(user_id=customer.id, court_id=court2.id, rating=4, comment="Dhanwantari is a classic outdoor turf. Great space, highly recommended for evening matches under the floodlights.")
        db.session.add_all([rev1, rev2])
        
        # 7. Add some historical bookings
        booking1 = Booking(
            user_id=customer.id,
            court_id=court1.id,
            date=date.today() - timedelta(days=2),
            start_time=18,
            end_time=20,
            base_price=3000.0,         # 2 hours at Rs. 1500
            discount_applied=300.0,    # 10% discount
            total_price=2850.0,        # Rs. 2700 court + Rs. 150 ball rental
            status="confirmed"
        )
        db.session.add(booking1)
        db.session.flush()
        
        rental1 = Rental(booking_id=booking1.id, equipment_id=eq1.id, quantity=1, price=150.0)
        db.session.add(rental1)
        
        payment1 = Payment(
            booking_id=booking1.id,
            amount=2850.0,
            payment_method="Wallet",
            transaction_id="TXN-NPR-E123",
            status="completed",
            payment_date=datetime.now() - timedelta(days=2)
        )
        db.session.add(payment1)
        
        db.session.commit()
        print("MySQL database seeded successfully with Nepalese Futsal data!")

if __name__ == "__main__":
    seed_database()

# Git simulation edit: nepal_seed
