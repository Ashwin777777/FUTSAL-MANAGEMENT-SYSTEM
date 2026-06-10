from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.controllers.auth_controller import AuthController
from flask_login import current_user, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        role = request.form.get('role', 'customer')
        admin_key = request.form.get('admin_key')
        
        success, message = AuthController.register_user(
            username=username,
            email=email,
            password=password,
            phone=phone,
            role=role,
            admin_key=admin_key
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'danger')
            
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        success, res = AuthController.login_user_check(username, password, remember)
        if success:
            flash(f"Welcome back, {res.username}!", 'success')
            next_page = request.args.get('next')
            if res.role in ['admin', 'staff']:
                return redirect(next_page or url_for('admin.dashboard'))
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash(res, 'danger')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    AuthController.logout()
    flash("You have been logged out.", 'info')
    return redirect(url_for('main.index'))
