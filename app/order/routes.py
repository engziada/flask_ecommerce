from flask import render_template, redirect, url_for, flash, request, jsonify, session, current_app
from flask_login import login_required, current_user
from app.models.order import Order, OrderItem
from app.models.cart import Cart
from app.models.address import Address
from app.models.shipping import ShippingCarrier, ShippingMethod, ShippingQuote
from app.models.coupon import Coupon
from app.shipping.services import BostaShippingService, calculate_shipping_cost
from app.extensions import db
from app.order import bp
from datetime import datetime, timedelta
from app.utils.stripe_utils import create_payment_intent, confirm_payment_intent
import stripe
from app.utils.paymob_utils import create_order, get_payment_key, verify_webhook_signature, process_transaction_response
import json

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
    if not addresses:
        flash('Please add a shipping address first.', 'warning')
        return redirect(url_for('address.addresses'))
    
    # Get active shipping carriers with their methods
    carriers = ShippingCarrier.query.filter_by(is_active=True).options(
        db.joinedload(ShippingCarrier.shipping_methods)
    ).all()
    
    # Make sure we have at least one carrier with a method
    if not carriers or not any(carrier.shipping_methods for carrier in carriers):
        flash('No shipping methods available.', 'error')
        return redirect(url_for('cart.cart'))
    
    # Get applied coupon from session
    coupon_code = session.get('coupon_code')
    discount = 0
    coupon = None
    
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code).first()
        if coupon:
            if coupon.discount_type == 'percentage':
                discount = subtotal * (coupon.discount_amount / 100)
                if coupon.max_discount_amount and discount > coupon.max_discount_amount:
                    discount = coupon.max_discount_amount
            else:  # fixed amount
                discount = min(coupon.discount_amount, subtotal)  # Don't exceed subtotal
    
    # Default shipping cost (will be updated when user selects shipping method)
    shipping_cost = 0.0
    
    # Calculate final total
    total = subtotal + shipping_cost - discount
    
    # Create a pending order with default shipping address
    order = Order(
        user_id=current_user.id,
        status='pending',
        payment_status='pending',
        payment_method='cod',  # Default to COD
        shipping_address_id=addresses[0].id,  # Use first address as default
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        discount=discount,
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
    db.session.commit()
    
    current_app.logger.info(f'Created pending order {order.id} with shipping address {order.shipping_address_id}')
    
    return render_template('order/checkout.html',
                         order=order,
                         cart_items=cart_items,
                         addresses=addresses,
                         carriers=carriers,
                         subtotal=subtotal,
                         shipping_cost=shipping_cost,
                         coupon=coupon,
                         discount=discount,
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

            # Get applied coupon from session
            coupon_code = session.get('coupon_code')
            discount = 0
            coupon = None
            
            if coupon_code:
                coupon = Coupon.query.filter_by(code=coupon_code).first()
                if coupon:
                    if coupon.discount_type == 'percentage':
                        discount = subtotal * (coupon.discount_amount / 100)
                        if coupon.max_discount_amount and discount > coupon.max_discount_amount:
                            discount = coupon.max_discount_amount
                    else:  # fixed amount
                        discount = min(coupon.discount_amount, subtotal)  # Don't exceed subtotal
            
            # Calculate total
            total = subtotal + shipping_cost - discount
            
            return jsonify({
                'success': True,
                'shipping_cost': shipping_cost,
                'subtotal': subtotal,
                'discount': discount,
                'total': total
            })
            
        except Exception as e:
            current_app.logger.error(f"Error estimating shipping cost: {str(e)}")
            return jsonify({'error': 'Could not estimate shipping cost'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in calculate_shipping: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/update-payment-intent', methods=['POST'])
@login_required
def update_payment_intent():
    """Update payment intent amount"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        amount = data.get('amount')
        if not amount:
            return jsonify({'error': 'Missing amount'}), 400
            
        # Create or update payment intent
        payment_intent = create_payment_intent(
            amount=amount,
            currency='egp',  # Use Egyptian Pounds
            customer_id=current_user.stripe_customer_id
        )
        
        return jsonify({
            'success': True,
            'payment_intent_id': payment_intent.id
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f'Error updating payment intent: {str(e)}')
        return jsonify({'error': 'Failed to update payment intent'}), 500

@bp.route('/process-checkout', methods=['POST'])
@login_required
def process_checkout():
    """Process the checkout"""
    try:
        # Get form data
        payment_method = request.form.get('payment_method')
        shipping_address_id = request.form.get('shipping_address_id')
        payment_intent_id = request.form.get('payment_intent_id')
        
        if not shipping_address_id:
            flash('Please select a shipping address.', 'error')
            return redirect(url_for('order.checkout'))
            
        # Get cart items
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            flash('Your cart is empty.', 'error')
            return redirect(url_for('cart.cart'))
            
        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        
        # Get shipping cost from session
        shipping_cost = session.get('shipping_cost')
        stored_address_id = session.get('shipping_address_id')
        
        # Verify shipping cost exists and matches the current address
        if shipping_cost is None or str(stored_address_id) != str(shipping_address_id):
            flash('Please recalculate shipping cost before proceeding.', 'error')
            return redirect(url_for('order.checkout'))
            
        # Apply coupon if exists
        coupon_code = session.get('coupon_code')
        discount = 0
        
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code).first()
            if coupon:
                if coupon.discount_type == 'percentage':
                    discount = subtotal * (coupon.discount_amount / 100)
                    if coupon.max_discount_amount and discount > coupon.max_discount_amount:
                        discount = coupon.max_discount_amount
                else:  # fixed amount
                    discount = min(coupon.discount_amount, subtotal)
        
        # Calculate final total
        total = subtotal + shipping_cost - discount
        
        # For card payments, confirm the payment intent
        if payment_method == 'card':
            if not payment_intent_id:
                flash('Payment processing failed. Please try again.', 'error')
                return redirect(url_for('order.checkout'))
                
            try:
                payment = confirm_payment_intent(payment_intent_id)
                if not payment.status == 'succeeded':
                    flash('Payment failed. Please try again.', 'error')
                    return redirect(url_for('order.checkout'))
            except stripe.error.StripeError as e:
                flash(f'Payment failed: {str(e)}', 'error')
                return redirect(url_for('order.checkout'))
        
        # Create order
        order = Order(
            user_id=current_user.id,
            shipping_address_id=shipping_address_id,
            payment_method=payment_method,
            stripe_payment_id=payment_intent_id if payment_method == 'card' else None,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            discount=discount,
            total=total,
            status='pending' if payment_method == 'cod' else 'paid',
            payment_status='pending' if payment_method == 'cod' else 'paid'
        )
        
        db.session.add(order)
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
            
            # Update product stock
            product = cart_item.product
            product.stock -= cart_item.quantity
            db.session.add(product)
        
        # Clear cart, shipping cost, and coupon from session
        Cart.query.filter_by(user_id=current_user.id).delete()
        session.pop('shipping_cost', None)
        session.pop('shipping_address_id', None)
        session.pop('coupon_code', None)
        
        db.session.commit()
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order.order_detail', order_id=order.id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error processing checkout: {str(e)}')
        flash('Error processing your order. Please try again.', 'error')
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
        discount = 0
        coupon_code = session.get('coupon_code')
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code).first()
            if coupon:
                if coupon.discount_type == 'percentage':
                    discount = subtotal * (coupon.discount_amount / 100)
                    if coupon.max_discount_amount and discount > coupon.max_discount_amount:
                        discount = coupon.max_discount_amount
                else:  # fixed amount
                    discount = min(coupon.discount_amount, subtotal)  # Don't exceed subtotal
        total = subtotal + shipping_cost - discount

        # Create a PaymentIntent with the order amount and currency
        intent = create_payment_intent(
            amount=total,
            currency='egp',  # Use Egyptian Pounds
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
        session['coupon_code'] = promo_code
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
        if order.delivery_order_id:
            try:
                bosta_service = BostaShippingService()
                bosta_service.cancel_shipping_order(order.delivery_order_id)
                
                # Update delivery status
                order.delivery_status = 'CANCELLED'
                order.delivery_updated_at = datetime.utcnow()
                
                current_app.logger.info(f"Cancelled Bosta delivery for order {order_id}")
            except Exception as e:
                current_app.logger.error(f"Failed to cancel Bosta delivery for order {order_id}: {str(e)}")
                # Continue with order cancellation even if delivery cancellation fails
        
        # Restore product stock
        for item in order.items:
            item.product.stock += item.quantity
            current_app.logger.info(f"Restored {item.quantity} items to stock for product {item.product.name}")
        
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

def calculate_shipping_cost(address_id):
    """Helper function to calculate shipping cost for an address"""
    try:
        # Get address
        address = Address.query.get_or_404(address_id)
        
        # Initialize Bosta shipping service
        bosta_service = BostaShippingService()
        
        # Get the default pickup location
        bosta_service._ensure_token()
        bosta_service._get_default_location()
        
        if not bosta_service.default_location:
            current_app.logger.error("Could not get default pickup location")
            return None
            
        # Get pickup and dropoff cities
        pickup_city = bosta_service.default_location['address']['city']['name']
        dropoff_city = address.city
        
        # Estimate shipping cost
        shipping_cost = bosta_service.estimate_shipping_cost(
            pickup_city=pickup_city,
            dropoff_city=dropoff_city,
            cod_amount=0  # We'll add COD fee later if needed
        )
        
        if shipping_cost is None:
            current_app.logger.error("Could not calculate shipping cost")
            return None
            
        return shipping_cost
        
    except Exception as e:
        current_app.logger.error(f"Error calculating shipping cost: {str(e)}")
        return None

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

@bp.route('/process-paymob-payment', methods=['POST'])
@login_required
def process_paymob_payment():
    """Process PayMob payment and return payment URL"""
    try:
        # Get order ID from request
        order_id = request.json.get('order_id')
        if not order_id:
            current_app.logger.error('No order ID provided')
            return jsonify({'success': False, 'error': 'Invalid order ID'})
        
        current_app.logger.info(f'Processing PayMob payment for order {order_id}')
        
        # Get order with related items and products
        order = Order.query.options(
            db.joinedload(Order.items).joinedload(OrderItem.ordered_product)
        ).get_or_404(order_id)
        
        if order.user_id != current_user.id:
            current_app.logger.error(f'Unauthorized access to order {order_id}')
            return jsonify({'success': False, 'error': 'Unauthorized'})
        
        # Check if order has shipping address
        if not order.shipping_address_id:
            current_app.logger.error(f'No shipping address for order {order_id}')
            return jsonify({'success': False, 'error': 'Please select a shipping address'})
        
        # Convert amount to cents (PayMob requires amount in cents)
        amount_cents = int(order.total * 100)
        current_app.logger.debug(f'Processing payment for amount: {amount_cents} cents')
        
        # Create order items list for PayMob
        items = [{
            'name': item.ordered_product.name,
            'amount_cents': int(item.price * 100),
            'description': f'{item.ordered_product.name} x {item.quantity}',
            'quantity': item.quantity
        } for item in order.items]
        
        current_app.logger.debug(f'Creating PayMob order with {len(items)} items')
        
        try:
            # Create order in PayMob
            paymob_order_id, auth_token = create_order(
                amount_cents=amount_cents,
                items=items
            )
            current_app.logger.info(f'PayMob order created: {paymob_order_id}')
        except Exception as e:
            current_app.logger.error(f'Error creating PayMob order: {str(e)}')
            return jsonify({'success': False, 'error': 'Failed to create payment order'})
        
        # Get shipping address
        shipping_address = Address.query.get(order.shipping_address_id)
        if not shipping_address:
            current_app.logger.error(f'Shipping address {order.shipping_address_id} not found')
            return jsonify({'success': False, 'error': 'Invalid shipping address'})
        
        # Get billing data from shipping address
        billing_data = {
            'first_name': current_user.first_name or 'N/A',
            'last_name': current_user.last_name or 'N/A',
            'email': current_user.email,
            'phone_number': shipping_address.phone,
            'street': f'{shipping_address.street}, Building {shipping_address.building_number or "N/A"}',
            'building': shipping_address.building_number or 'NA',
            'floor': shipping_address.floor or 'NA',
            'apartment': shipping_address.apartment or 'NA',
            'city': shipping_address.city,
            'country': 'EG',  # Egypt country code
            'postal_code': shipping_address.postal_code or 'NA',
            'state': shipping_address.district or 'NA'
        }
        
        current_app.logger.debug(f'Getting payment key with billing data: {json.dumps(billing_data)}')
        
        try:
            # Get payment key
            payment_key = get_payment_key(
                order_id=paymob_order_id,
                auth_token=auth_token,
                amount_cents=amount_cents,
                billing_data=billing_data,
                integration_id=current_app.config.get('PAYMOB_INTEGRATION_ID')
            )
            current_app.logger.info('Payment key generated successfully')
        except Exception as e:
            current_app.logger.error(f'Error getting payment key: {str(e)}')
            return jsonify({'success': False, 'error': 'Failed to generate payment key'})
        
        # Get iframe ID
        iframe_id = current_app.config.get('PAYMOB_IFRAME_ID')
        if not iframe_id:
            current_app.logger.error('PayMob iframe ID not configured')
            return jsonify({'success': False, 'error': 'Payment system not properly configured'})
        
        # Save PayMob order ID
        order.paymob_order_id = str(paymob_order_id)
        db.session.commit()
        current_app.logger.info(f'Updated order {order_id} with PayMob order ID: {paymob_order_id}')
        
        return jsonify({
            'success': True,
            'payment_key': payment_key,
            'iframe_id': iframe_id
        })
        
    except Exception as e:
        current_app.logger.error(f'PayMob payment error: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e) if current_app.debug else 'Payment processing failed. Please try again.'
        }), 500

@bp.route('/paymob-callback', methods=['GET', 'POST'])
def paymob_callback():
    """Handle PayMob payment callback"""
    try:
        current_app.logger.info('Received PayMob callback')
        
        # Get data from request
        if request.method == 'GET':
            data = request.args.to_dict()
        else:
            data = request.json
            
        current_app.logger.debug(f'Callback data: {json.dumps(data)}')
        
        # Get transaction ID and success status
        transaction_id = data.get('id') or data.get('transaction_id')
        success = data.get('success') == 'true' or data.get('success') == True
        order_id = data.get('order')
        
        current_app.logger.info(f'Processing transaction {transaction_id} for order {order_id}, success: {success}')
        
        if not order_id:
            error_msg = 'No order ID in callback'
            current_app.logger.error(error_msg)
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Find our order by PayMob order ID
        order = Order.query.filter_by(paymob_order_id=order_id).first()
        if not order:
            error_msg = f'Order not found for PayMob order ID: {order_id}'
            current_app.logger.error(error_msg)
            return jsonify({'success': False, 'error': error_msg}), 404
        
        if success:
            # Update order status
            order.payment_status = 'paid'
            order.status = 'processing'
            order.payment_method = 'card'
            order.paid_at = datetime.utcnow()
            order.paymob_payment_id = transaction_id
            
            # Clear cart
            Cart.query.filter_by(user_id=order.user_id).delete()
            
            db.session.commit()
            
            current_app.logger.info(f'Payment successful for order {order.id}')
            
            # Send order confirmation email
            try:
                send_order_confirmation_email(order)
            except Exception as e:
                current_app.logger.error(f'Failed to send order confirmation email: {str(e)}')
            
            response_data = {
                'success': True,
                'redirect_url': url_for('order.order_confirmation', order_id=order.id)
            }
        else:
            # Payment failed
            order.payment_status = 'failed'
            db.session.commit()
            
            current_app.logger.error(f'Payment failed for order {order.id}')
            response_data = {
                'success': False,
                'error': 'Payment failed. Please try again or choose a different payment method.'
            }
        
        # Return JSON for POST requests, redirect for GET requests
        if request.method == 'POST':
            return jsonify(response_data)
        else:
            if success:
                return redirect(url_for('order.order_confirmation', order_id=order.id))
            else:
                flash('Payment failed. Please try again or choose a different payment method.', 'error')
                return redirect(url_for('order.checkout'))
            
    except Exception as e:
        current_app.logger.error(f'Error processing PayMob callback: {str(e)}')
        error_response = {
            'success': False,
            'error': str(e) if current_app.debug else 'An error occurred while processing your payment.'
        }
        if request.method == 'POST':
            return jsonify(error_response), 500
        else:
            flash(error_response['error'], 'error')
            return redirect(url_for('order.orders'))

@bp.route('/order-confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Show order confirmation page"""
    order = Order.query.get_or_404(order_id)
    
    # Ensure user can only view their own orders
    if order.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('order/confirmation.html', order=order)
