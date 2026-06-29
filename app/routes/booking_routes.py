from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app.controllers.booking_controller import BookingController
from app.models import Court, Equipment, Booking
from datetime import date, datetime

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/book/<int:court_id>', methods=['GET'])
@login_required
def book(court_id):
    court = Court.query.get_or_404(court_id)
    equipments = Equipment.query.filter_by(status='available').all()
    today_str = date.today().strftime('%Y-%m-%d')
    return render_template('booking/book.html', court=court, equipments=equipments, today=today_str)

@booking_bp.route('/api/slots', methods=['GET'])
@login_required
def get_slots():
    court_id = request.args.get('court_id', type=int)
    date_str = request.args.get('date')
    
    if not court_id or not date_str:
        return jsonify({'error': 'Missing court_id or date'}), 400
        
    try:
        slots = BookingController.get_available_slots(court_id, date_str)
        return jsonify({'slots': slots})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/api/price-check', methods=['POST'])
@login_required
def price_check():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
        
    court_id = data.get('court_id')
    date_str = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    promo_code = data.get('promo_code')
    rentals = data.get('rentals', [])
    
    if not all([court_id, date_str, start_time is not None, end_time is not None]):
        return jsonify({'error': 'Missing booking parameters'}), 400
        
    pricing, err = BookingController.calculate_price(
        court_id=int(court_id),
        booking_date=date_str,
        start_time=int(start_time),
        end_time=int(end_time),
        promo_code_str=promo_code,
        rentals_data=rentals
    )
    
    if err:
        return jsonify({'error': err}), 400
        
    return jsonify(pricing)

@booking_bp.route('/book/<int:court_id>/confirm', methods=['POST'])
@login_required
def book_confirm(court_id):
    date_str = request.form.get('date')
    start_time = request.form.get('start_time', type=int)
    end_time = request.form.get('end_time', type=int)
    promo_code = request.form.get('promo_code')
    payment_method = request.form.get('payment_method', 'Cash')
    
    # Process rentals from form
    equipments = Equipment.query.filter_by(status='available').all()
    rentals_data = []
    for eq in equipments:
        qty = request.form.get(f'rental_qty_{eq.id}', type=int, default=0)
        if qty > 0:
            rentals_data.append({'equipment_id': eq.id, 'quantity': qty})
            
    success, res = BookingController.create_booking(
        user_id=current_user.id,
        court_id=court_id,
        booking_date=date_str,
        start_time=start_time,
        end_time=end_time,
        rentals_data=rentals_data,
        promo_code_str=promo_code,
        payment_method=payment_method
    )
    
    if success:
        flash("Booking confirmed successfully!", "success")
        return redirect(url_for('booking.receipt', booking_id=res.id))
    else:
        flash(f"Booking failed: {res}", "danger")
        return redirect(url_for('booking.book', court_id=court_id))

@booking_bp.route('/bookings/history')
@login_required
def history():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.date.desc(), Booking.start_time.desc()).all()
    return render_template('booking/history.html', bookings=bookings)

@booking_bp.route('/bookings/<int:booking_id>/receipt')
@login_required
def receipt(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and current_user.role not in ['admin', 'staff']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.dashboard'))
    return render_template('booking/receipt.html', booking=booking)

@booking_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    success, message = BookingController.cancel_booking(
        booking_id=booking_id,
        user_id=current_user.id,
        is_admin=(current_user.role in ['admin', 'staff'])
    )
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")
    return redirect(url_for('booking.history'))

# Git simulation edit: route_fix
