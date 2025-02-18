from flask import jsonify, request, session
from app.shipping import bp
from app.shipping.services import BostaShippingService
from app.models.shipping import ShippingCarrier
from app.models.address import Address
from app.models.cart import Cart
from app.models.user import User
from datetime import datetime, timedelta
from flask import current_app
from flask_login import current_user, login_required
from app.utils.city_mapping import BostaCityMapping

@bp.route('/carriers', methods=['GET'])
def get_carriers():
    """Get list of active shipping carriers"""
    carriers = ShippingCarrier.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'code': c.code,
        'base_cost': c.base_cost,
        'methods': [{
            'id': m.id,
            'name': m.name,
            'code': m.code,
            'description': m.description,
            'estimated_days': m.estimated_days
        } for m in c.methods if m.is_active]
    } for c in carriers])

@bp.route('/calculate', methods=['POST'])
@login_required
def calculate_cost():
    """Calculate shipping cost for an order"""
    data = request.get_json()
    address_id = data.get('address_id')
    carrier_code = data.get('carrier_code', 'bosta')
    
    if not address_id:
        return jsonify({'error': 'Address ID is required'}), 400
        
    try:
        # Get the address
        address = Address.query.get(address_id)
        if not address:
            return jsonify({'error': 'Invalid address'}), 404
            
        # Get cart items for the current user
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
            
        # Calculate total weight and dimensions
        total_weight = sum(item.quantity * item.product.weight for item in cart_items if item.product.weight)
        
        try:
            # Get shipping service
            shipping_service = BostaShippingService()
            
            # Calculate shipping cost
            cod_amount = float(data.get('total', 0)) if data.get('payment_method') == 'cod' else 0
            shipping_cost = shipping_service.estimate_shipping_cost(
                pickup_city='Ismailia',  # Default Bosta pickup location
                dropoff_city=address.city,
                cod_amount=cod_amount  # Pass total amount if COD
            )
            
            if shipping_cost is None:
                return jsonify({'error': 'Could not calculate shipping cost for the selected address'}), 400
                
            # Store shipping cost in session
            session['shipping_cost'] = shipping_cost
            session['shipping_address_id'] = address_id
                
            # Return shipping quote
            return jsonify([{
                'carrier_id': 1,  # Bosta ID
                'carrier_name': 'Bosta',
                'method_id': 1,
                'method_name': 'Standard Delivery',
                'cost': shipping_cost,
                'currency': 'EGP',
                'estimated_days': 3,
                'valid_until': (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }])
            
        except Exception as e:
            current_app.logger.error(f'Error calculating shipping cost: {str(e)}')
            # Only return 500 if it's a server error, not a validation error
            if 'No hub/zone ID found' in str(e):
                return jsonify({'error': 'Selected city is not supported for delivery'}), 400
            return jsonify({'error': 'Error calculating shipping cost. Please try again.'}), 500
            
    except Exception as e:
        current_app.logger.error(f'Error calculating shipping cost: {str(e)}')
        return jsonify({'error': str(e)}), 400

@bp.route('/cities')
def get_cities():
    """Get list of available cities"""
    return jsonify({
        'cities': BostaCityMapping.get_city_choices()
    })

@bp.route('/track/<tracking_number>', methods=['GET'])
def track_delivery(tracking_number):
    """Track a delivery by tracking number"""
    try:
        tracking_info = track_shipment(tracking_number)
        return jsonify(tracking_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/webhook', methods=['POST'])
def shipping_webhook():
    """Handle shipping status updates from Bosta"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400

        bp.logger.info(f"Received shipping webhook: {data}")
        
        # Extract delivery information
        delivery_id = data.get('_id')
        status = data.get('status')
        tracking_number = data.get('trackingNumber')
        business_reference = data.get('businessReference')
        
        if not all([delivery_id, status, tracking_number, business_reference]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Update order shipping status
        # TODO: Implement order status update based on Bosta delivery status
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        bp.logger.error(f"Error processing shipping webhook: {str(e)}")
        return jsonify({'error': str(e)}), 500
