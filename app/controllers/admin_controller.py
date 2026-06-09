from app import db
from app.models import User, Court, Booking, Equipment, Maintenance, Payment
from sqlalchemy import func
from datetime import datetime, date, timedelta

class AdminController:
    @staticmethod
    def get_analytics_data():
        """
        Gathers analytics for the admin dashboard.
        """
        total_bookings = Booking.query.filter(Booking.status != 'cancelled').count()
        
        # Calculate total revenue
        total_revenue = db.session.query(func.sum(Payment.amount)).filter(Payment.status == 'completed').scalar() or 0.0
        total_revenue = round(total_revenue, 2)
        
        active_courts = Court.query.filter_by(status='active').count()
        total_users = User.query.filter_by(role='customer').count()
        
        # Bookings by court
        court_stats = db.session.query(
            Court.name, 
            func.count(Booking.id)
        ).join(Booking).filter(Booking.status != 'cancelled').group_by(Court.name).all()
        
        court_labels = [stat[0] for stat in court_stats]
        court_counts = [stat[1] for stat in court_stats]
        
        # Last 7 days booking & revenue trend
        today = date.today()
        dates_list = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        date_labels = [d.strftime("%b %d") for d in dates_list]
        
        daily_bookings = []
        daily_revenue = []
        
        for d in dates_list:
            b_count = Booking.query.filter(Booking.date == d, Booking.status != 'cancelled').count()
            daily_bookings.append(b_count)
            
            rev = db.session.query(func.sum(Payment.amount))\
                .join(Booking)\
                .filter(Booking.date == d, Payment.status == 'completed')\
                .scalar() or 0.0
            daily_revenue.append(round(rev, 2))
            
        recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
        
        return {
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'active_courts': active_courts,
            'total_users': total_users,
            'court_labels': court_labels,
            'court_counts': court_counts,
            'date_labels': date_labels,
            'daily_bookings': daily_bookings,
            'daily_revenue': daily_revenue,
            'recent_bookings': recent_bookings
        }

    # Court Management
    @staticmethod
    def add_court(name, court_type, turf_type, hourly_rate, image_url=None):
        new_court = Court(
            name=name,
            type=court_type,
            turf_type=turf_type,
            hourly_rate=float(hourly_rate),
            image_url=image_url or '/static/images/default_court.jpg',
            status='active'
        )
        db.session.add(new_court)
        db.session.commit()
        return new_court

    @staticmethod
    def update_court(court_id, name, court_type, turf_type, hourly_rate, status, image_url=None):
        court = Court.query.get(court_id)
        if not court:
            return False, "Court not found"
        court.name = name
        court.type = court_type
        court.turf_type = turf_type
        court.hourly_rate = float(hourly_rate)
        court.status = status
        if image_url:
            court.image_url = image_url
        db.session.commit()
        return True, "Court updated successfully"

    # Equipment Management
    @staticmethod
    def add_equipment(name, rental_price, stock):
        new_eq = Equipment(
            name=name,
            rental_price=float(rental_price),
            stock=int(stock),
            status='available' if int(stock) > 0 else 'unavailable'
        )
        db.session.add(new_eq)
        db.session.commit()
        return new_eq

    @staticmethod
    def update_equipment(eq_id, name, rental_price, stock, status):
        eq = Equipment.query.get(eq_id)
        if not eq:
            return False, "Equipment not found"
        eq.name = name
        eq.rental_price = float(rental_price)
        eq.stock = int(stock)
        eq.status = status
        db.session.commit()
        return True, "Equipment updated successfully"

    # Maintenance Management
    @staticmethod
    def schedule_maintenance(court_id, maint_date, start_time, end_time, reason):
        if isinstance(maint_date, str):
            maint_date = datetime.strptime(maint_date, "%Y-%m-%d").date()
            
        # Check if there are active bookings in this period
        overlapping_bookings = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.date == maint_date,
            Booking.status != 'cancelled',
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).all()
        
        if overlapping_bookings:
            return False, f"Cannot schedule maintenance. There are {len(overlapping_bookings)} active booking(s) during this time."
            
        maint = Maintenance(
            court_id=court_id,
            date=maint_date,
            start_time=int(start_time),
            end_time=int(end_time),
            reason=reason
        )
        db.session.add(maint)
        db.session.commit()
        return True, "Maintenance scheduled successfully"

    @staticmethod
    def delete_maintenance(maint_id):
        maint = Maintenance.query.get(maint_id)
        if maint:
            db.session.delete(maint)
            db.session.commit()
            return True, "Maintenance window removed"
        return False, "Maintenance record not found"
        
    @staticmethod
    def update_payment_status(payment_id, status):
        payment = Payment.query.get(payment_id)
        if payment:
            payment.status = status
            db.session.commit()
            return True, "Payment status updated"
        return False, "Payment not found"
