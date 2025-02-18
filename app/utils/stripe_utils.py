import stripe
from flask import current_app
from functools import wraps

def init_stripe():
    """Initialize Stripe with the secret key from config"""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

def create_payment_intent(amount, currency='egp', customer_id=None, metadata=None):
    """
    Create a Stripe PaymentIntent
    
    Args:
        amount (float): Amount in EGP (will be converted to smallest currency unit - piasters)
        currency (str): Currency code (default: 'egp')
        customer_id (str): Stripe customer ID
        metadata (dict): Additional metadata for the payment intent
    
    Returns:
        stripe.PaymentIntent: The created payment intent
    """
    try:
        # Convert amount to piasters (1 EGP = 100 piasters)
        amount_in_piasters = int(amount * 100)
        
        intent_data = {
            'amount': amount_in_piasters,
            'currency': currency,
            'automatic_payment_methods': {'enabled': True},
            'metadata': metadata or {}
        }
        
        if customer_id:
            intent_data['customer'] = customer_id
            
        payment_intent = stripe.PaymentIntent.create(**intent_data)
        
        current_app.logger.info(f'Created payment intent: {payment_intent.id} for {amount} EGP')
        return payment_intent
        
    except stripe.error.StripeError as e:
        current_app.logger.error(f'Stripe error creating payment intent: {str(e)}')
        raise
    except Exception as e:
        current_app.logger.error(f'Error creating payment intent: {str(e)}')
        raise

def confirm_payment_intent(payment_intent_id):
    """
    Confirm a Stripe PaymentIntent
    
    Args:
        payment_intent_id (str): The ID of the payment intent to confirm
    
    Returns:
        stripe.PaymentIntent: The confirmed payment intent
    """
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if payment_intent.status == 'requires_confirmation':
            payment_intent.confirm()
        return payment_intent
    except stripe.error.StripeError as e:
        current_app.logger.error(f'Stripe error confirming payment intent: {str(e)}')
        raise
    except Exception as e:
        current_app.logger.error(f'Error confirming payment intent: {str(e)}')
        raise

def refund_payment(payment_intent_id):
    """Refund a payment"""
    try:
        init_stripe()
        # First retrieve the payment intent to get the payment
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if not intent.latest_charge:
            raise ValueError("No charge found for this payment intent")
            
        # Create the refund
        refund = stripe.Refund.create(
            charge=intent.latest_charge,
            reason='requested_by_customer'
        )
        return refund
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error during refund: {str(e)}")
        raise

def format_amount(amount, currency='egp'):
    """
    Format amount in EGP with proper currency symbol
    
    Args:
        amount (float): Amount to format
        currency (str): Currency code (default: 'egp')
    
    Returns:
        str: Formatted amount string (e.g., 'EGP 100.00')
    """
    return f'EGP {amount:.2f}'

def require_stripe(f):
    """Decorator to ensure Stripe is initialized"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        init_stripe()
        return f(*args, **kwargs)
    return decorated_function
