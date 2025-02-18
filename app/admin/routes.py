from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import os
import logging
import sys
from datetime import datetime, timedelta

from app.models.product import Product, ProductImage
from app.models.category import Category
from app.models.user import User
from app.models.order import Order
from app.models.coupon import Coupon
from app.models.shipping import ShippingCarrier, ShippingMethod
from app.shipping.services import BostaShippingService
from app.utils import allowed_file
from app.decorators import admin_required
from app.extensions import db, csrf
from functools import wraps
from . import bp
from .forms import CategoryForm, ProductForm

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
    show_deleted = request.args.get('show_deleted', 'all')  # Options: 'all', 'active', 'deleted'
    
    query = Product.query
    
    if show_deleted == 'active':
        query = query.filter_by(is_deleted=False)
    elif show_deleted == 'deleted':
        query = query.filter_by(is_deleted=True)
    
    products = query.paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/products.html', products=products, show_deleted=show_deleted)

@bp.route('/products/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_product():
    """Create new product page"""
    form = ProductForm()
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if request.method == 'POST':
        current_app.logger.info('Form submitted')
        current_app.logger.info(f'Form data: {request.form}')
        current_app.logger.info(f'Files: {request.files}')
        
        if not form.validate():
            current_app.logger.error('Form validation failed')
            for field, errors in form.errors.items():
                for error in errors:
                    current_app.logger.error(f'Error in {field}: {error}')
                    flash(f'Error in {field}: {error}', 'error')
            return render_template('admin/product_form.html', form=form)

        try:
            # Create the product
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
            db.session.add(product)
            db.session.flush()  # Get product ID without committing

            # Handle images
            primary_set = False
            for image_form in form.images:
                if image_form.image.data:
                    file = image_form.image.data
                    current_app.logger.info(f'Processing image: {file.filename}')
                    
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        current_app.logger.info(f'Saving file to: {file_path}')
                        
                        # Ensure upload directory exists
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        file.save(file_path)
                        
                        # If no primary image is set, make the first one primary
                        if not primary_set and image_form.is_primary.data:
                            is_primary = True
                            primary_set = True
                        elif not primary_set and not any(f.is_primary.data for f in form.images):
                            is_primary = True
                            primary_set = True
                        else:
                            is_primary = image_form.is_primary.data

                        image = ProductImage(
                            image_url=f'/static/uploads/{filename}',
                            product_id=product.id,
                            is_primary=is_primary
                        )
                        db.session.add(image)
                        current_app.logger.info(f'Added image to database: {filename}')

            db.session.commit()
            flash('Product created successfully!', 'success')
            return redirect(url_for('admin.products'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating product: {str(e)}')
            current_app.logger.exception('Full traceback:')
            flash('An error occurred while creating the product.', 'error')

    return render_template('admin/product_form.html', form=form)

@bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    """Edit product page"""
    # Set up detailed logging
    import logging
    import sys
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Add file handler for detailed logging
    log_file = os.path.join('logs', 'product_edit.log')
    fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Add console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # Start logging
    logger.info('='*80)
    logger.info(f'Starting edit_product for product_id: {product_id}')
    
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.product_id = product_id
    categories = Category.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if request.method == 'GET':
        logger.debug('GET request - preparing form')
        # Clear existing form entries
        while len(form.images) > 0:
            form.images.pop_entry()

        # Populate images
        for image in product.images:
            logger.debug(f'Adding existing image to form: {image.image_url}, is_primary: {image.is_primary}')
            form.images.append_entry({
                'image': None,  # Don't populate the FileField
                'is_primary': image.is_primary
            })

    if request.method == 'POST':
        logger.debug('POST request received')
        logger.debug(f'Form data: {request.form}')
        logger.debug(f'Files: {[(k, v.filename) for k, v in request.files.items() if v.filename]}')
        
    if form.validate_on_submit():
        logger.info('Form validation successful')
        try:
            # Update basic product info
            logger.debug('Updating basic product info')
            product.name = form.name.data
            product.description = form.description.data
            product.price = form.price.data
            product.stock = form.stock.data
            product.category_id = form.category_id.data
            product.sku = form.sku.data.strip().upper() if form.sku.data else None
            product.weight = form.weight.data
            product.dimensions = form.dimensions.data
            product.is_active = form.is_active.data
            
            # Process images
            processed_urls = set()
            primary_set = False
            
            # First, handle existing images
            logger.debug('Processing existing images')
            for key, value in request.form.items():
                if key.startswith('existing_images-'):
                    logger.debug(f'Found existing image form key: {key} with value: {value}')
                    idx = key.split('-')[1]
                    image_url = value
                    is_primary = request.form.get(f'images-{idx}-is_primary') == 'y'
                    logger.debug(f'Processing existing image: {image_url}, is_primary: {is_primary}')
                    
                    # Find the image in our database
                    for img in product.images:
                        if img.image_url == image_url:
                            logger.debug(f'Found matching image in database: {img.image_url}')
                            img.is_primary = is_primary
                            if is_primary:
                                logger.debug('Setting as primary image')
                                # Set other images as non-primary
                                for other_img in product.images:
                                    if other_img != img:
                                        other_img.is_primary = False
                                primary_set = True
                            processed_urls.add(image_url)
                            break

            # Delete images that are not in the form
            logger.debug(f'Processed URLs: {processed_urls}')
            logger.debug(f'Current product images: {[img.image_url for img in product.images]}')
            for img in list(product.images):  # Create a copy of the list since we're modifying it
                if img.image_url not in processed_urls:
                    logger.debug(f'Deleting image not in form: {img.image_url}')
                    try:
                        # Delete the actual file if it exists
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(img.image_url))
                        logger.debug(f'Attempting to delete file: {file_path}')
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logger.debug(f'Successfully deleted file: {file_path}')
                        db.session.delete(img)
                    except Exception as e:
                        logger.error(f'Error deleting image file: {str(e)}', exc_info=True)
                        # Continue with the update even if file deletion fails
            
            # Then handle new images
            logger.debug('Processing new images')
            for idx, image_form in enumerate(form.images):
                logger.debug(f'Processing image form at index {idx}')
                if image_form.image.data and isinstance(image_form.image.data, FileStorage):
                    file = image_form.image.data
                    logger.debug(f'Found new image file: {file.filename}')
                    if allowed_file(file.filename):
                        try:
                            filename = secure_filename(file.filename)
                            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                            logger.debug(f'Saving new file to: {file_path}')
                            file.save(file_path)
                            image_url = f'/static/uploads/{filename}'
                            
                            # Create new image
                            new_image = ProductImage(
                                image_url=image_url,
                                product_id=product.id,
                                is_primary=image_form.is_primary.data and not primary_set
                            )
                            if new_image.is_primary:
                                logger.debug('Setting new image as primary')
                                # Set other images as non-primary
                                for img in product.images:
                                    img.is_primary = False
                                primary_set = True
                            db.session.add(new_image)
                            logger.debug(f'Successfully added new image: {image_url}')
                        except Exception as e:
                            logger.error(f'Error saving new image: {str(e)}', exc_info=True)
                            raise
            
            # Ensure at least one image is primary if there are any images
            if product.images.count() > 0 and not primary_set:
                logger.debug('No primary image set, setting first image as primary')
                first_image = product.images.first()
                if first_image:
                    first_image.is_primary = True
                    for other_img in product.images:
                        if other_img != first_image:
                            other_img.is_primary = False

            logger.debug('Committing changes to database')
            db.session.commit()
            logger.info('Product updated successfully')
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin.products'))
        except Exception as e:
            db.session.rollback()
            logger.error('Error updating product', exc_info=True)
            logger.error(f'Exception details: {str(e)}')
            flash('An error occurred while updating the product.', 'error')
    else:
        if request.method == 'POST':
            logger.error('Form validation failed')
            logger.error(f'Form errors: {form.errors}')
            flash('Please correct the errors below.', 'error')

    return render_template('admin/product_form.html', form=form, product=product)

@bp.route('/products/<int:product_id>/images/<int:image_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product_image(product_id, image_id):
    """Delete a product image"""
    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Add file handler
    fh = logging.FileHandler('logs/product_edit.log')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    logger.debug(f'Deleting image {image_id} from product {product_id}')
    
    try:
        product = Product.query.get_or_404(product_id)
        image = ProductImage.query.get_or_404(image_id)
        
        if image.product_id != product.id:
            logger.error(f'Image {image_id} does not belong to product {product_id}')
            flash('Image does not belong to this product.', 'error')
            return redirect(url_for('admin.edit_product', product_id=product_id))
        
        # If this was the primary image, set another image as primary
        if image.is_primary and product.images.count() > 1:
            next_image = ProductImage.query.filter(
                ProductImage.product_id == product_id,
                ProductImage.id != image_id
            ).first()
            if next_image:
                next_image.is_primary = True
                logger.debug(f'Set image {next_image.id} as new primary image')
        
        # Delete the image file if it exists
        if image.image_url:
            try:
                file_path = os.path.join(
                    current_app.root_path,
                    'static',
                    image.image_url.replace('/static/', '')
                )
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f'Deleted image file: {file_path}')
            except Exception as e:
                logger.error(f'Error deleting image file: {str(e)}')
        
        db.session.delete(image)
        db.session.commit()
        logger.debug('Successfully deleted image from database')
        flash('Image deleted successfully.', 'success')
        
    except Exception as e:
        logger.error(f'Error deleting image: {str(e)}', exc_info=True)
        db.session.rollback()
        flash(f'Error deleting image: {str(e)}', 'error')
    
    return redirect(url_for('admin.edit_product', product_id=product_id))

@bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    """Soft delete product by marking it as deleted"""
    product = Product.query.get_or_404(product_id)
    product.is_deleted = True
    product.is_active = False  # Also deactivate the product
    db.session.commit()
    flash('Product has been marked as deleted.', 'success')
    return redirect(url_for('admin.products'))

@bp.route('/products/<int:product_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_product(product_id):
    """Restore a deleted product"""
    product = Product.query.get_or_404(product_id)
    if not product.is_deleted:
        flash('Product is not deleted.', 'warning')
        return redirect(url_for('admin.products'))
    
    product.is_deleted = False
    product.is_active = True  # Also reactivate the product
    db.session.commit()
    flash('Product has been restored successfully.', 'success')
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

@bp.route('/orders/<int:order_id>/confirm', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def confirm_order(order_id):
    """Confirm order and create Bosta shipping order"""
    order = Order.query.get_or_404(order_id)
    
    if not order.can_update_status:
        flash('This order cannot be modified.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
        
    if order.status != 'pending':
        flash('Only pending orders can be confirmed.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
    
    try:
        # Get Bosta carrier
        bosta_carrier = ShippingCarrier.query.filter_by(code='bosta').first()
        if not bosta_carrier:
            raise ValueError("Bosta shipping carrier not found")
            
        # Get standard shipping method
        shipping_method = ShippingMethod.query.filter_by(carrier_id=bosta_carrier.id, code='standard').first()
        if not shipping_method:
            raise ValueError("Standard shipping method not found")
            
        # Set shipping carrier and method
        order.shipping_carrier = bosta_carrier
        order.shipping_method = shipping_method
        
        # Create Bosta shipping order
        bosta_service = BostaShippingService()
        shipping_result = bosta_service.create_shipping_order(order)
        
        # Update order with Bosta details
        order.delivery_tracking_number = shipping_result.get('tracking_number')
        order.delivery_id = shipping_result.get('delivery_id')
        order.delivery_status = shipping_result.get('status')
        order.delivery_status_code = shipping_result.get('status_code')
        order.delivery_created_at = datetime.utcnow()
        order.status = 'processing'
        db.session.commit()
        
        flash('Order confirmed and shipping created successfully.', 'success')
    except Exception as e:
        current_app.logger.error(f'Error creating Bosta shipping order: {str(e)}')
        flash('Failed to create shipping order. Please try again.', 'error')
        
    return redirect(url_for('admin.order_detail', order_id=order.id))

@bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def cancel_order(order_id):
    """Cancel the order"""
    order = Order.query.get_or_404(order_id)
    
    if not order.can_update_status:
        flash('This order cannot be modified.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
        
    if order.status not in ['pending', 'processing']:
        flash('Only pending or processing orders can be cancelled.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
    
    try:
        # If order has a Bosta delivery, cancel it first
        if order.delivery_id:
            try:
                bosta_service = BostaShippingService()
                bosta_service.cancel_shipping_order(order.delivery_id)
                current_app.logger.info(f"Successfully cancelled Bosta delivery for order {order.id}")
            except Exception as e:
                current_app.logger.error(f"Failed to cancel Bosta delivery for order {order.id}: {str(e)}")
                flash('Failed to cancel shipping delivery. Please try again or contact support.', 'error')
                return redirect(url_for('admin.order_detail', order_id=order.id))
        
        # Cancel the order in our system
        order.cancel_order('admin')
        flash('Order cancelled successfully.', 'success')
        
    except Exception as e:
        current_app.logger.error(f"Error cancelling order {order.id}: {str(e)}")
        flash('An error occurred while cancelling the order. Please try again.', 'error')
        
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

@bp.route('/orders/<int:order_id>/mark_shipped', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def mark_order_shipped(order_id):
    """Mark order as shipped"""
    order = Order.query.get_or_404(order_id)
    
    if not order.can_update_status:
        flash('This order cannot be modified.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
        
    if order.status != 'processing':
        flash('Only processing orders can be marked as shipped.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
    
    try:
        order.status = 'shipped'
        db.session.commit()
        flash('Order marked as shipped successfully.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error marking order {order.id} as shipped: {str(e)}")
        flash('An error occurred while updating the order. Please try again.', 'error')
        
    return redirect(url_for('admin.order_detail', order_id=order.id))

@bp.route('/orders/<int:order_id>/mark_delivered', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def mark_order_delivered(order_id):
    """Mark order as delivered"""
    order = Order.query.get_or_404(order_id)
    
    if not order.can_update_status:
        flash('This order cannot be modified.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
        
    if order.status != 'shipped':
        flash('Only shipped orders can be marked as delivered.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order.id))
    
    try:
        order.status = 'delivered'
        db.session.commit()
        flash('Order marked as delivered successfully.', 'success')
    except Exception as e:
        current_app.logger.error(f"Error marking order {order.id} as delivered: {str(e)}")
        flash('An error occurred while updating the order. Please try again.', 'error')
        
    return redirect(url_for('admin.order_detail', order_id=order.id))

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
            
            # Convert valid_from and valid_until to UTC
            valid_from = datetime.fromisoformat(data.get('valid_from')) if data.get('valid_from') else datetime.utcnow()
            valid_until = datetime.fromisoformat(data.get('valid_until')) if data.get('valid_until') else None
            
            # Subtract 2 hours to convert from UTC+2 to UTC
            valid_from = valid_from - timedelta(hours=2)
            if valid_until:
                valid_until = valid_until - timedelta(hours=2)
            
            coupon = Coupon(
                code=data.get('code'),
                discount_type=data.get('discount_type'),
                discount_amount=float(data.get('discount_amount', 0)),
                min_purchase_amount=float(data.get('min_purchase_amount', 0)),
                max_discount_amount=float(data.get('max_discount_amount')) if data.get('max_discount_amount') else None,
                valid_from=valid_from,
                valid_until=valid_until,
                usage_limit=int(data.get('usage_limit')) if data.get('usage_limit') else None
            )
            
            db.session.add(coupon)
            db.session.commit()
            
            return jsonify({'success': True})
            
        except Exception as e:
            current_app.logger.error(f"Error creating coupon: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
            
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
