from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.address import Address
from app.extensions import db
from app.address import bp
from app.address.forms import AddressForm

@bp.route('/')
@login_required
def addresses():
    """Display user's addresses"""
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template('address/addresses.html', addresses=addresses)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_address():
    form = AddressForm()
    if form.validate_on_submit():
        try:
            # Start a transaction
            db.session.begin_nested()
            
            # If this is the first address or set as default, update other addresses
            if form.is_default.data:
                Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
            
            # If this is the user's first address, make it default regardless
            if not Address.query.filter_by(user_id=current_user.id).first():
                form.is_default.data = True
            
            address = Address(
                user_id=current_user.id,
                name=form.name.data,
                phone=form.phone.data,
                street=form.street.data,
                building_number=form.building_number.data,
                floor=form.floor.data,
                apartment=form.apartment.data,
                city=form.city.data,
                district=form.district.data,
                postal_code=form.postal_code.data,
                is_default=form.is_default.data
            )
            
            db.session.add(address)
            db.session.commit()
            flash('Address added successfully!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('address.addresses'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding address: {str(e)}', 'danger')
    
    return render_template('address/address_form.html', form=form)

@bp.route('/edit/<int:address_id>', methods=['GET', 'POST'])
@login_required
def edit_address(address_id):
    """Edit address"""
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    form = AddressForm(obj=address)
    
    if form.validate_on_submit():
        try:
            # If setting as default, update other addresses
            if form.is_default.data and not address.is_default:
                Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
            
            form.populate_obj(address)
            db.session.commit()
            flash('Address updated successfully!', 'success')
            return redirect(url_for('address.addresses'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating address: {str(e)}', 'danger')
    
    return render_template('address/address_form.html', form=form, address=address)

@bp.route('/delete/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    """Delete address"""
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
    
    try:
        was_default = address.is_default
        db.session.delete(address)
        
        # If the deleted address was default, set the first remaining address as default
        if was_default:
            remaining_address = Address.query.filter_by(user_id=current_user.id).first()
            if remaining_address:
                remaining_address.is_default = True
        
        db.session.commit()
        flash('Address deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting address: {str(e)}', 'danger')
    
    return redirect(url_for('address.addresses'))

@bp.route('/set-default/<int:address_id>', methods=['POST'])
@login_required
def set_default_address(address_id):
    """Set address as default"""
    try:
        # Set all addresses as non-default
        Address.query.filter_by(user_id=current_user.id).update({'is_default': False})
        
        # Set the selected address as default
        address = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()
        address.is_default = True
        db.session.commit()
        
        flash('Default address updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error setting default address: {str(e)}', 'danger')
    
    return redirect(url_for('address.addresses'))
