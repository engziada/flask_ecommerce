from flask import render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from app.models.order import Order, OrderItem
from app.models.cart import Cart
from app.models.address import Address
from app.models.shipping import ShippingCarrier, ShippingMethod, ShippingQuote
from app.shipping.services import BostaShippingService, calculate_shipping_cost
from app.extensions import db
from app.order import bp
from datetime import datetime, timedelta
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
    # Use eager loading to load product relationships
    cart_items = Cart.query.filter_by(user_id=current_user.id).join(Cart.product).options(db.contains_eager(Cart.product)).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.cart'))
    
    # Calculate cart totals
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    
    # Get user addresses with one query
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    # Get active shipping carriers with their methods
    carriers = ShippingCarrier.query.filter_by(is_active=True).options(
        db.joinedload(ShippingCarrier.shipping_methods)
    ).all()
    
    # Make sure we have at least one carrier with a method
    if not carriers or not any(carrier.shipping_methods for carrier in carriers):
        flash('No shipping methods available.', 'error')
        return redirect(url_for('cart.cart'))
    
    # Apply any discounts from session
    discount_percent = session.get('discount', 0)
    discount_amount = (subtotal * discount_percent / 100) if discount_percent > 0 else 0
    
    # Default shipping cost (will be updated when user selects shipping method)
    shipping_cost = 0.0
    
    # Calculate final total
    total = subtotal + shipping_cost - discount_amount
    
    return render_template('order/checkout.html',
                         cart_items=cart_items,
                         addresses=addresses,
                         carriers=carriers,
                         subtotal=subtotal,
                         shipping_cost=shipping_cost,
                         discount_percent=discount_percent,
                         discount_amount=discount_amount,
                         total=total)

@bp.route('/calculate-shipping', methods=['POST'])
@login_required
def calculate_shipping():
    """Calculate shipping cost based on selected address, carrier, and payment method"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        address_id = data.get('address_id')
        carrier_code = data.get('carrier_code')
        payment_method = data.get('payment_method', 'card')
        
        if not address_id:
            return jsonify({'error': 'Missing address ID'}), 400
            
        if not carrier_code:
            return jsonify({'error': 'Missing carrier code'}), 400
            
        # Get address and cart items
        address = Address.query.get_or_404(address_id)
        cart_items = Cart.query.filter_by(user_id=current_user.id).join(Cart.product).options(db.contains_eager(Cart.product)).all()
        
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
        
        # Calculate subtotal
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        
        # Initialize Bosta shipping service
        bosta_service = BostaShippingService()
        
        # Get the default pickup location
        bosta_service._ensure_token()
        bosta_service._get_default_location()
        
        if not bosta_service.default_location:
            return jsonify({'error': 'Could not get default pickup location'}), 500
            
        # Set COD amount based on payment method
        cod_amount = subtotal if payment_method == 'cod' else 0
        
        # Get pickup and dropoff cities
        pickup_city = bosta_service.default_location['address']['city']['name']
        dropoff_city = address.city
        
        # Estimate shipping cost
        try:
            shipping_cost = bosta_service.estimate_shipping_cost(
                pickup_city=pickup_city,
                dropoff_city=dropoff_city,
                cod_amount=cod_amount
            )
            
            if shipping_cost is None:
                return jsonify({'error': 'Could not calculate shipping cost'}), 400

            # Apply any discounts from session
            discount_percent = session.get('discount', 0)
            discount_amount = (subtotal * discount_percent / 100) if discount_percent > 0 else 0
            
            # Calculate total
            total = subtotal + shipping_cost - discount_amount
            
            return jsonify({
                'success': True,
                'shipping_cost': shipping_cost,
                'subtotal': subtotal,
                'discount_amount': discount_amount,
                'total': total
            })
            
        except Exception as e:
            current_app.logger.error(f"Error estimating shipping cost: {str(e)}")
            return jsonify({'error': 'Could not estimate shipping cost'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in calculate_shipping: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/process', methods=['POST'])
@login_required
def process_checkout():
    """Process the checkout"""
    try:
        # Get form data
        address_id = request.form.get('address_id')
        payment_method = request.form.get('payment_method')
        carrier_id = request.form.get('carrier_id')
        method_id = request.form.get('method_id')
        
        # Log the form data for debugging
        current_app.logger.info(f"Checkout form data: address_id={address_id}, payment_method={payment_method}, carrier_id={carrier_id}, method_id={method_id}")
        
        if not all([address_id, payment_method, carrier_id, method_id]):
            missing_fields = []
            if not address_id: missing_fields.append('shipping address')
            if not payment_method: missing_fields.append('payment method')
            if not carrier_id: missing_fields.append('shipping carrier')
            if not method_id: missing_fields.append('shipping method')
            flash(f'Missing required checkout information: {", ".join(missing_fields)}.', 'error')
            return redirect(url_for('order.checkout'))
        
        # Get cart items
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            flash('Your cart is empty.', 'error')
            return redirect(url_for('cart.cart'))
        
        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        
        # Get shipping carrier and method
        carrier = ShippingCarrier.query.get_or_404(carrier_id)
        method = ShippingMethod.query.get_or_404(method_id)
        
        # Calculate shipping cost
        shipping_cost = carrier.base_cost
        if method.code == 'express':
            shipping_cost *= 1.5 if carrier.code == 'bosta' else 1.3
        
        # Apply any discounts from session
        discount_percent = session.get('discount', 0)
        discount_amount = (subtotal * discount_percent / 100) if discount_percent > 0 else 0
        
        # Calculate final total
        total = subtotal + shipping_cost - discount_amount
        
        # Create the order
        order = Order(
            user_id=current_user.id,
            shipping_address_id=address_id,
            shipping_carrier_id=carrier_id,
            shipping_method_id=method_id,
            payment_method=payment_method,
            status='pending',
            payment_status='pending',
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            discount=discount_amount,
            total=total
        )
        
        # Add order items
        for cart_item in cart_items:
            order_item = OrderItem(
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            order.items.append(order_item)
        
        db.session.add(order)
        db.session.flush()  # This assigns the order.id without committing
        
        # Create shipping quote
        quote = ShippingQuote(
            order_id=order.id,  # Now order.id is available
            carrier_id=carrier_id,
            method_id=method_id,
            cost=shipping_cost,
            currency='EGP',
            quote_data={
                'base_cost': carrier.base_cost,
                'method': method.code,
                'estimated_days': method.estimated_days
            },
            is_selected=True,
            valid_until=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(quote)
        
        # Create Bosta delivery order
        try:
            bosta_service = BostaShippingService()
            delivery_order = bosta_service.create_shipping_order(order)
            if delivery_order:
                # Update order with tracking info
                order.tracking_number = delivery_order.get('trackingNumber')
                order.carrier_tracking_url = delivery_order.get('trackingURL')
                db.session.commit()
                current_app.logger.info(f"Successfully created delivery order for order {order.id}")
            else:
                current_app.logger.warning(f"No delivery order data returned for order {order.id}")
        except Exception as e:
            current_app.logger.error(f"Error creating Bosta delivery order: {str(e)}")
            # Don't fail the entire order if shipping creation fails
            # Just log the error and continue
        
        # Clear cart
        for item in cart_items:
            db.session.delete(item)
        
        # Clear discount from session
        session.pop('discount', None)
        
        db.session.commit()
        
        if payment_method == 'card':
            # Create Stripe payment intent
            payment_intent = create_payment_intent(order)
            order.stripe_payment_id = payment_intent.id
            db.session.commit()
            
            return render_template('order/payment.html', 
                                client_secret=payment_intent.client_secret,
                                order=order)
        else:
            # For cash on delivery
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order.order_detail', order_id=order.id))
            
    except Exception as e:
        current_app.logger.error(f"Checkout error: {str(e)}")
        flash('An error occurred during checkout. Please try again.', 'error')
        return redirect(url_for('order.checkout'))

@bp.route('/create-payment-intent', methods=['POST'])
@login_required
def create_payment():
    """Create a payment intent for Stripe"""
    try:
        cart_items = Cart.query.filter_by(user_id=current_user.id).join(Cart.product).options(db.contains_eager(Cart.product)).all()
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
    cart_items = Cart.query.filter_by(user_id=current_user.id).join(Cart.product).options(db.contains_eager(Cart.product)).all()
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

@bp.route('/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    """Cancel an order"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if order belongs to current user
        if order.user_id != current_user.id:
            flash('You do not have permission to cancel this order.', 'error')
            return redirect(url_for('order.orders'))
            
        # Check if order can be cancelled
        if order.status not in ['pending', 'processing']:
            flash('This order cannot be cancelled.', 'error')
            return redirect(url_for('order.orders'))
            
        # Cancel Bosta delivery if exists
        if order.delivery_id:
            try:
                bosta_service = BostaShippingService()
                bosta_service.cancel_shipping_order(order.delivery_id)
                current_app.logger.info(f"Cancelled Bosta delivery for order {order_id}")
            except Exception as e:
                current_app.logger.error(f"Failed to cancel Bosta delivery for order {order_id}: {str(e)}")
                # Continue with order cancellation even if delivery cancellation fails
        
        # Update order status
        order.status = 'cancelled'
        order.date_updated = datetime.utcnow()
        
        # Save changes
        db.session.commit()
        
        flash('Order has been cancelled successfully.', 'success')
        current_app.logger.info(f"Order {order_id} cancelled successfully")
        
    except Exception as e:
        db.session.rollback()
        flash('Failed to cancel order.', 'error')
        current_app.logger.error(f"Error cancelling order {order_id}: {str(e)}")
        
    return redirect(url_for('order.orders'))

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
