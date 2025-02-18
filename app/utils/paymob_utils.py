import requests
import hmac
import hashlib
import json
from functools import wraps
from flask import current_app

# PayMob API endpoints
PAYMOB_BASE_URL = 'https://accept.paymob.com/api'
AUTH_URL = f'{PAYMOB_BASE_URL}/auth/tokens'
ORDER_URL = f'{PAYMOB_BASE_URL}/ecommerce/orders'
PAYMENT_KEY_URL = f'{PAYMOB_BASE_URL}/acceptance/payment_keys'

def init_paymob():
    """Initialize PayMob configuration"""
    if not current_app.config.get('PAYMOB_API_KEY'):
        current_app.logger.error('PayMob API key not configured')
        raise ValueError('PayMob API key not configured')

def require_paymob(f):
    """Decorator to ensure PayMob is initialized"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        init_paymob()
        return f(*args, **kwargs)
    return decorated_function

@require_paymob
def get_auth_token():
    """Get authentication token from PayMob"""
    try:
        api_key = current_app.config.get('PAYMOB_API_KEY')
        if not api_key:
            raise ValueError('PayMob API key not configured')
            
        current_app.logger.debug(f'Getting auth token from PayMob')
        response = requests.post(AUTH_URL, json={'api_key': api_key})
        
        # Log response for debugging
        current_app.logger.debug(f'PayMob auth response status: {response.status_code}')
        current_app.logger.debug(f'PayMob auth response: {response.text}')
        
        response.raise_for_status()
        token = response.json().get('token')
        
        if not token:
            raise ValueError('No token in PayMob response')
            
        current_app.logger.info('Successfully obtained PayMob auth token')
        return token
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f'PayMob authentication error: {str(e)}')
        current_app.logger.error(f'Response: {e.response.text if hasattr(e, "response") else "No response"}')
        raise
    except Exception as e:
        current_app.logger.error(f'PayMob authentication error: {str(e)}')
        raise

@require_paymob
def create_order(amount_cents, items, shipping_data=None, currency='EGP'):
    """
    Create an order on PayMob
    
    Args:
        amount_cents (int): Amount in cents
        items (list): List of order items
        shipping_data (dict): Shipping information
        currency (str): Currency code (default: EGP)
    
    Returns:
        tuple: (order_id, token)
    """
    try:
        # Get authentication token
        auth_token = get_auth_token()
        
        # Create order data
        order_data = {
            'auth_token': auth_token,
            'delivery_needed': 'false',
            'amount_cents': amount_cents,
            'currency': currency,
            'items': items
        }
        
        if shipping_data:
            order_data['shipping_data'] = shipping_data
            order_data['delivery_needed'] = 'true'
        
        # Log request data
        current_app.logger.debug(f'Creating PayMob order with data: {json.dumps(order_data)}')
        
        response = requests.post(ORDER_URL, json=order_data)
        
        # Log response for debugging
        current_app.logger.debug(f'PayMob order creation response status: {response.status_code}')
        current_app.logger.debug(f'PayMob order creation response: {response.text}')
        
        response.raise_for_status()
        order_response = response.json()
        
        order_id = order_response.get('id')
        if not order_id:
            raise ValueError('No order ID in PayMob response')
            
        current_app.logger.info(f'Successfully created PayMob order: {order_id}')
        return order_id, auth_token
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f'PayMob order creation error: {str(e)}')
        current_app.logger.error(f'Response: {e.response.text if hasattr(e, "response") else "No response"}')
        raise
    except Exception as e:
        current_app.logger.error(f'PayMob order creation error: {str(e)}')
        raise

@require_paymob
def get_payment_key(order_id, auth_token, amount_cents, currency='EGP', 
                   integration_id=None, billing_data=None):
    """
    Get payment key for the iframe
    
    Args:
        order_id (int): PayMob order ID
        auth_token (str): Authentication token
        amount_cents (int): Amount in cents
        currency (str): Currency code
        integration_id (str): Integration ID (optional)
        billing_data (dict): Customer billing information
    
    Returns:
        str: Payment key token
    """
    try:
        # Get integration ID from config if not provided
        integration_id = integration_id or current_app.config.get('PAYMOB_INTEGRATION_ID')
        if not integration_id:
            raise ValueError('PayMob integration ID not configured')
            
        current_app.logger.debug(f'Using integration ID: {integration_id}')
        
        # Ensure billing data has all required fields
        required_fields = ['first_name', 'last_name', 'email', 'phone_number', 'street', 'city', 'country']
        billing_data = billing_data or {}
        
        for field in required_fields:
            if field not in billing_data or not billing_data[field]:
                billing_data[field] = 'NA'
        
        payment_data = {
            'auth_token': auth_token,
            'amount_cents': amount_cents,
            'expiration': 3600,
            'order_id': order_id,
            'billing_data': billing_data,
            'currency': currency,
            'integration_id': int(integration_id),  # PayMob expects this as integer
            'lock_order_when_paid': 'false'
        }
        
        # Log request data
        current_app.logger.debug(f'Getting payment key with data: {json.dumps(payment_data)}')
        
        response = requests.post(PAYMENT_KEY_URL, json=payment_data)
        
        # Log response for debugging
        current_app.logger.debug(f'PayMob payment key response status: {response.status_code}')
        current_app.logger.debug(f'PayMob payment key response: {response.text}')
        
        response.raise_for_status()
        payment_response = response.json()
        
        token = payment_response.get('token')
        if not token:
            raise ValueError('No payment token in PayMob response')
            
        current_app.logger.info('Successfully obtained PayMob payment key')
        return token
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f'PayMob payment key error: {str(e)}')
        current_app.logger.error(f'Response: {e.response.text if hasattr(e, "response") else "No response"}')
        raise
    except Exception as e:
        current_app.logger.error(f'PayMob payment key error: {str(e)}')
        raise

def verify_webhook_signature(request_data, hmac_secret):
    """
    Verify PayMob webhook signature
    
    Args:
        request_data (dict): Webhook request data
        hmac_secret (str): HMAC secret key
    
    Returns:
        bool: True if signature is valid
    """
    try:
        # Get the signature from headers
        received_signature = request_data.get('hmac')
        if not received_signature:
            return False
            
        # Sort request data alphabetically
        sorted_data = json.dumps(request_data, sort_keys=True).encode('utf-8')
        
        # Calculate HMAC
        calculated_signature = hmac.new(
            hmac_secret.encode('utf-8'),
            sorted_data,
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(received_signature, calculated_signature)
    except Exception as e:
        current_app.logger.error(f'PayMob webhook signature verification error: {str(e)}')
        return False

def process_transaction_response(transaction_data):
    """
    Process transaction response from PayMob
    
    Args:
        transaction_data (dict): Transaction response data
    
    Returns:
        dict: Processed transaction data
    """
    try:
        success = transaction_data.get('success', False)
        order_id = transaction_data.get('order', {}).get('id')
        amount_cents = transaction_data.get('amount_cents')
        currency = transaction_data.get('currency')
        transaction_id = transaction_data.get('id')
        
        return {
            'success': success,
            'order_id': order_id,
            'amount': amount_cents / 100,  # Convert to main currency unit
            'currency': currency,
            'transaction_id': transaction_id,
            'raw_response': transaction_data
        }
    except Exception as e:
        current_app.logger.error(f'PayMob transaction processing error: {str(e)}')
        raise
