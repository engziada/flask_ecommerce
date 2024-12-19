from flask import render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.category import Category
from app.models.user import User
from app.models.order import Order
from app.models.coupon import Coupon
from app.extensions import db, csrf
from functools import wraps
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime
from . import bp
from .forms import CategoryForm, ProductForm

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['jpg', 'jpeg', 'png', 'gif']

@bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard"""
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    recent_orders = Order.query.order_by(Order.date_created.desc()).limit(5).all()
    return render_template('admin/index.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         recent_orders=recent_orders)

@bp.route('/products')
@login_required
@admin_required
def products():
    """Product management page"""
    page = request.args.get('page', 1, type=int)
    products = Product.query.paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/products.html', products=products)

@bp.route('/products/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_product():
    """Create new product page"""
    form = ProductForm()
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            category_id=form.category_id.data,
            sku=form.sku.data,
            weight=form.weight.data,
            dimensions=form.dimensions.data,
            is_active=form.is_active.data
        )

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                product.image_url = url_for('static', filename=f'uploads/{filename}')

        db.session.add(product)
        db.session.commit()
        flash('Product created successfully!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', form=form)

@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    """Edit product page"""
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        form.populate_obj(product)

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                product.image_url = url_for('static', filename=f'uploads/{filename}')

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', form=form, product=product)

@bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    """Delete product"""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.products'))

@bp.route('/categories')
@login_required
@admin_required
def categories():
    """Category management page"""
    categories = Category.query.all()
    
    # Update any categories missing timestamps
    from datetime import datetime
    update_needed = False
    for category in categories:
        if not category.created_at:
            category.created_at = datetime.utcnow()
            category.updated_at = category.created_at
            update_needed = True
    
    if update_needed:
        db.session.commit()
        
    return render_template('admin/categories.html', categories=categories)

@bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    """Create new category page"""
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', form=form)

@bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    """Edit category page"""
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        category.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=category, form=form)

@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """Delete category"""
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin.categories'))

@bp.route('/orders')
@login_required
@admin_required
def orders():
    """Order management page"""
    page = request.args.get('page', 1, type=int)
    orders = Order.query.order_by(Order.date_created.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/orders.html', orders=orders)

@bp.route('/orders/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    """Order detail page"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def update_order_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    
    if not order.can_update_status:
        flash('This order was cancelled by the user and cannot be modified.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
    
    status = request.form.get('status')
    if status not in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
        flash('Invalid status.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
    
    if status == 'cancelled':
        order.cancel_order('admin')
    else:
        order.status = status
        db.session.commit()
    
    flash(f'Order status updated to {status}.', 'success')
    return redirect(url_for('admin.order_detail', order_id=order.id))

@bp.route('/orders/<int:order_id>/update_payment_status', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def update_payment_status(order_id):
    """Update payment status for COD orders"""
    order = Order.query.get_or_404(order_id)
    
    if order.payment_method != 'COD':
        flash('This action is only available for Cash on Delivery orders.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order_id))
    
    order.payment_status = 'paid'
    order.date_updated = datetime.utcnow()
    db.session.commit()
    
    flash('Payment status updated successfully.', 'success')
    return redirect(url_for('admin.order_detail', order_id=order_id))

@bp.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users)

@bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin status from the last admin
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot remove admin status from the last admin!', 'danger')
        return redirect(url_for('admin.users'))
    
    # Prevent self-demotion
    if user == current_user:
        flash("You cannot change your own admin status!", 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    full_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.email
    flash(f"{'Removed admin status from' if not user.is_admin else 'Made'} {full_name} {'an admin' if user.is_admin else ''} successfully!", 'success')
    return redirect(url_for('admin.users'))

@bp.route('/coupons')
@login_required
@admin_required
def coupons():
    """Coupon management page"""
    coupons = Coupon.query.all()
    return render_template('admin/coupons.html', coupons=[c.to_dict() for c in coupons])

@bp.route('/api/coupons', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_coupons():
    """Manage coupons - list, create"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate input
            if not data.get('code'):
                return jsonify({'success': False, 'error': 'Coupon code is required'})
                
            if not data.get('discount_type') in ['percentage', 'fixed', 'free_shipping']:
                return jsonify({'success': False, 'error': 'Invalid discount type'})
            
            # Create new coupon
            coupon = Coupon(
                code=data['code'],
                discount_type=data['discount_type'],
                discount_amount=float(data.get('discount_amount', 0)),
                min_purchase_amount=float(data.get('min_purchase_amount', 0)),
                max_discount_amount=float(data.get('max_discount_amount')) if data.get('max_discount_amount') else None,
                valid_from=datetime.fromisoformat(data['valid_from']) if data.get('valid_from') else None,
                valid_until=datetime.fromisoformat(data['valid_until']) if data.get('valid_until') else None,
                usage_limit=int(data['usage_limit']) if data.get('usage_limit') else None
            )
            db.session.add(coupon)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
            
    # GET request - return all coupons
    coupons = Coupon.query.all()
    return jsonify([c.to_dict() for c in coupons])

@bp.route('/api/coupons/<int:coupon_id>', methods=['PUT', 'DELETE'])
@login_required
@admin_required
def manage_coupon(coupon_id):
    """Manage single coupon - update, delete"""
    try:
        coupon = Coupon.query.get_or_404(coupon_id)
        
        if request.method == 'DELETE':
            db.session.delete(coupon)
            db.session.commit()
            return jsonify({'success': True})
            
        # PUT request
        data = request.get_json()
        
        # Validate input
        if not data.get('code'):
            return jsonify({'success': False, 'error': 'Coupon code is required'})
            
        if not data.get('discount_type') in ['percentage', 'fixed', 'free_shipping']:
            return jsonify({'success': False, 'error': 'Invalid discount type'})
            
        # Check if the new code already exists (excluding current coupon)
        existing_coupon = Coupon.query.filter(
            Coupon.code == data['code'].upper(),
            Coupon.id != coupon_id
        ).first()
        if existing_coupon:
            return jsonify({'success': False, 'error': 'A coupon with this code already exists'})
            
        if data['discount_type'] != 'free_shipping':
            try:
                discount_amount = float(data.get('discount_amount', 0))
                if data['discount_type'] == 'percentage' and (discount_amount <= 0 or discount_amount > 100):
                    return jsonify({'success': False, 'error': 'Percentage discount must be between 0 and 100'})
                elif data['discount_type'] == 'fixed' and discount_amount <= 0:
                    return jsonify({'success': False, 'error': 'Fixed discount amount must be greater than 0'})
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid discount amount'})
        
        # Update coupon
        coupon.code = data['code']
        coupon.discount_type = data['discount_type']
        coupon.discount_amount = float(data.get('discount_amount', 0))
        coupon.min_purchase_amount = float(data.get('min_purchase_amount', 0))
        coupon.max_discount_amount = float(data.get('max_discount_amount')) if data.get('max_discount_amount') else None
        coupon.valid_from = datetime.fromisoformat(data['valid_from']) if data.get('valid_from') else None
        coupon.valid_until = datetime.fromisoformat(data['valid_until']) if data.get('valid_until') else None
        coupon.usage_limit = int(data['usage_limit']) if data.get('usage_limit') else None
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
