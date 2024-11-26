from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.cart import Cart
from app.extensions import db
from app.cart import bp
from sqlalchemy import func

@bp.route('/')
@login_required
def cart():
    """Shopping cart page route"""
    try:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items)
        return render_template('cart/cart.html', cart_items=cart_items, total=total)
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
