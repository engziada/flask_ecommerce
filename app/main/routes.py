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
from datetime import datetime, timedelta
from app.main import bp
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
    def is_admin():
        return current_user.is_authenticated and current_user.is_admin
        
    return {
        'cart_total': getattr(g, 'cart_total', 0),
        'wishlist_total': getattr(g, 'wishlist_total', 0),
        'is_admin': is_admin,
    }

@bp.route('/')
@bp.route('/index')
@bp.route('/home')
def index():
    """Home page route"""
    try:
        return render_template('main/index.html')
    except Exception as e:
        current_app.logger.error(f'Error in index route: {str(e)}')
        return render_template('errors/500.html'), 500

@bp.route('/shop')
def shop():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'default')
    
    # Base query
    query = Product.query.filter_by(is_active=True, is_deleted=False)
    
    # Apply sorting
    if sort_by == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.created_at.desc())
    elif sort_by == 'name_asc':
        query = query.order_by(Product.name.asc())
    elif sort_by == 'name_desc':
        query = query.order_by(Product.name.desc())
    
    # Paginate results
    products = query.paginate(
        page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12)
    )
    
    categories = Category.query.all()
    
    # Get wishlist items for the current user
    wishlist_items = set()
    if current_user.is_authenticated:
        wishlist_items = {item.product_id for item in Wishlist.query.filter_by(user_id=current_user.id).all()}
    
    # Check if any product is new
    current_time = datetime.now()
    thirty_days_ago = current_time - timedelta(days=30)
    for product in products:
        product.is_new = product.created_at >= thirty_days_ago
    
    return render_template('main/shop.html', 
                         products=products, 
                         categories=categories,
                         wishlist_items=wishlist_items,
                         sort_by=sort_by)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    current_app.logger.debug(f'Accessing product detail for product_id: {product_id}')
    
    product = Product.query.filter_by(id=product_id, is_deleted=False).first_or_404()
    current_app.logger.debug(f'Found product: {product.name}')
    current_app.logger.debug(f'Product has {product.images.count()} images')
    
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    form = ReviewForm()
    
    current_app.logger.debug(f'Product has {len(reviews)} reviews')
    return render_template('main/product_detail.html', product=product, reviews=reviews, form=form)

# @bp.route('/category/<int:category_id>')
# def category_products(category_id):
#     page = request.args.get('page', 1, type=int)
#     category = Category.query.get_or_404(category_id)
#     products = Product.query.filter_by(category_id=category_id, is_active=True, is_deleted=False).paginate(
#         page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12)
#     )
#     return render_template('main/category_products.html', 
#                          category=category, 
#                          products=products)

@bp.route('/category/<int:category_id>')
def category_products(category_id):
    page = request.args.get('page', 1, type=int)
    category = Category.query.get_or_404(category_id)
    products = Product.query.filter_by(category_id=category_id, is_active=True, is_deleted=False).paginate(
        page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12)
    )
    categories = Category.query.all()
    
    # Get wishlist items for the current user (same as shop route)
    wishlist_items = set()
    if current_user.is_authenticated:
        wishlist_items = {item.product_id for item in Wishlist.query.filter_by(user_id=current_user.id).all()}
    
    return render_template('main/shop.html', 
                         products=products, 
                         categories=categories,
                         category=category,
                         wishlist_items=wishlist_items)

@bp.route('/search')
def search():
    """Search products page"""
    query = request.args.get('q', '')
    current_app.logger.debug(f'Search query: "{query}"')
    
    page = request.args.get('page', 1, type=int)
    products = Product.query.filter(
        Product.is_deleted == False,
        Product.is_active == True,
        (Product.name.ilike(f'%{query}%') | Product.description.ilike(f'%{query}%'))
    ).paginate(page=page, per_page=current_app.config.get('PRODUCTS_PER_PAGE', 12))
    
    current_app.logger.debug(f'Found {products.total} products matching search')
    current_app.logger.debug(f'Displaying page {page} of {products.pages}')
    
    return render_template('main/search.html', products=products, query=query)

@bp.route('/review/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    """Add product review route"""
    product = Product.query.get_or_404(product_id)
    form = ReviewForm()
    
    if form.validate_on_submit():
        try:
            review = Review(
                user_id=current_user.id,
                product_id=product_id,
                rating=form.rating.data,
                comment=form.comment.data
            )
            db.session.add(review)
            db.session.commit()
            flash('Your review has been added!', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error adding review: {str(e)}')
            flash('Error adding review. Please try again.', 'danger')
    
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
        try:
            msg = Message(
                subject=f'Contact Form: {form.subject.data}',
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                recipients=[current_app.config['MAIL_DEFAULT_RECIPIENT']],
                body=f'From: {form.name.data} <{form.email.data}>\n\n{form.message.data}'
            )
            mail.send(msg)
            flash('Your message has been sent!', 'success')
            return redirect(url_for('main.contact'))
        except Exception as e:
            current_app.logger.error(f'Error sending contact email: {str(e)}')
            flash('Error sending message. Please try again later.', 'danger')
    
    return render_template('main/contact.html', form=form)

@bp.route('/privacy')
def privacy():
    """Privacy policy page route"""
    return render_template('main/privacy.html')

@bp.route('/terms')
def terms():
    """Terms of service page route"""
    return render_template('main/terms.html')

@bp.route('/get-product-details/<int:product_id>')
def get_product_details(product_id):
    """Get product details for quick view"""
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'success': True,
            'name': product.name,
            'price': float(product.price),
            'description': product.description,
            'image_url': product.image_url,
            'stock': product.stock,
            'category': product.category.name,
            'add_to_cart_url': url_for('cart.add_to_cart', product_id=product.id),
            'add_to_wishlist_url': url_for('wishlist.add_to_wishlist', product_id=product.id)
        })
    except Exception as e:
        current_app.logger.error(f'Error getting product details: {str(e)}')
        return jsonify({'success': False, 'error': 'Error getting product details'})

@bp.route('/api/counts')
@login_required
def get_counts():
    """Get cart and wishlist counts"""
    try:
        cart_count = Cart.query.filter_by(user_id=current_user.id).with_entities(
            func.sum(Cart.quantity)
        ).scalar() or 0
        
        wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()
        
        return jsonify({
            'cart_count': int(cart_count),
            'wishlist_count': wishlist_count
        })
    except Exception as e:
        current_app.logger.error(f"Error getting counts: {str(e)}")
        return jsonify({
            'cart_count': 0,
            'wishlist_count': 0
        }), 500
