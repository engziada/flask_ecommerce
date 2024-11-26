from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.category import Category
from app.models.user import User
from app.models.order import Order
from app.extensions import db
from functools import wraps
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime

bp = Blueprint('admin', __name__)

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

@bp.route('/product/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_product():
    """Create new product page"""
    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            description=request.form['description'],
            price=float(request.form['price']),
            stock=int(request.form['stock']),
            category_id=int(request.form['category_id']),
            sku=request.form.get('sku'),
            weight=float(request.form.get('weight', 0)),
            dimensions=request.form.get('dimensions'),
            is_active=bool(request.form.get('is_active'))
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
    
    categories = Category.query.all()
    return render_template('admin/product_form.html', categories=categories)

@bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    """Edit product page"""
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock = int(request.form['stock'])
        product.category_id = int(request.form['category_id'])
        product.sku = request.form.get('sku')
        product.weight = float(request.form.get('weight', 0))
        product.dimensions = request.form.get('dimensions')
        product.is_active = bool(request.form.get('is_active'))

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
    
    categories = Category.query.all()
    return render_template('admin/product_form.html', product=product, categories=categories)

@bp.route('/product/<int:product_id>/delete', methods=['POST'])
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
    return render_template('admin/categories.html', categories=categories)

@bp.route('/category/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    """Create new category page"""
    if request.method == 'POST':
        category = Category(name=request.form['name'])
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html')

@bp.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    """Edit category page"""
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        category.name = request.form['name']
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=category)

@bp.route('/category/<int:category_id>/delete', methods=['POST'])
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
    status_filter = request.args.get('status', None)
    
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    orders = query.order_by(Order.date_created.desc()).paginate(
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
def update_order_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        flash('Invalid status', 'error')
        return redirect(url_for('admin.order_detail', order_id=order_id))
    
    # Check if the status transition is valid
    current_status = order.status
    valid_transitions = {
        'pending': ['processing', 'cancelled'],
        'processing': ['shipped', 'cancelled'],
        'shipped': ['delivered', 'cancelled'],
        'delivered': [],  # Final state
        'cancelled': []   # Final state
    }
    
    if new_status not in valid_transitions.get(current_status, []):
        flash(f'Cannot change order status from {current_status} to {new_status}', 'error')
        return redirect(url_for('admin.order_detail', order_id=order_id))
    
    try:
        order.status = new_status
        order.date_updated = datetime.utcnow()
        db.session.commit()
        flash(f'Order status updated to {new_status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating order status', 'error')
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

@bp.route('/users')
@login_required
@admin_required
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users)

@bp.route('/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(user_id):
    """Toggle user's admin status"""
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin status from the last admin
    if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
        flash('Cannot remove admin status from the last admin!', 'danger')
        return redirect(url_for('admin.users'))
    
    # Prevent self-demotion
    if user == current_user:
        flash('You cannot change your own admin status!', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"{'Removed admin status from' if not user.is_admin else 'Made'} {user.name} {'an admin' if user.is_admin else ''} successfully!", 'success')
    return redirect(url_for('admin.users'))
