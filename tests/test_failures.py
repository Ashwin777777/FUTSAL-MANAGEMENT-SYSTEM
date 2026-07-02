import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date, timedelta
from app import create_app, db
from app.models import Court, User, Equipment, PromoCode
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    PEAK_START_HOUR = 16
    PEAK_END_HOUR = 22
    PEAK_MULTIPLIER = 1.25

class FailingBookingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed test data
        self.customer = User(username="fail_c", email="fail@test.com", password_hash="hash", role="customer")
        self.court = Court(name="Velocity Baneshwor", type="Indoor", turf_type="Rubberized", hourly_rate=1000.0)
        self.equipment = Equipment(name="Shoes", rental_price=200.0, stock=5, status="available")
        
        db.session.add_all([self.customer, self.court, self.equipment])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_peak_hour_price_assertion_mismatch(self):
        """
        Failing Test 1: Expects peak hour booking to be regular price.
        The actual pricing will apply a 25% peak multiplier, causing a mismatch.
        """
        from app.controllers.booking_controller import BookingController
        booking_date = date(2026, 7, 6) # Monday
        
        # Booking at 17:00 (peak hour)
        pricing, err = BookingController.calculate_price(
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=17,
            end_time=18
        )
        self.assertIsNone(err)
        
        # INTENTIONAL FAILURE: Expecting Rs. 1000.0, but actual is Rs. 1250.0
        self.assertEqual(pricing['court_cost'], 1000.0)

    def test_double_booking_success_expectation(self):
        """
        Failing Test 2: Asserts that booking a slot which is already booked succeeds.
        The backend will block it and return False, causing this test to fail.
        """
        from app.controllers.booking_controller import BookingController
        booking_date = date(2026, 7, 6)
        
        # 1. Create first booking: 10:00 to 11:00 (Succeeds)
        success1, res1 = BookingController.create_booking(
            user_id=self.customer.id,
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=10,
            end_time=11,
            payment_method="Cash"
        )
        self.assertTrue(success1)
        
        # 2. Try to book same slot (Should block it, but we assert it succeeds)
        # INTENTIONAL FAILURE: Expecting True, but actual is False
        success2, res2 = BookingController.create_booking(
            user_id=self.customer.id,
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=10,
            end_time=11,
            payment_method="Cash"
        )
        self.assertTrue(success2)

    def test_expired_promo_code_discount_expectation(self):
        """
        Failing Test 3: Tries to apply an expired promo code and expects a discount.
        The backend will correctly reject it (0.0 discount), causing this test to fail.
        """
        from app.controllers.booking_controller import BookingController
        # Create an expired promo code
        expired_promo = PromoCode(code="EXPIRED50", discount_percent=50, valid_until=date.today() - timedelta(days=5), active=True)
        db.session.add(expired_promo)
        db.session.commit()

        booking_date = date(2026, 7, 6) # Monday
        
        pricing, err = BookingController.calculate_price(
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=12,
            end_time=13,
            promo_code_str="EXPIRED50"
        )
        self.assertIsNone(err)
        
        # INTENTIONAL FAILURE: Expecting Rs. 500.0 discount, but actual is Rs. 0.0
        self.assertEqual(pricing['discount'], 500.0)

    def test_insufficient_equipment_stock_success_expectation(self):
        """
        Failing Test 4: Attempts to rent more equipment than available stock, expecting success.
        The backend will block it due to stock limits, causing this test to fail.
        """
        from app.controllers.booking_controller import BookingController
        booking_date = date(2026, 7, 6)
        
        # Attempt to rent 10 shoes (stock is only 5)
        # INTENTIONAL FAILURE: Expecting True, but actual is False
        success, res = BookingController.create_booking(
            user_id=self.customer.id,
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=12,
            end_time=13,
            rentals_data=[{'equipment_id': self.equipment.id, 'quantity': 10}],
            payment_method="Cash"
        )
        self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()
