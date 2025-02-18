"""Authentication routes."""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from app.models.user import User
from app.extensions import limiter
from app.models.address import Address
from app.models.order import Order
from app.extensions import db, bcrypt, mail
from datetime import datetime
from flask_mail import Message
import jwt
from time import time
import os

from app.auth import bp

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            print('next page: ',next_page)
            # Only redirect to next_page if it exists and is a relative path (for security)
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('shop.index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('shop.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('auth.register'))
        
        user = User(username=username, email=email)
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        if email != current_user.email and User.query.filter_by(email=email).first():
            flash('Email already in use', 'error')
            return redirect(url_for('auth.profile'))
        
        current_user.username = username
        current_user.email = email
        
        try:
            db.session.commit()
            flash('Profile updated successfully', 'success')
        except:
            db.session.rollback()
            flash('An error occurred', 'error')
        
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html')

@bp.route('/change_password', methods=['GET', 'POST'])
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

@bp.route('/reset_password_request', methods=['GET', 'POST'])
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

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
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

@bp.route('/address/add', methods=['POST'])
@login_required
def add_address():
    street = request.form.get('street')
    city = request.form.get('city')
    state = request.form.get('state')
    zip_code = request.form.get('zip_code')
    country = request.form.get('country')
    name = request.form.get('name')
    phone = request.form.get('phone')
    is_default = request.form.get('is_default', False)
    
    if is_default:
        # Set all other addresses as non-default
        Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
    
    address = Address(
        user_id=current_user.id,
        name=name,
        phone=phone,
        street=street,
        city=city,
        state=state,
        zip_code=zip_code,
        country=country,
        is_default=is_default
    )
    
    try:
        db.session.add(address)
        db.session.commit()
        flash('Address added successfully!', 'success')
    except:
        db.session.rollback()
        flash('An error occurred while adding the address.', 'error')
    
    return redirect(url_for('auth.profile'))

@bp.route('/address/delete/<int:address_id>', methods=['POST'])
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

@bp.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_created.desc()).all()
    return render_template('auth/orders.html', orders=orders)
