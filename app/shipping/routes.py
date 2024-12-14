from flask import jsonify, request
from app.shipping import bp
from app.shipping.services import calculate_shipping_cost, track_shipment, BostaCityMapping, BostaShippingService
from app.models.shipping import ShippingCarrier

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
def calculate_cost():
    """Calculate shipping cost for an order"""
    data = request.get_json()
    order_id = data.get('order_id')
    carrier_code = data.get('carrier_code')
    method_code = data.get('method_code')
    
    try:
        quotes = calculate_shipping_cost(order_id, carrier_code, method_code)
        return jsonify([{
            'carrier_id': q.carrier_id,
            'carrier_name': q.carrier.name,
            'method_id': q.method_id,
            'method_name': q.method.name,
            'cost': q.cost,
            'currency': q.currency,
            'estimated_days': q.method.estimated_days,
            'valid_until': q.valid_until.isoformat() if q.valid_until else None
        } for q in quotes])
    except Exception as e:
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
