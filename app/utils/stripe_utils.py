import stripe
from flask import current_app
from functools import wraps

def init_stripe():
    """Initialize Stripe with the secret key from config"""
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

def create_payment_intent(amount, currency='usd', metadata=None):
    """Create a Stripe PaymentIntent"""
    try:
        init_stripe()
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            payment_method_types=['card'],
            metadata=metadata or {}
        )
        return intent
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error: {str(e)}")
        raise

def confirm_payment_intent(payment_intent_id):
    """Confirm a PaymentIntent"""
    try:
        init_stripe()
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return intent
    except stripe.error.StripeError as e:
        current_app.logger.error(f"Stripe error: {str(e)}")
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

def require_stripe(f):
    """Decorator to ensure Stripe is initialized"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        init_stripe()
        return f(*args, **kwargs)
    return decorated_function
