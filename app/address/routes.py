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
                street2=form.street2.data,
                building_number=form.building_number.data,
                floor=form.floor.data,
                apartment=form.apartment.data,
                city=form.city.data,
                state=form.state.data,
                zip_code=form.zip_code.data,
                country=form.country.data,
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
    
    if request.method == 'POST':
        try:
            address.name = request.form.get('name')
            address.phone = request.form.get('phone')
            address.street = request.form.get('street')  
            address.city = request.form.get('city')
            address.state = request.form.get('state')
            address.zip_code = request.form.get('zip_code')  
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
