from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify, g
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.category import Category
from app.models.cart import Cart
from app.models.wishlist import Wishlist
from app.models.review import Review
from app.forms.contact import ContactForm
from app.forms.review import ReviewForm
from app.extensions import db, mail
from flask_mail import Message
from datetime import datetime
from app.main import bp
from app.models.address import Address  # Import the Address model
from sqlalchemy import func

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        # Get cart total
        cart_total = db.session.query(func.sum(Cart.quantity)).filter_by(user_id=current_user.id).scalar() or 0
        g.cart_total = cart_total
        
        # Get wishlist total
        wishlist_total = Wishlist.query.filter_by(user_id=current_user.id).count()
        g.wishlist_total = wishlist_total

@bp.context_processor
def utility_processor():
    return {
        'cart_total': getattr(g, 'cart_total', 0),
        'wishlist_total': getattr(g, 'wishlist_total', 0)
    }

@bp.route('/')
@bp.route('/index')
def index():
    """Home page route"""
    try:
        page = request.args.get('page', 1, type=int)
        products = Product.query.filter_by(is_active=True).paginate(
            page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12)
        )
        return render_template('main/index.html', products=products)
    except Exception as e:
        current_app.logger.error(f'Error in index route: {str(e)}')
        return render_template('errors/500.html'), 500

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page route"""
    try:
        product = Product.query.get_or_404(product_id)
        reviews = Review.query.filter_by(product_id=product_id).all()
        form = ReviewForm()
        return render_template('main/product_detail.html', product=product, reviews=reviews, form=form)
    except Exception as e:
        current_app.logger.error(f'Error in product_detail route: {str(e)}')
        return render_template('errors/500.html'), 500

@bp.route('/category/<int:category_id>')
def category_products(category_id):
    """Category products page route"""
    try:
        category = Category.query.get_or_404(category_id)
        page = request.args.get('page', 1, type=int)
        products = Product.query.filter_by(category_id=category_id, is_active=True).paginate(
            page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12)
        )
        return render_template('main/category_products.html', category=category, products=products)
    except Exception as e:
        current_app.logger.error(f'Error in category_products route: {str(e)}')
        return render_template('errors/500.html'), 500

@bp.route('/search')
def search():
    """Search products route"""
    try:
        query = request.args.get('q', '')
        if not query:
            return redirect(url_for('bp.index'))
        
        page = request.args.get('page', 1, type=int)
        products = Product.query.filter(
            Product.name.ilike(f'%{query}%') | 
            Product.description.ilike(f'%{query}%')
        ).paginate(
            page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12)
        )
        return render_template('main/search.html', products=products, query=query)
    except Exception as e:
        current_app.logger.error(f'Error in search route: {str(e)}')
        return render_template('errors/500.html'), 500

@bp.route('/cart')
@login_required
def cart():
    """Shopping cart page route"""
    try:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items)
        return render_template('main/cart.html', cart_items=cart_items, total=total)
    except Exception as e:
        current_app.logger.error(f'Error in cart route: {str(e)}')
        return render_template('errors/500.html'), 500

@bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart route"""
    try:
        product = Product.query.get_or_404(product_id)
        if product.stock <= 0:
            return jsonify({'success': False, 'message': 'Product out of stock'}), 400
        
        cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = Cart(user_id=current_user.id, product_id=product_id, quantity=1)
            db.session.add(cart_item)
        
        db.session.commit()
        
        # Get updated cart total
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        cart_total = sum(item.quantity for item in cart_items)
        
        return jsonify({
            'success': True, 
            'message': 'Product added to cart',
            'cart_total': cart_total
        })
    except Exception as e:
        current_app.logger.error(f'Error in add_to_cart route: {str(e)}')
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

@bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    """Remove product from cart route"""
    try:
        cart_item = Cart.query.get_or_404(item_id)
        if cart_item.user_id != current_user.id:
            flash('You are not authorized to remove this item.', 'danger')
            return redirect(url_for('main.cart'))
        
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart.', 'success')
        return redirect(url_for('main.cart'))
    except Exception as e:
        current_app.logger.error(f'Error in remove_from_cart route: {str(e)}')
        db.session.rollback()
        return render_template('errors/500.html'), 500

@bp.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    """Update cart item quantity"""
    try:
        cart_item = Cart.query.get_or_404(item_id)
        if cart_item.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        quantity = request.json.get('quantity')
        if not quantity or quantity < 1:
            return jsonify({'error': 'Invalid quantity'}), 400
        
        if quantity > cart_item.product.stock:
            return jsonify({'error': 'Not enough stock available'}), 400
        
        cart_item.quantity = quantity
        db.session.commit()
        
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items)
        
        return jsonify({
            'success': True,
            'quantity': quantity,
            'total': total,
            'item_total': cart_item.product.price * quantity
        })
    except Exception as e:
        current_app.logger.error(f'Error in update_cart route: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/wishlist')
@login_required
def wishlist():
    """Display user's wishlist"""
    try:
        wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
        return render_template('main/wishlist.html', wishlist_items=wishlist_items)
    except Exception as e:
        current_app.logger.error(f'Error in wishlist route: {str(e)}')
        flash('An error occurred while loading your wishlist', 'error')
        return redirect(url_for('main.index'))

@bp.route('/wishlist/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    """Toggle product in wishlist"""
    try:
        # Check if product exists
        product = Product.query.get_or_404(product_id)
        
        # Check if item is already in wishlist
        wishlist_item = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()

        if wishlist_item:
            # Remove from wishlist
            db.session.delete(wishlist_item)
            message = 'Product removed from wishlist'
            in_wishlist = False
        else:
            # Add to wishlist
            wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
            db.session.add(wishlist_item)
            message = 'Product added to wishlist'
            in_wishlist = True

        db.session.commit()
        
        # Get updated wishlist total
        wishlist_total = Wishlist.query.filter_by(user_id=current_user.id).count()
        
        return jsonify({
            'success': True,
            'message': message,
            'in_wishlist': in_wishlist,
            'wishlist_total': wishlist_total
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error toggling wishlist: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while updating wishlist'
        }), 500

@bp.route('/wishlist/check/<int:product_id>')
@login_required
def check_wishlist(product_id):
    """Check if product is in wishlist"""
    try:
        wishlist_item = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()
        
        return jsonify({
            'success': True,
            'in_wishlist': wishlist_item is not None
        })
    except Exception as e:
        current_app.logger.error(f'Error in check_wishlist: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'An error occurred while checking wishlist status'
        }), 500

@bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    """Add product to wishlist route"""
    try:
        product = Product.query.get_or_404(product_id)
        wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        
        if wishlist_item:
            return jsonify({'success': False, 'message': 'Product already in wishlist'}), 400
        
        wishlist_item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Product added to wishlist'})
    except Exception as e:
        current_app.logger.error(f'Error in add_to_wishlist route: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/wishlist/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_wishlist(item_id):
    """Remove product from wishlist route"""
    try:
        wishlist_item = Wishlist.query.get_or_404(item_id)
        if wishlist_item.user_id != current_user.id:
            flash('You are not authorized to remove this item.', 'danger')
            return redirect(url_for('bp.wishlist'))
        
        db.session.delete(wishlist_item)
        db.session.commit()
        flash('Item removed from wishlist.', 'success')
        return redirect(url_for('bp.wishlist'))
    except Exception as e:
        current_app.logger.error(f'Error in remove_from_wishlist route: {str(e)}')
        db.session.rollback()
        return render_template('errors/500.html'), 500

@bp.route('/review/add/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    """Add product review route"""
    try:
        product = Product.query.get_or_404(product_id)
        form = ReviewForm()
        
        if form.validate_on_submit():
            review = Review(
                user_id=current_user.id,
                product_id=product_id,
                rating=form.rating.data,
                comment=form.comment.data
            )
            db.session.add(review)
            db.session.commit()
            
            flash('Review added successfully', 'success')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{getattr(form, field).label.text}: {error}', 'error')
        
        return redirect(url_for('main.product_detail', product_id=product_id))
    except Exception as e:
        current_app.logger.error(f'Error in add_review route: {str(e)}')
        db.session.rollback()
        flash('An error occurred while adding your review', 'error')
        return redirect(url_for('main.product_detail', product_id=product_id))

@bp.route('/about')
def about():
    """About page route"""
    return render_template('main/about.html')

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page route"""
    form = ContactForm()
    if form.validate_on_submit():
        msg = Message(
            subject=f"Contact Form - {form.subject.data}",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[current_app.config['MAIL_DEFAULT_SENDER']],
            body=f"""
            From: {form.name.data} <{form.email.data}>
            Subject: {form.subject.data}
            Message: {form.message.data}
            """
        )
        mail.send(msg)
        flash('Your message has been sent. Thank you!', 'success')
        return redirect(url_for('bp.contact'))
    return render_template('main/contact.html', form=form)

@bp.route('/privacy')
def privacy():
    """Privacy policy page route"""
    return render_template('main/privacy.html')

@bp.route('/terms')
def terms():
    """Terms of service page route"""
    return render_template('main/terms.html')

@bp.route('/checkout')
@login_required
def checkout():
    """Checkout page route"""
    try:
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
                            discount=0)
    except Exception as e:
        current_app.logger.error(f'Error in checkout route: {str(e)}')
        return render_template('errors/500.html'), 500

@bp.route('/api/product/<int:product_id>')
def get_product_details(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.price),
                'stock': product.stock,
                'image_url': product.image_url,
                'category_name': product.category.name if product.category else None
            }
        })
    except Exception as e:
        current_app.logger.error(f'Error getting product details: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Failed to load product details'
        }), 500
