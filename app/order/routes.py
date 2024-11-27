from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app.models.order import Order, OrderItem
from app.models.cart import Cart
from app.models.address import Address
from app.extensions import db
from app.order import bp
from datetime import datetime

@bp.route('/')
@login_required
def orders():
    """Display user's orders"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_created.desc()).all()
    return render_template('order/orders.html', orders=orders)

@bp.route('/checkout')
@login_required
def checkout():
    """Checkout page"""
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.cart'))
    
    # Calculate cart totals
    subtotal = sum(item.subtotal for item in cart_items)  # Using the subtotal property
    shipping_cost = 10.00  # Fixed shipping cost, you can modify this based on your needs
    
    # Apply any discounts from session
    discount_percent = session.get('discount', 0)
    discount_amount = (subtotal * discount_percent / 100) if discount_percent > 0 else 0
    
    # Calculate final total
    total = subtotal + shipping_cost - discount_amount
    
    # Get user addresses
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    return render_template('order/checkout.html',
                         cart_items=cart_items,
                         addresses=addresses,
                         subtotal=subtotal,
                         shipping_cost=shipping_cost,
                         discount_percent=discount_percent,
                         discount_amount=discount_amount,
                         total=total)

@bp.route('/process', methods=['POST'])
@login_required
def process_checkout():
    """Process the checkout"""
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.cart'))
    
    address_id = request.form.get('shipping_address')
    if not address_id:
        flash('Please select a delivery address.', 'danger')
        return redirect(url_for('order.checkout'))
    
    # Handle new address creation
    if address_id == 'new':
        try:
            address = Address(
                user_id=current_user.id,
                name=request.form.get('name'),
                street=request.form.get('street'),
                city=request.form.get('city'),
                state=request.form.get('state'),
                postal_code=request.form.get('zip_code'),
                country=request.form.get('country', 'US'),
                phone=request.form.get('phone')
            )
            db.session.add(address)
            db.session.flush()  # Get the new address ID
            address_id = address.id
        except Exception as e:
            flash('Error creating new address. Please try again.', 'danger')
            return redirect(url_for('order.checkout'))
    else:
        address = Address.query.get_or_404(address_id)
        if address.user_id != current_user.id:
            flash('Invalid address selected.', 'danger')
            return redirect(url_for('order.checkout'))
    
    try:
        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        shipping_cost = 10.0  # Fixed shipping cost
        discount_percent = session.get('discount', 0)
        discount_amount = (subtotal * discount_percent / 100)
        total = subtotal + shipping_cost - discount_amount
        
        # Create order
        order = Order(
            user_id=current_user.id,
            shipping_address_id=address_id,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            discount=discount_amount,
            total=total,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
        
        # Clear cart
        for item in cart_items:
            db.session.delete(item)
        
        # Clear discount
        session.pop('discount', None)
        
        db.session.commit()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order.order_detail', order_id=order.id))
    
    except Exception as e:
        db.session.rollback()
        flash('Error processing your order. Please try again.', 'danger')
        return redirect(url_for('order.checkout'))

@bp.route('/<int:order_id>')
@login_required
def order_detail(order_id):
    """Display order details"""
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('order/order_detail.html', order=order)

@bp.route('/apply-promo', methods=['POST'])
@login_required
def apply_promo():
    """Apply promotional code"""
    promo_code = request.form.get('promo_code', '').upper()
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    # Simple promo code logic (should be replaced with proper promo code system)
    valid_codes = {
        'WELCOME10': 10,
        'SAVE20': 20,
        'SPECIAL50': 50
    }
    
    if promo_code in valid_codes:
        discount = valid_codes[promo_code]
        session['discount'] = discount
        final_total = total - (total * discount / 100)
        return jsonify({
            'success': True,
            'message': f'Promo code applied! {discount}% discount',
            'discount': discount,
            'final_total': final_total
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Invalid promo code'
        })

@bp.route('/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You cannot cancel this order.', 'error')
        return redirect(url_for('order.orders'))
    
    if order.status not in ['pending', 'processing']:
        flash('This order cannot be cancelled.', 'error')
        return redirect(url_for('order.order_detail', order_id=order.id))
    
    order.cancel_order('user')
    flash('Order has been cancelled.', 'success')
    return redirect(url_for('order.order_detail', order_id=order.id))
