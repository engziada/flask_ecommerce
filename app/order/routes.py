from flask import render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from app.models.order import Order, OrderItem
from app.models.cart import Cart
from app.models.address import Address
from app.extensions import db
from app.order import bp
from datetime import datetime
from app.utils.stripe_utils import create_payment_intent, confirm_payment_intent
import stripe

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

def validate_credit_card(cc_number, cc_name, cc_exp_month, cc_exp_year, cc_cvv):
    """Validate credit card information"""
    import re
    from datetime import datetime
    
    # Remove spaces and non-digits from card number
    cc_number = re.sub(r'\D', '', cc_number)
    
    # Basic card type patterns
    card_patterns = {
        'visa': r'^4[0-9]{12}(?:[0-9]{3})?$',
        'mastercard': r'^5[1-5][0-9]{14}$',
        'amex': r'^3[47][0-9]{13}$',
        'discover': r'^6(?:011|5[0-9]{2})[0-9]{12}$'
    }
    
    errors = []
    
    # Validate card number format
    valid_card = False
    for card_type, pattern in card_patterns.items():
        if re.match(pattern, cc_number):
            valid_card = True
            break
    
    if not valid_card:
        errors.append('Invalid credit card number')
    
    # Luhn algorithm validation
    if valid_card:
        sum = 0
        num_digits = len(cc_number)
        oddeven = num_digits & 1
        
        for count in range(num_digits):
            digit = int(cc_number[count])
            if not ((count & 1) ^ oddeven):
                digit = digit * 2
                if digit > 9:
                    digit = digit - 9
            sum = sum + digit
        
        if sum % 10 != 0:
            errors.append('Invalid credit card number (checksum failed)')
    
    # Validate name
    if not cc_name or len(cc_name.strip()) < 3:
        errors.append('Invalid name on card')
    
    # Validate expiration date
    try:
        exp_month = int(cc_exp_month)
        exp_year = int(cc_exp_year)
        
        if not (1 <= exp_month <= 12):
            errors.append('Invalid expiration month')
        
        current_date = datetime.now()
        exp_date = datetime(exp_year, exp_month, 1)
        
        if exp_date < current_date:
            errors.append('Card has expired')
    except (ValueError, TypeError):
        errors.append('Invalid expiration date')
    
    # Validate CVV
    if not cc_cvv or not cc_cvv.isdigit():
        errors.append('Invalid CVV')
    else:
        # AMEX requires 4 digits, others require 3
        is_amex = cc_number.startswith(('34', '37'))
        if (is_amex and len(cc_cvv) != 4) or (not is_amex and len(cc_cvv) != 3):
            errors.append('Invalid CVV length')
    
    return errors

@bp.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment():
    """Create a payment intent for Stripe"""
    try:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400

        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        shipping_cost = 10.0  # Fixed shipping cost
        discount_percent = session.get('discount', 0)
        discount_amount = (subtotal * discount_percent / 100)
        total = subtotal + shipping_cost - discount_amount

        # Create a PaymentIntent with the order amount and currency
        intent = create_payment_intent(
            amount=total,
            metadata={
                'user_id': current_user.id,
                'cart_items': ','.join(str(item.id) for item in cart_items)
            }
        )

        return jsonify({
            'clientSecret': intent.client_secret
        })

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating payment intent: {str(e)}")
        return jsonify({'error': 'An error occurred processing your payment'}), 500

@bp.route('/process', methods=['POST'])
@login_required
def process_checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart.cart'))

    payment_method = request.form.get('payment_method', 'card')
    shipping_address_id = request.form.get('shipping_address')
    if not shipping_address_id:
        flash('Please select a shipping address.', 'error')
        return redirect(url_for('order.checkout'))

    try:
        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        shipping_cost = 10.0  # Fixed shipping cost
        total = subtotal + shipping_cost

        # Create order
        order = Order(
            user_id=current_user.id,
            shipping_address_id=shipping_address_id,
            subtotal=subtotal,
            total=total,
            shipping_cost=shipping_cost,
            payment_method=payment_method
        )

        if payment_method == 'card':
            # Handle card payment
            payment_intent_id = request.form.get('payment_intent_id')
            if not payment_intent_id:
                flash('Payment processing failed.', 'error')
                return redirect(url_for('order.checkout'))
            
            order.stripe_payment_id = payment_intent_id
            order.status = 'pending'
            order.payment_status = 'paid'
        else:  # COD
            order.status = 'pending'
            order.payment_status = 'pending'
            order.payment_method = 'COD'

        # Add order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)

        # Clear cart
        for item in cart_items:
            db.session.delete(item)
        
        db.session.add(order)
        db.session.commit()

        flash('Order placed successfully!', 'success')
        return redirect(url_for('order.order_detail', order_id=order.id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error processing order: {str(e)}')
        flash('An error occurred while processing your order. Please try again.', 'error')
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
