from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.controllers.main_controller import MainController
from app.models import Court, Booking

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    data = MainController.get_homepage_data()
    return render_template('index.html', data=data)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # If admin/staff logs in, redirect to admin dashboard
    if current_user.role in ['admin', 'staff']:
        return redirect(url_for('admin.dashboard'))
        
    # Get user's bookings
    recent_bookings = Booking.query.filter_by(user_id=current_user.id)\
        .order_by(Booking.date.desc(), Booking.start_time.desc())\
        .limit(3).all()
        
    all_courts = Court.query.filter_by(status='active').all()
    
    return render_template('dashboard.html', bookings=recent_bookings, courts=all_courts)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        success, msg = MainController.update_profile(
            user_id=current_user.id,
            username=username,
            email=email,
            phone=phone,
            current_password=current_password if current_password else None,
            new_password=new_password if new_password else None
        )
        
        if success:
            flash(msg, 'success')
        else:
            flash(msg, 'danger')
            
        return redirect(url_for('main.profile'))
        
    return render_template('profile.html')

@main_bp.route('/court/<int:court_id>/review', methods=['POST'])
@login_required
def submit_review(court_id):
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    success, msg = MainController.add_review(
        user_id=current_user.id,
        court_id=court_id,
        rating=rating,
        comment=comment
    )
    
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
        
    return redirect(request.referrer or url_for('main.dashboard'))
