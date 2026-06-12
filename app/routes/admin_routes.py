from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.controllers.admin_controller import AdminController
from app.models import Court, Booking, Equipment, Maintenance, Payment
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def restrict_to_admin_or_staff():
    """
    Secures all routes in this blueprint so only admins and staff can access them.
    """
    if current_user.role not in ['admin', 'staff']:
        flash("Access denied. Authorized personnel only.", "danger")
        return redirect(url_for('main.dashboard'))

@admin_bp.route('/dashboard')
def dashboard():
    analytics = AdminController.get_analytics_data()
    return render_template('admin/dashboard.html', analytics=analytics)

# Court Management
@admin_bp.route('/courts', methods=['GET', 'POST'])
def courts():
    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name')
        court_type = request.form.get('type')
        turf_type = request.form.get('turf_type')
        hourly_rate = request.form.get('hourly_rate')
        image_url = request.form.get('image_url')
        
        if action == 'add':
            AdminController.add_court(name, court_type, turf_type, hourly_rate, image_url)
            flash(f"Court '{name}' added successfully!", "success")
        elif action == 'edit':
            court_id = request.form.get('court_id', type=int)
            status = request.form.get('status')
            AdminController.update_court(court_id, name, court_type, turf_type, hourly_rate, status, image_url)
            flash(f"Court '{name}' updated successfully!", "success")
            
        return redirect(url_for('admin.courts'))
        
    all_courts = Court.query.all()
    return render_template('admin/courts.html', courts=all_courts)

# Booking & Payment Management
@admin_bp.route('/bookings', methods=['GET'])
def bookings():
    all_bookings = Booking.query.order_by(Booking.date.desc(), Booking.start_time.desc()).all()
    return render_template('admin/bookings.html', bookings=all_bookings)

@admin_bp.route('/payments/<int:payment_id>/status', methods=['POST'])
def update_payment(payment_id):
    status = request.form.get('status')
    success, msg = AdminController.update_payment_status(payment_id, status)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for('admin.bookings'))

# Equipment Inventory Management
@admin_bp.route('/equipment', methods=['GET', 'POST'])
def equipment():
    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name')
        rental_price = request.form.get('rental_price')
        stock = request.form.get('stock')
        
        if action == 'add':
            AdminController.add_equipment(name, rental_price, stock)
            flash(f"Equipment '{name}' added successfully!", "success")
        elif action == 'edit':
            eq_id = request.form.get('equipment_id', type=int)
            status = request.form.get('status')
            AdminController.update_equipment(eq_id, name, rental_price, stock, status)
            flash(f"Equipment '{name}' updated successfully!", "success")
            
        return redirect(url_for('admin.equipment'))
        
    all_equipment = Equipment.query.all()
    return render_template('admin/equipment.html', equipment=all_equipment)

# Maintenance Scheduling
@admin_bp.route('/maintenance', methods=['GET', 'POST'])
def maintenance():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            court_id = request.form.get('court_id', type=int)
            maint_date = request.form.get('date')
            start_time = request.form.get('start_time', type=int)
            end_time = request.form.get('end_time', type=int)
            reason = request.form.get('reason')
            
            success, msg = AdminController.schedule_maintenance(
                court_id, maint_date, start_time, end_time, reason
            )
            if success:
                flash(msg, "success")
            else:
                flash(msg, "danger")
        elif action == 'delete':
            maint_id = request.form.get('maintenance_id', type=int)
            success, msg = AdminController.delete_maintenance(maint_id)
            if success:
                flash(msg, "success")
            else:
                flash(msg, "danger")
                
        return redirect(url_for('admin.maintenance'))
        
    all_maintenance = Maintenance.query.order_by(Maintenance.date.desc()).all()
    courts = Court.query.filter_by(status='active').all()
    return render_template('admin/maintenance.html', maintenance=all_maintenance, courts=courts)
