from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.address import Address
from app.extensions import db
from app.address import bp

@bp.route('/')
@login_required
def addresses():
    """Display user's addresses"""
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template('address/addresses.html', addresses=addresses)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_address():
    """Add new address"""
    if request.method == 'POST':
        try:
            address = Address(
                user_id=current_user.id,
                name=request.form.get('name'),
                phone=request.form.get('phone'),
                address_line1=request.form.get('address_line1'),
                address_line2=request.form.get('address_line2'),
                city=request.form.get('city'),
                state=request.form.get('state'),
                postal_code=request.form.get('postal_code'),
                country=request.form.get('country', 'US'),
                is_default=bool(request.form.get('is_default'))
            )
            
            if address.is_default:
                # Set all other addresses as non-default
                Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
            
            db.session.add(address)
            db.session.commit()
            flash('Address added successfully!', 'success')
            
            # If this is part of checkout process, redirect back
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('address.addresses'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding address. Please try again.', 'danger')
    
    return render_template('address/address_form.html')

@bp.route('/edit/<int:address_id>', methods=['GET', 'POST'])
@login_required
def edit_address(address_id):
    """Edit address"""
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            address.name = request.form.get('name')
            address.phone = request.form.get('phone')
            address.address_line1 = request.form.get('address_line1')
            address.address_line2 = request.form.get('address_line2')
            address.city = request.form.get('city')
            address.state = request.form.get('state')
            address.postal_code = request.form.get('postal_code')
            address.country = request.form.get('country', 'US')
            
            new_is_default = bool(request.form.get('is_default'))
            if new_is_default and not address.is_default:
                # Set all other addresses as non-default
                Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
            address.is_default = new_is_default
            
            db.session.commit()
            flash('Address updated successfully!', 'success')
            return redirect(url_for('address.addresses'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating address. Please try again.', 'danger')
    
    return render_template('address/address_form.html', address=address)

@bp.route('/delete/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    """Delete address"""
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(address)
        db.session.commit()
        flash('Address deleted successfully.', 'success')
    except:
        db.session.rollback()
        flash('Error deleting address.', 'danger')
    
    return redirect(url_for('address.addresses'))

@bp.route('/set-default/<int:address_id>', methods=['POST'])
@login_required
def set_default_address(address_id):
    """Set address as default"""
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    
    try:
        # Set all addresses as non-default
        Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
        # Set selected address as default
        address.is_default = True
        db.session.commit()
        return jsonify({'success': True, 'message': 'Default address updated.'})
    except:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating default address.'})
