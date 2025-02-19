from flask import jsonify, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from app.coupons import bp
from app.models.coupon import Coupon
from app.extensions import db
from app.utils.decorators import admin_required
from datetime import datetime, timedelta

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
def manage_coupons():
    """Manage coupons page (admin only)"""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    coupons = Coupon.query.all()
    return render_template('admin/coupons.html', 
                         coupons=coupons,
                         today=today,
                         tomorrow=tomorrow)

@bp.route('/admin/api/coupons', methods=['GET'])
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
        # Validate required fields
        required_fields = ['code', 'discount_type', 'discount_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate discount type
        valid_discount_types = ['percentage', 'fixed', 'free_shipping']
        if data['discount_type'] not in valid_discount_types:
            return jsonify({'error': f'Invalid discount type. Must be one of: {", ".join(valid_discount_types)}'}), 400
        
        # Validate discount amount
        try:
            discount_amount = float(data['discount_amount'])
            if discount_amount < 0:
                return jsonify({'error': 'Discount amount cannot be negative'}), 400
            if data['discount_type'] == 'percentage' and discount_amount > 100:
                return jsonify({'error': 'Percentage discount cannot exceed 100%'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid discount amount'}), 400
        
        # Convert date strings to datetime objects if provided
        valid_from = None
        valid_until = None
        
        if data.get('valid_from'):
            try:
                valid_from = datetime.fromisoformat(data['valid_from'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid valid_from date format'}), 400
                
        if data.get('valid_until'):
            try:
                valid_until = datetime.fromisoformat(data['valid_until'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid valid_until date format'}), 400
        
        # Check if coupon code already exists
        existing_coupon = Coupon.query.filter_by(code=data['code'].strip().upper()).first()
        if existing_coupon:
            return jsonify({'error': 'Coupon code already exists'}), 400
            
        coupon = Coupon(
            code=data['code'],
            discount_type=data['discount_type'],
            discount_amount=discount_amount,
            min_purchase_amount=float(data.get('min_purchase_amount', 0)),
            max_discount_amount=float(data['max_discount_amount']) if data.get('max_discount_amount') else None,
            valid_from=valid_from,
            valid_until=valid_until,
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
        # Validate discount type if provided
        if 'discount_type' in data:
            valid_discount_types = ['percentage', 'fixed', 'free_shipping']
            if data['discount_type'] not in valid_discount_types:
                return jsonify({'error': f'Invalid discount type. Must be one of: {", ".join(valid_discount_types)}'}), 400
        
        # Validate discount amount if provided
        if 'discount_amount' in data:
            try:
                discount_amount = float(data['discount_amount'])
                if discount_amount < 0:
                    return jsonify({'error': 'Discount amount cannot be negative'}), 400
                if data.get('discount_type', coupon.discount_type) == 'percentage' and discount_amount > 100:
                    return jsonify({'error': 'Percentage discount cannot exceed 100%'}), 400
                coupon.discount_amount = discount_amount
            except ValueError:
                return jsonify({'error': 'Invalid discount amount'}), 400
        
        # Update code if provided
        if 'code' in data:
            new_code = data['code'].strip().upper()
            existing_coupon = Coupon.query.filter(
                Coupon.code == new_code,
                Coupon.id != coupon_id
            ).first()
            if existing_coupon:
                return jsonify({'error': 'Coupon code already exists'}), 400
            coupon.code = new_code
            
        # Update other fields
        if 'discount_type' in data:
            coupon.discount_type = data['discount_type']
        if 'min_purchase_amount' in data:
            coupon.min_purchase_amount = float(data['min_purchase_amount'])
        if 'max_discount_amount' in data:
            coupon.max_discount_amount = float(data['max_discount_amount']) if data['max_discount_amount'] else None
            
        # Handle dates
        if 'valid_from' in data:
            try:
                coupon.valid_from = datetime.fromisoformat(data['valid_from'].replace('Z', '+00:00')) if data['valid_from'] else None
            except ValueError:
                return jsonify({'error': 'Invalid valid_from date format'}), 400
                
        if 'valid_until' in data:
            try:
                coupon.valid_until = datetime.fromisoformat(data['valid_until'].replace('Z', '+00:00')) if data['valid_until'] else None
            except ValueError:
                return jsonify({'error': 'Invalid valid_until date format'}), 400
                
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
