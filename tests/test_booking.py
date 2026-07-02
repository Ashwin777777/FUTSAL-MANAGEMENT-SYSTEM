import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date, timedelta
from app import create_app, db
from app.models import Court, Equipment, PromoCode, User, Booking
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    PEAK_START_HOUR = 16
    PEAK_END_HOUR = 22
    PEAK_MULTIPLIER = 1.25
    WEEKEND_MULTIPLIER = 1.15

class BookingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed initial data for testing
        self.customer = User(username="test_c", email="c@test.com", password_hash="hash", role="customer")
        self.court = Court(name="Velocity Baneshwor", type="Indoor", turf_type="Rubberized", hourly_rate=1000.0)
        self.equipment = Equipment(name="Bibs", rental_price=100.0, stock=5, status="available")
        self.promo = PromoCode(code="WELCOME10", discount_percent=10, valid_until=date.today() + timedelta(days=10), active=True)
        
        db.session.add_all([self.customer, self.court, self.equipment, self.promo])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_price_calculation_regular_hour(self):
        from app.controllers.booking_controller import BookingController
        # Weekday (e.g. Monday is 0, let's pick a guaranteed weekday: 2026-07-06 is a Monday)
        booking_date = date(2026, 7, 6) # Monday
        
        # 12:00 to 13:00 (1 hour, regular weekday hour)
        pricing, err = BookingController.calculate_price(
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=12,
            end_time=13
        )
        self.assertNil(err)
        # Expected: 1000.0
        self.assertEqual(pricing['court_cost'], 1000.0)
        self.assertEqual(pricing['total'], 1000.0)

    def test_price_calculation_peak_hour(self):
        from app.controllers.booking_controller import BookingController
        booking_date = date(2026, 7, 6) # Monday
        
        # 17:00 to 18:00 (1 peak hour on weekday)
        # Peak multiplier is 1.25 -> 1000 * 1.25 = 1250.0
        pricing, err = BookingController.calculate_price(
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=17,
            end_time=18
        )
        self.assertNil(err)
        self.assertEqual(pricing['court_cost'], 1250.0)

    def test_price_calculation_weekend_and_promo(self):
        from app.controllers.booking_controller import BookingController
        booking_date = date(2026, 7, 5) # Sunday (Weekend)
        
        # 12:00 to 13:00 (1 hour, weekend regular hour)
        # Weekend multiplier is 1.15 -> 1000 * 1.15 = 1150.0
        # Promo code: WELCOME10 gives 10% off the court cost -> 1150.0 * 0.10 = 115.0 discount
        # Total court cost = 1150.0 - 115.0 = 1035.0
        pricing, err = BookingController.calculate_price(
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=12,
            end_time=13,
            promo_code_str="WELCOME10"
        )
        self.assertNil(err)
        self.assertEqual(pricing['court_cost'], 1150.0)
        self.assertEqual(pricing['discount'], 115.0)
        self.assertEqual(pricing['total'], 1035.0)

    def test_double_booking_prevention(self):
        from app.controllers.booking_controller import BookingController
        booking_date = date(2026, 7, 6)
        
        # 1. Create first booking: 10:00 to 11:00
        success, res = BookingController.create_booking(
            user_id=self.customer.id,
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=10,
            end_time=11,
            payment_method="Cash"
        )
        self.assertTrue(success)
        
        # 2. Try to book the same slot (10:00 to 11:00) -> should fail
        success2, res2 = BookingController.create_booking(
            user_id=self.customer.id,
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=10,
            end_time=11,
            payment_method="Cash"
        )
        self.assertFalse(success2)
        self.assertIn("not available", res2)

        # 3. Try to book overlapping slot (9:00 to 11:00) -> should fail
        success3, res3 = BookingController.create_booking(
            user_id=self.customer.id,
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=9,
            end_time=11,
            payment_method="Cash"
        )
        self.assertFalse(success3)
        self.assertIn("not available", res3)

    def test_equipment_stock_deduction_and_cancellation_return(self):
        from app.controllers.booking_controller import BookingController
        booking_date = date(2026, 7, 6)
        
        # Initial stock check
        self.assertEqual(self.equipment.stock, 5)

        # Book with 2 Bibs
        success, res = BookingController.create_booking(
            user_id=self.customer.id,
            court_id=self.court.id,
            booking_date=booking_date,
            start_time=14,
            end_time=15,
            rentals_data=[{'equipment_id': self.equipment.id, 'quantity': 2}],
            payment_method="Cash"
        )
        self.assertTrue(success)
        
        # Verify stock deducted
        db.session.refresh(self.equipment)
        self.assertEqual(self.equipment.stock, 3)

        # Cancel booking
        success_cancel, msg_cancel = BookingController.cancel_booking(
            booking_id=res.id,
            user_id=self.customer.id,
            is_admin=True # Bypass cancellation time-limit checks for test
        )
        self.assertTrue(success_cancel)

        # Verify stock returned
        db.session.refresh(self.equipment)
        self.assertEqual(self.equipment.stock, 5)

    def assertNil(self, val):
        self.assertIsNone(val)

if __name__ == '__main__':
    unittest.main()
