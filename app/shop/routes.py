from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.cart import Cart
from app.models.wishlist import Wishlist
from app.models.order import Order, OrderItem
from app.models.address import Address
from app import db
from datetime import datetime

bp = Blueprint('shop', __name__)

@bp.route('/wishlist')
@login_required
def wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('main/wishlist.html', wishlist_items=wishlist_items)

@bp.route('/add-to-wishlist/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product is already in wishlist
    existing_item = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing_item:
        return jsonify({
            'success': False,
            'message': 'Product is already in your wishlist'
        })
    
    wishlist_item = Wishlist(
        user_id=current_user.id,
        product_id=product_id
    )
    
    try:
        db.session.add(wishlist_item)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Product added to wishlist'
        })
    except:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An error occurred while adding to wishlist'
        })

@bp.route('/remove-from-wishlist/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    wishlist_item = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first_or_404()
    
    try:
        db.session.delete(wishlist_item)
        db.session.commit()
        flash('Product removed from wishlist', 'success')
    except:
        db.session.rollback()
        flash('An error occurred', 'error')
    
    return redirect(url_for('shop.wishlist'))

@bp.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    
    # Calculate totals
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping_cost = 10.00  # Fixed shipping cost
    total = subtotal + shipping_cost
    
    return render_template('main/cart.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         shipping_cost=shipping_cost,
                         total=total)

@bp.route('/checkout')
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty', 'info')
        return redirect(url_for('main.index'))
    
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    # Calculate totals
    subtotal = sum(item.product.price * item.quantity for item in cart_items)
    shipping_cost = 10.00  # Fixed shipping cost for now
    total = subtotal + shipping_cost
    
    return render_template('main/checkout.html',
                         cart_items=cart_items,
                         addresses=addresses,
                         subtotal=subtotal,
                         shipping_cost=shipping_cost,
                         total=total,
                         discount=0,
                         current_year=datetime.now().year)

@bp.route('/apply-promo', methods=['POST'])
@login_required
def apply_promo():
    data = request.get_json()
    promo_code = data.get('code')
    
    # Simple promo code implementation
    valid_promos = {
        'WELCOME10': 10,
        'SAVE20': 20
    }
    
    if promo_code in valid_promos:
        discount = valid_promos[promo_code]
        # Store discount in session
        session['discount'] = discount
        return jsonify({
            'success': True,
            'message': f'Promo code applied! {discount}% discount'
        })
    
    return jsonify({
        'success': False,
        'message': 'Invalid promo code'
    })

@bp.route('/process-checkout', methods=['POST'])
@login_required
def process_checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('shop.checkout'))
    
    # Get or create shipping address
    address_id = request.form.get('shipping_address')
    if address_id == 'new':
        address = Address(
            user_id=current_user.id,
            name=request.form.get('name'),
            street=request.form.get('street'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            zip_code=request.form.get('zip_code'),
            country=request.form.get('country'),
            phone=request.form.get('phone')
        )
        if request.form.get('save_address'):
            db.session.add(address)
            db.session.commit()
    else:
        address = Address.query.get_or_404(address_id)
    
    # Create order
    order = Order(
        user_id=current_user.id,
        shipping_address_id=address.id,
        status='pending',
        subtotal=sum(item.product.price * item.quantity for item in cart_items),
        shipping_cost=10.00,  # Fixed shipping cost
        discount=session.get('discount', 0),
        total=sum(item.product.price * item.quantity for item in cart_items) + 10.00,
        date_created=datetime.utcnow()
    )
    
    # Add order items
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
    
    try:
        # Clear cart
        for item in cart_items:
            db.session.delete(item)
        
        db.session.add(order)
        db.session.commit()
        
        # Clear discount from session
        session.pop('discount', None)
        
        flash('Order placed successfully!', 'success')
        return redirect(url_for('auth.orders'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while processing your order.', 'error')
        return redirect(url_for('shop.checkout'))
