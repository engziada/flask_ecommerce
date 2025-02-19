"""Authentication routes."""
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user, login_user, logout_user
from app.models.user import User
from app.models.address import Address
from app.utils.city_mapping import BostaCityMapping
from app.extensions import db, limiter, bcrypt, mail
from datetime import datetime
from flask_mail import Message
import jwt
from time import time
import os
import random
import string
from flask import abort
from urllib.parse import urlparse
from app.auth import bp as auth

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
            
        if not user.is_active():
            if user.status == 'suspended':
                flash('Your account has been suspended. Please contact support.', 'error')
            else:
                flash('Your account has been cancelled.', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
        
        user = User(email=email)
        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name
        user.date_registered = datetime.utcnow()
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during registration: {str(e)}")
            flash('An error occurred during registration', 'error')
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page."""
    if request.method == 'POST':
        if current_user.status != 'active':
            flash('Your account is not active. Please contact support.', 'error')
            return redirect(url_for('auth.profile'))
            
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        
        if first_name:
            current_user.first_name = first_name
        if last_name:
            current_user.last_name = last_name
        if phone:
            current_user.phone = phone
            
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')
            
    # Get user's addresses
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    return render_template('auth/profile.html', 
                         user=current_user, 
                         addresses=addresses,
                         bosta_cities=BostaCityMapping.CITY_MAPPING)

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not bcrypt.check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('auth.change_password'))
        
        current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        
        try:
            db.session.commit()
            flash('Password changed successfully', 'success')
            return redirect(url_for('auth.profile'))
        except:
            db.session.rollback()
            flash('An error occurred', 'error')
            return redirect(url_for('auth.change_password'))
    
    return render_template('auth/change_password.html')

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = jwt.encode(
                {'reset_password': user.id, 'exp': time() + 600},
                os.environ.get('SECRET_KEY', 'dev'),
                algorithm='HS256'
            )
            
            msg = Message('Password Reset Request',
                        sender='noreply@flaskshop.com',
                        recipients=[user.email])
            msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_password', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
            mail.send(msg)
            flash('Check your email for the instructions to reset your password', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('Email address not found', 'error')
    
    return render_template('auth/reset_password_request.html')

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    try:
        id = jwt.decode(token, os.environ.get('SECRET_KEY', 'dev'), algorithms=['HS256'])['reset_password']
        user = User.query.get(id)
        
        if not user:
            flash('Invalid reset token', 'error')
            return redirect(url_for('main.index'))
    except:
        flash('Invalid or expired reset token', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        password2 = request.form.get('password2')
        
        if not password or not password2:
            flash('Please fill out all fields', 'error')
            return render_template('auth/reset_password.html')
            
        if password != password2:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html')
            
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'error')
            return render_template('auth/reset_password.html')
        
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.commit()
        flash('Your password has been reset. You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html')

@auth.route('/delete_profile', methods=['POST'])
@login_required
def delete_profile():
    try:
        current_user.cancel_profile()
        db.session.commit()
        logout_user()
        flash('Your profile has been successfully cancelled.', 'success')
        return redirect(url_for('main.index'))
    except Exception as e:
        current_app.logger.error(f"Error cancelling profile: {str(e)}")
        db.session.rollback()
        flash('An error occurred while cancelling your profile', 'error')
        return redirect(url_for('auth.profile'))

@auth.route('/add_address', methods=['POST'])
@login_required
def add_address():
    """Add a new address for the current user."""
    street = request.form.get('street')
    city = request.form.get('city')
    district = request.form.get('district')
    building_number = request.form.get('building_number')
    floor = request.form.get('floor')
    apartment = request.form.get('apartment')
    name = request.form.get('name')
    phone = request.form.get('phone')
    is_default = request.form.get('is_default') == 'true'
    
    # Validate required fields
    if not all([street, city, name, phone]):
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('auth.profile'))
    
    # Validate city against Bosta city list
    if city not in BostaCityMapping.CITY_MAPPING:
        flash('Please select a valid city from the list.', 'error')
        return redirect(url_for('auth.profile'))
    
    if is_default:
        # Set all other addresses as non-default
        Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
    
    address = Address(
        user_id=current_user.id,
        name=name,
        phone=phone,
        street=street,
        building_number=building_number,
        floor=floor,
        apartment=apartment,
        city=city,
        district=district,
        is_default=is_default
    )
    
    try:
        db.session.add(address)
        db.session.commit()
        flash('Address added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while adding the address.', 'error')
        current_app.logger.error(f"Error adding address: {str(e)}")
    
    return redirect(url_for('auth.profile'))

@auth.route('/address/delete/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    address = Address.query.get_or_404(address_id)
    
    if address.user_id != current_user.id:
        flash('You are not authorized to delete this address.', 'error')
        return redirect(url_for('auth.profile'))
    
    try:
        db.session.delete(address)
        db.session.commit()
        flash('Address deleted successfully!', 'success')
    except:
        db.session.rollback()
        flash('An error occurred while deleting the address.', 'error')
    
    return redirect(url_for('auth.profile'))

@auth.route('/orders')
@login_required
def orders():
    from app.models.order import Order
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_created.desc()).all()
    return render_template('auth/orders.html', orders=orders)

@auth.route('/admin/suspend_user/<int:user_id>', methods=['POST'])
@login_required
def suspend_user(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    try:
        user.suspend_profile()
        db.session.commit()
        # Send email to user about suspension
        send_suspension_email(user)
        flash(f'User {user.username} has been suspended.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error suspending user: {str(e)}")
        db.session.rollback()
        flash('An error occurred while suspending the user', 'error')
    
    return redirect(url_for('admin.users'))

@auth.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    if not current_user.is_admin:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    try:
        # Generate random password
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        user.set_password(new_password)
        db.session.commit()
        
        # Send email with new password
        send_password_reset_email(user, new_password)
        flash(f'Password reset for user {user.username}. Email sent.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error resetting password: {str(e)}")
        db.session.rollback()
        flash('An error occurred while resetting the password', 'error')
    
    return redirect(url_for('admin.users'))

def send_suspension_email(user):
    msg = Message(
        'Account Suspended',
        recipients=[user.email]
    )
    msg.body = f'''Dear {user.username},

Your account has been suspended by an administrator.
If you believe this is an error, please contact support.

Best regards,
The Team'''
    mail.send(msg)

def send_password_reset_email(user, new_password):
    msg = Message(
        'Password Reset by Administrator',
        recipients=[user.email]
    )
    msg.body = f'''Dear {user.username},

Your password has been reset by an administrator.
Your new password is: {new_password}

Please change this password after logging in.

Best regards,
The Team'''
    mail.send(msg)
