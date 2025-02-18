import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template_string
from datetime import datetime

# Load environment variables
load_dotenv()

# PayMob API Configuration
PAYMOB_API_KEY = os.getenv('PAYMOB_API_KEY')
PAYMOB_IFRAME_ID = os.getenv('PAYMOB_IFRAME_ID')
PAYMOB_INTEGRATION_ID = os.getenv('PAYMOB_INTEGRATION_ID')

# PayMob API endpoints
BASE_URL = 'https://accept.paymob.com/api'
AUTH_URL = f'{BASE_URL}/auth/tokens'
ORDER_URL = f'{BASE_URL}/ecommerce/orders'
PAYMENT_KEY_URL = f'{BASE_URL}/acceptance/payment_keys'

# Create Flask app for testing
app = Flask(__name__)

# HTML template for the payment page
PAYMENT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>PayMob Test Payment</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .info { background-color: #cce5ff; color: #004085; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PayMob Test Payment</h1>
        {% if error %}
            <div class="status error">
                <h3>Error:</h3>
                <pre>{{ error }}</pre>
            </div>
        {% endif %}
        
        {% if auth_token %}
            <div class="status info">
                <h3>Auth Token:</h3>
                <pre>{{ auth_token[:50] }}...</pre>
            </div>
        {% endif %}
        
        {% if order_id %}
            <div class="status info">
                <h3>Order ID:</h3>
                <pre>{{ order_id }}</pre>
            </div>
        {% endif %}
        
        {% if payment_key %}
            <div class="status info">
                <h3>Payment Key:</h3>
                <pre>{{ payment_key[:50] }}...</pre>
            </div>
            
            <h2>Payment Iframe:</h2>
            <iframe width="100%" height="800" src="https://accept.paymob.com/api/acceptance/iframes/{{ iframe_id }}?payment_token={{ payment_key }}"></iframe>
        {% endif %}
    </div>
</body>
</html>
'''

def get_auth_token():
    """Get authentication token"""
    try:
        response = requests.post(AUTH_URL, json={'api_key': PAYMOB_API_KEY})
        response.raise_for_status()
        return response.json().get('token')
    except requests.exceptions.RequestException as e:
        raise Exception(f'Authentication failed: {str(e)}')

def create_order(auth_token, amount_cents=100):
    """Create an order"""
    try:
        order_data = {
            'auth_token': auth_token,
            'delivery_needed': 'false',
            'amount_cents': amount_cents,
            'currency': 'EGP',
            'items': [{
                'name': 'Test Item',
                'amount_cents': amount_cents,
                'description': 'Test item for PayMob integration',
                'quantity': 1
            }]
        }
        
        response = requests.post(ORDER_URL, json=order_data)
        response.raise_for_status()
        return response.json().get('id')
    except requests.exceptions.RequestException as e:
        raise Exception(f'Order creation failed: {str(e)}')

def get_payment_key(auth_token, order_id, amount_cents=100):
    """Get payment key"""
    try:
        payment_data = {
            'auth_token': auth_token,
            'amount_cents': amount_cents,
            'expiration': 3600,
            'order_id': order_id,
            'billing_data': {
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'test@example.com',
                'phone_number': '+201234567890',
                'street': 'Test Street',
                'building': 'Test Building',
                'floor': '1',
                'apartment': '1',
                'city': 'Test City',
                'country': 'EG',
                'state': 'Test State',
                'postal_code': '12345'
            },
            'currency': 'EGP',
            'integration_id': PAYMOB_INTEGRATION_ID,
            'lock_order_when_paid': 'false'
        }
        
        response = requests.post(PAYMENT_KEY_URL, json=payment_data)
        response.raise_for_status()
        return response.json().get('token')
    except requests.exceptions.RequestException as e:
        raise Exception(f'Payment key generation failed: {str(e)}')

@app.route('/')
def test_payment():
    """Test PayMob payment flow"""
    result = {
        'error': None,
        'auth_token': None,
        'order_id': None,
        'payment_key': None,
        'iframe_id': PAYMOB_IFRAME_ID
    }
    
    try:
        # Step 1: Get authentication token
        result['auth_token'] = get_auth_token()
        
        # Step 2: Create order
        result['order_id'] = create_order(result['auth_token'])
        
        # Step 3: Get payment key
        result['payment_key'] = get_payment_key(
            result['auth_token'],
            result['order_id']
        )
        
    except Exception as e:
        result['error'] = str(e)
    
    return render_template_string(PAYMENT_TEMPLATE, **result)

if __name__ == '__main__':
    # Ensure all required environment variables are set
    required_vars = ['PAYMOB_API_KEY', 'PAYMOB_IFRAME_ID', 'PAYMOB_INTEGRATION_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    print("Starting PayMob test server...")
    print("This will create a test order for 1 EGP (100 cents)")
    print("\nTest card numbers:")
    print("Success: 4987654321098769")
    print("Declined: 5123456789012346")
    print("\nCard details:")
    print("Name on card: Test Account")
    print("Expiry: Any future date")
    print("CVV: 123")
    
    app.run(debug=True, port=5001)
