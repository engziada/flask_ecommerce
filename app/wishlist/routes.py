from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.product import Product
from app.models.wishlist import Wishlist
from app.extensions import db
from app.wishlist import bp

@bp.route('/')
@login_required
def wishlist():
    """Display user's wishlist"""
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('wishlist/wishlist.html', wishlist_items=wishlist_items)

@bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    """Add product to wishlist"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if product already in wishlist
        existing_item = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()
        
        if existing_item:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Product is already in your wishlist'
                })
            flash('Product is already in your wishlist.', 'info')
            return redirect(request.referrer or url_for('main.index'))
        
        wishlist_item = Wishlist(
            user_id=current_user.id,
            product_id=product_id
        )
        
        db.session.add(wishlist_item)
        db.session.commit()
        
        # Get updated wishlist total
        wishlist_total = Wishlist.query.filter_by(user_id=current_user.id).count()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Product added to wishlist',
                'wishlist_total': wishlist_total
            })
            
        flash('Product added to wishlist.', 'success')
        return redirect(request.referrer or url_for('main.index'))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Error adding product to wishlist'
            }), 500
            
        flash('Error adding product to wishlist.', 'danger')
        return redirect(request.referrer or url_for('main.index'))

@bp.route('/toggle/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist(product_id):
    """Toggle product in wishlist"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # Check if product already in wishlist
        wishlist_item = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()
        
        if wishlist_item:
            db.session.delete(wishlist_item)
            message = 'Product removed from wishlist'
            in_wishlist = False
        else:
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
        return jsonify({
            'success': False,
            'message': 'Error updating wishlist'
        }), 500

@bp.route('/check/<int:product_id>')
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
        return jsonify({
            'success': False,
            'message': 'Error checking wishlist status'
        }), 500
