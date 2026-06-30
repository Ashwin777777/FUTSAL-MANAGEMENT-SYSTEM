from datetime import datetime, date
from app import db
from app.models import Booking, Court, Equipment, Rental, Payment, PromoCode, Maintenance
from flask import current_app

class BookingController:
    @staticmethod
    def get_available_slots(court_id, booking_date):
        """
        Returns a list of time slots from 6 AM to 11 PM (23:00) with availability status.
        Status can be: 'available', 'booked', 'maintenance'
        """
        if isinstance(booking_date, str):
            booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
            
        # Get all bookings for this court on this date
        bookings = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.date == booking_date,
            Booking.status != 'cancelled'
        ).all()
        
        # Get all maintenance windows for this court on this date
        maintenances = Maintenance.query.filter(
            Maintenance.court_id == court_id,
            Maintenance.date == booking_date
        ).all()
        
        slots = []
        for hour in range(6, 23):  # 6 AM to 11 PM
            status = 'available'
            booking_info = None
            
            # Check maintenance
            for maint in maintenances:
                if maint.start_time <= hour < maint.end_time:
                    status = 'maintenance'
                    booking_info = f"Maintenance: {maint.reason}"
                    break
            
            # Check bookings if not in maintenance
            if status == 'available':
                for b in bookings:
                    if b.start_time <= hour < b.end_time:
                        status = 'booked'
                        booking_info = "Booked"
                        break
            
            # Check peak hour
            is_peak = current_app.config['PEAK_START_HOUR'] <= hour < current_app.config['PEAK_END_HOUR']
            
            slots.append({
                'hour': hour,
                'time_str': f"{hour:02d}:00 - {hour+1:02d}:00",
                'status': status,
                'info': booking_info,
                'is_peak': is_peak
            })
            
        return slots

    @staticmethod
    def calculate_price(court_id, booking_date, start_time, end_time, promo_code_str=None, rentals_data=None):
        """
        Calculates the pricing breakdown for a booking.
        rentals_data: list of dicts with {'equipment_id': id, 'quantity': qty}
        """
        court = Court.query.get(court_id)
        if not court:
            return None, "Court not found"
            
        if isinstance(booking_date, str):
            booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
            
        hours = end_time - start_time
        if hours <= 0:
            return None, "Invalid time duration"
            
        # Calculate base price considering peak hours and weekends
        base_rate = court.hourly_rate
        court_cost = 0.0
        
        is_weekend = booking_date.weekday() in [5, 6]  # 5 is Saturday, 6 is Sunday
        weekend_mult = current_app.config.get('WEEKEND_MULTIPLIER', 1.15)
        peak_mult = current_app.config.get('PEAK_MULTIPLIER', 1.25)
        peak_start = current_app.config.get('PEAK_START_HOUR', 16)
        peak_end = current_app.config.get('PEAK_END_HOUR', 22)
        
        hourly_breakdown = []
        for hour in range(start_time, end_time):
            rate = base_rate
            is_peak = peak_start <= hour < peak_end
            
            if is_peak:
                rate *= peak_mult
            if is_weekend:
                rate *= weekend_mult
                
            court_cost += rate
            hourly_breakdown.append({
                'hour': hour,
                'time_str': f"{hour:02d}:00 - {hour+1:02d}:00",
                'rate': round(rate, 2),
                'is_peak': is_peak,
                'is_weekend': is_weekend
            })
            
        court_cost = round(court_cost, 2)
        
        # Calculate rentals
        rental_cost = 0.0
        rental_breakdown = []
        if rentals_data:
            for item in rentals_data:
                eq_id = int(item['equipment_id'])
                qty = int(item['quantity'])
                if qty <= 0:
                    continue
                eq = Equipment.query.get(eq_id)
                if eq and eq.status == 'available':
                    cost = eq.rental_price * qty
                    rental_cost += cost
                    rental_breakdown.append({
                        'equipment_id': eq.id,
                        'name': eq.name,
                        'qty': qty,
                        'unit_price': eq.rental_price,
                        'total': round(cost, 2)
                    })
                    
        # Apply promo code
        discount = 0.0
        promo = None
        if promo_code_str:
            promo = PromoCode.query.filter_by(code=promo_code_str.upper(), active=True).first()
            if promo and promo.valid_until >= date.today():
                # Apply discount to the court cost only (or subtotal, let's do court cost)
                discount = round((court_cost * (promo.discount_percent / 100.0)), 2)
            else:
                promo = None
                
        subtotal = court_cost + rental_cost
        total = round(subtotal - discount, 2)
        if total < 0:
            total = 0.0
            
        return {
            'court_name': court.name,
            'hourly_rate': base_rate,
            'hours': hours,
            'hourly_breakdown': hourly_breakdown,
            'court_cost': court_cost,
            'rental_cost': rental_cost,
            'rental_breakdown': rental_breakdown,
            'promo_code': promo.code if promo else None,
            'discount_percent': promo.discount_percent if promo else 0,
            'discount': discount,
            'subtotal': subtotal,
            'total': total
        }, None

    @staticmethod
    def create_booking(user_id, court_id, booking_date, start_time, end_time, rentals_data=None, promo_code_str=None, payment_method='Cash'):
        """
        Creates a booking after verifying availability.
        """
        if isinstance(booking_date, str):
            booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
            
        # 1. Double Booking and Maintenance validation
        slots = BookingController.get_available_slots(court_id, booking_date)
        for slot in slots:
            if start_time <= slot['hour'] < end_time:
                if slot['status'] != 'available':
                    return False, f"Time slot {slot['time_str']} is not available ({slot['status']})."
                    
        # 2. Calculate pricing
        pricing, err = BookingController.calculate_price(court_id, booking_date, start_time, end_time, promo_code_str, rentals_data)
        if err:
            return False, err
            
        # 3. Verify rental stock
        if rentals_data:
            for item in rentals_data:
                eq_id = int(item['equipment_id'])
                qty = int(item['quantity'])
                if qty <= 0:
                    continue
                eq = Equipment.query.get(eq_id)
                if not eq or eq.stock < qty:
                    return False, f"Insufficient stock for {eq.name if eq else 'Equipment'}. Available: {eq.stock if eq else 0}."

        # 4. Create Booking
        new_booking = Booking(
            user_id=user_id,
            court_id=court_id,
            date=booking_date,
            start_time=start_time,
            end_time=end_time,
            base_price=pricing['court_cost'],
            discount_applied=pricing['discount'],
            total_price=pricing['total'],
            status='confirmed'  # Auto-confirm for simple app flow (or 'pending')
        )
        db.session.add(new_booking)
        db.session.flush()  # To get new_booking.id
        
        # 5. Create rentals and deduct stock
        if rentals_data:
            for item in rentals_data:
                eq_id = int(item['equipment_id'])
                qty = int(item['quantity'])
                if qty <= 0:
                    continue
                eq = Equipment.query.get(eq_id)
                rental = Rental(
                    booking_id=new_booking.id,
                    equipment_id=eq.id,
                    quantity=qty,
                    price=eq.rental_price
                )
                db.session.add(rental)
                eq.stock -= qty  # Deduct stock
                
        # 6. Create Payment Record
        import uuid
        tx_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        payment = Payment(
            booking_id=new_booking.id,
            amount=pricing['total'],
            payment_method=payment_method,
            transaction_id=tx_id if payment_method != 'Cash' else None,
            status='completed' if payment_method != 'Cash' else 'pending'
        )
        db.session.add(payment)
        
        db.session.commit()
        return True, new_booking

    @staticmethod
    def cancel_booking(booking_id, user_id, is_admin=False):
        booking = Booking.query.get(booking_id)
        if not booking:
            return False, "Booking not found."
            
        if not is_admin and booking.user_id != user_id:
            return False, "Unauthorized action."
            
        if booking.status == 'cancelled':
            return False, "Booking is already cancelled."
            
        # Check grace period for customers (e.g., must cancel at least 6 hours before)
        if not is_admin:
            booking_datetime = datetime.combine(booking.date, datetime.min.time().replace(hour=booking.start_time))
            time_diff = booking_datetime - datetime.now()
            if time_diff.total_seconds() < 6 * 3600:  # 6 hours
                return False, "Bookings can only be cancelled up to 6 hours before the start time."
                
        # Return equipment to stock
        for rental in booking.rentals:
            eq = Equipment.query.get(rental.equipment_id)
            if eq:
                eq.stock += rental.quantity
                
        booking.status = 'cancelled'
        if booking.payment:
            booking.payment.status = 'refunded'
            
        db.session.commit()
        return True, "Booking cancelled successfully."

# Git simulation edit: doc_book
