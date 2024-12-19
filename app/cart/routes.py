from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, session
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.cart import Cart
from app.extensions import db
from app.cart import bp
from sqlalchemy import func
from app.models.coupon import Coupon  # Assuming you have a Coupon model

@bp.route('/')
@login_required
def cart():
    """Shopping cart page route"""
    try:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        
        # Get applied coupon from session if it exists
        coupon_code = session.get('coupon_code')
        discount = 0
        
        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code).first()
            if coupon:
                if coupon.discount_type == 'percentage':
                    discount = subtotal * (coupon.discount_amount / 100)
                else:  # fixed amount
                    discount = coupon.discount_amount
                    
        total = subtotal - discount
        
        return render_template(
            'cart/cart.html',
            cart_items=cart_items,
            subtotal=subtotal,
            discount=discount,
            total=total,
            coupon_code=coupon_code
        )
    except Exception as e:
        current_app.logger.error(f"Error in cart route: {str(e)}")
        flash('An error occurred while loading your cart. Please try again.', 'danger')
        return redirect(url_for('main.index'))

@bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart route"""
    try:
        # Enhanced request logging
        current_app.logger.info(f"Adding to cart - Product ID: {product_id}, User ID: {current_user.id}")
        current_app.logger.debug(f"Request headers: {dict(request.headers)}")
        current_app.logger.debug(f"Request data: {request.form}")
        
        # Get quantity from form data
        try:
            quantity = int(request.form.get('quantity', 1))
            if quantity < 1:
                quantity = 1
        except (TypeError, ValueError) as e:
            current_app.logger.error(f"Invalid quantity data: {str(e)}")
            quantity = 1
        
        # Verify product exists
        product = Product.query.get_or_404(product_id)
        if not product:
            current_app.logger.error(f"Product not found: {product_id}")
            return jsonify({
                'success': False,
                'message': 'Product not found'
            }), 404
        
        # Check stock availability
        if product.stock < quantity:
            current_app.logger.warning(f"Insufficient stock for product {product_id}: requested {quantity}, available {product.stock}")
            return jsonify({
                'success': False,
                'message': 'Not enough stock available'
            }), 400
        
        try:
            # Check if product already in cart
            cart_item = Cart.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first()
            
            if cart_item:
                current_app.logger.info(f"Updating existing cart item: {cart_item.id}")
                cart_item.quantity += quantity
            else:
                current_app.logger.info(f"Creating new cart item for product {product_id}")
                cart_item = Cart(
                    user_id=current_user.id,
                    product_id=product_id,
                    quantity=quantity
                )
                db.session.add(cart_item)
            
            db.session.commit()
            
            # Get updated cart total
            cart_total = Cart.query.filter_by(user_id=current_user.id).with_entities(
                func.sum(Cart.quantity)
            ).scalar() or 0
            
            return jsonify({
                'success': True,
                'message': 'Product added to cart successfully',
                'cart_total': cart_total
            })
            
        except Exception as e:
            current_app.logger.error(f"Database error: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': 'Error adding product to cart'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"Unexpected error adding to cart: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An unexpected error occurred'
        }), 500

@bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    """Remove product from cart route"""
    cart_item = Cart.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('cart.cart'))
    
    try:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', 'success')
    except:
        db.session.rollback()
        flash('Error removing item from cart.', 'danger')
    
    return redirect(url_for('cart.cart'))

@bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    """Update cart item quantity"""
    cart_item = Cart.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized action.'})
    
    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            return jsonify({'success': False, 'message': 'Invalid quantity.'})
        
        cart_item.quantity = quantity
        db.session.commit()
        
        # Calculate new totals
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items)
        item_total = cart_item.product.price * cart_item.quantity
        
        return jsonify({
            'success': True,
            'message': 'Cart updated successfully.',
            'total': total,
            'itemTotal': item_total
        })
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid quantity value.'})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating cart.'})

@bp.route('/coupons/apply', methods=['POST'])
@login_required
def apply_coupon():
    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        current_app.logger.info(f"Attempting to apply coupon code: {code}")
        
        if not code:
            return jsonify({'success': False, 'error': 'Please enter a coupon code'})
            
        coupon = Coupon.query.filter_by(code=code).first()
        if not coupon:
            current_app.logger.info(f"Coupon not found: {code}")
            return jsonify({'success': False, 'error': 'Invalid coupon code'})
            
        # Get cart items and calculate total
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            return jsonify({'success': False, 'error': 'Your cart is empty'})
            
        subtotal = sum(item.product.price * item.quantity for item in cart_items)
        current_app.logger.info(f"Cart subtotal: {subtotal}")
        
        # Validate coupon
        is_valid, error_message = coupon.is_valid(subtotal)
        if not is_valid:
            current_app.logger.info(f"Coupon validation failed: {error_message}")
            return jsonify({'success': False, 'error': error_message})
        
        # Calculate discount
        if coupon.discount_type == 'percentage':
            discount = subtotal * (coupon.discount_amount / 100)
            if coupon.max_discount_amount:
                discount = min(discount, coupon.max_discount_amount)
        else:  # fixed amount
            discount = min(coupon.discount_amount, subtotal)  # Don't allow discount greater than subtotal
            
        current_app.logger.info(f"Calculated discount: {discount}")
        
        # Store coupon in session
        session['coupon_code'] = coupon.code
        
        # Calculate new total
        new_total = subtotal - discount
        current_app.logger.info(f"New total after discount: {new_total}")
        
        # Increment times used
        coupon.times_used += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Coupon {code} applied successfully!',
            'discount': discount,
            'new_total': new_total,
            'subtotal': subtotal
        })
    except Exception as e:
        current_app.logger.error(f"Error applying coupon: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred while applying the coupon'})

@bp.route('/coupons/remove', methods=['POST'])
@login_required
def remove_coupon():
    try:
        if 'coupon_code' in session:
            del session['coupon_code']
            
        # Recalculate cart total without discount
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        new_total = sum(item.product.price * item.quantity for item in cart_items)
        
        return jsonify({
            'success': True,
            'message': 'Coupon removed successfully',
            'new_total': new_total,
            'discount': 0
        })
    except Exception as e:
        current_app.logger.error(f"Error removing coupon: {str(e)}")
        return jsonify({'success': False, 'error': 'An error occurred while removing the coupon'})

@bp.route('/coupons/check/<code>', methods=['GET'])
@login_required
def check_coupon(code):
    try:
        coupon = Coupon.query.filter_by(code=code.upper()).first()
        if coupon:
            return jsonify({
                'exists': True,
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_amount': coupon.discount_amount,
                'min_purchase_amount': coupon.min_purchase_amount,
                'max_discount_amount': coupon.max_discount_amount,
                'is_active': coupon.is_active,
                'times_used': coupon.times_used
            })
        return jsonify({'exists': False})
    except Exception as e:
        current_app.logger.error(f"Error checking coupon: {str(e)}")
        return jsonify({'error': str(e)})
