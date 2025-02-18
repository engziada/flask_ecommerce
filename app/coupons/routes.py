from flask import jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.coupons import bp
from app.models.coupon import Coupon
from app.extensions import db
from app.utils.decorators import admin_required
from datetime import datetime

@bp.route('/apply', methods=['POST'])
@login_required
def apply_coupon():
    """Apply a coupon code to the cart"""
    code = request.form.get('code', '').strip().upper()
    cart_total = float(request.form.get('cart_total', 0))
    
    if not code:
        return jsonify({'error': 'Please enter a coupon code'}), 400
        
    coupon = Coupon.query.filter_by(code=code).first()
    
    if not coupon:
        return jsonify({'error': 'Invalid coupon code'}), 404
        
    is_valid, message = coupon.is_valid(cart_total)
    if not is_valid:
        return jsonify({'error': message}), 400
        
    discount = coupon.calculate_discount(cart_total)
    new_total = cart_total - discount
    
    return jsonify({
        'success': True,
        'message': 'Coupon applied successfully!',
        'discount': discount,
        'new_total': new_total
    })

@bp.route('/admin/coupons', methods=['GET'])
@login_required
@admin_required
def list_coupons():
    """List all coupons (admin only)"""
    coupons = Coupon.query.all()
    return jsonify([coupon.to_dict() for coupon in coupons])

@bp.route('/admin/coupons', methods=['POST'])
@login_required
@admin_required
def create_coupon():
    """Create a new coupon (admin only)"""
    data = request.get_json()
    
    try:
        # Convert date strings to datetime objects
        if data.get('valid_from'):
            data['valid_from'] = datetime.fromisoformat(data['valid_from'])
        if data.get('valid_until'):
            data['valid_until'] = datetime.fromisoformat(data['valid_until'])
            
        coupon = Coupon(
            code=data['code'],
            discount_type=data['discount_type'],
            discount_amount=float(data['discount_amount']),
            min_purchase_amount=float(data.get('min_purchase_amount', 0)),
            max_discount_amount=float(data['max_discount_amount']) if data.get('max_discount_amount') else None,
            valid_from=data.get('valid_from'),
            valid_until=data.get('valid_until'),
            usage_limit=int(data['usage_limit']) if data.get('usage_limit') else None
        )
        
        db.session.add(coupon)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Coupon created successfully',
            'coupon': coupon.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/admin/coupons/<int:coupon_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_coupon(coupon_id):
    """Delete a coupon (admin only)"""
    coupon = Coupon.query.get_or_404(coupon_id)
    
    try:
        db.session.delete(coupon)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Coupon deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@bp.route('/admin/coupons/<int:coupon_id>', methods=['PUT'])
@login_required
@admin_required
def update_coupon(coupon_id):
    """Update a coupon (admin only)"""
    coupon = Coupon.query.get_or_404(coupon_id)
    data = request.get_json()
    
    try:
        if 'code' in data:
            coupon.code = data['code'].upper()
        if 'discount_type' in data:
            coupon.discount_type = data['discount_type']
        if 'discount_amount' in data:
            coupon.discount_amount = float(data['discount_amount'])
        if 'min_purchase_amount' in data:
            coupon.min_purchase_amount = float(data['min_purchase_amount'])
        if 'max_discount_amount' in data:
            coupon.max_discount_amount = float(data['max_discount_amount']) if data['max_discount_amount'] else None
        if 'valid_from' in data:
            coupon.valid_from = datetime.fromisoformat(data['valid_from'])
        if 'valid_until' in data:
            coupon.valid_until = datetime.fromisoformat(data['valid_until']) if data['valid_until'] else None
        if 'usage_limit' in data:
            coupon.usage_limit = int(data['usage_limit']) if data['usage_limit'] else None
        if 'is_active' in data:
            coupon.is_active = bool(data['is_active'])
            
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Coupon updated successfully',
            'coupon': coupon.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
