from app import db
from datetime import datetime
from app.utils import refund_payment
from flask import current_app

class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        db.UniqueConstraint('stripe_payment_id', name='uq_order_stripe_payment_id'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=True)
    shipping_carrier_id = db.Column(db.Integer, db.ForeignKey('shipping_carriers.id', name='fk_order_shipping_carrier'), nullable=True)
    shipping_method_id = db.Column(db.Integer, db.ForeignKey('shipping_methods.id', name='fk_order_shipping_method'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')
    payment_status = db.Column(db.String(20), nullable=False, default='pending')
    payment_method = db.Column(db.String(20), nullable=False, default='card')  # 'card' or 'cod'
    cancelled_by = db.Column(db.String(20), nullable=True)  # 'user' or 'admin'
    subtotal = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Payment fields
    stripe_payment_id = db.Column(db.String(100), nullable=True)  # Stripe PaymentIntent ID
    refund_id = db.Column(db.String(100), nullable=True)  # Stripe Refund ID
    paymob_order_id = db.Column(db.String(100), nullable=True)
    paymob_payment_id = db.Column(db.String(100), nullable=True)
    # Delivery fields
    delivery_id = db.Column(db.String(100), nullable=True)  # Bosta delivery ID
    
    # Shipping fields
    delivery_tracking_number = db.Column(db.String(50), nullable=True)  # Bosta tracking number
    delivery_order_id = db.Column(db.String(50), nullable=True)  # Bosta delivery order ID
    pickup_order_id = db.Column(db.String(50), nullable=True)  # Bosta pickup order ID
    delivery_status = db.Column(db.String(50), nullable=True)  # Current delivery status from carrier
    delivery_status_code = db.Column(db.Integer, nullable=True)  # Carrier status code
    delivery_notes = db.Column(db.Text, nullable=True)  # Additional delivery notes/instructions
    delivery_created_at = db.Column(db.DateTime, nullable=True)  # When delivery order was created
    delivery_updated_at = db.Column(db.DateTime, nullable=True)  # Last delivery status update
    delivery_estimated_date = db.Column(db.DateTime, nullable=True)  # Estimated delivery date
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    shipping_carrier = db.relationship('ShippingCarrier', backref='orders')
    shipping_method = db.relationship('ShippingMethod', backref='orders')
    
    @property
    def status_color(self):
        status_colors = {
            'pending': 'warning',
            'processing': 'info',
            'shipped': 'primary',
            'delivered': 'success',
            'cancelled': 'danger'
        }
        return status_colors.get(self.status, 'secondary')
    
    @property
    def payment_status_color(self):
        status_colors = {
            'pending': 'warning',
            'paid': 'success',
            'refunded': 'info',
            'failed': 'danger'
        }
        return status_colors.get(self.payment_status, 'secondary')
    
    @property
    def payment_method_display(self):
        """Get display text for payment method"""
        methods = {
            'card': 'Credit Card',
            'cod': 'Cash on Delivery'
        }
        return methods.get(self.payment_method, self.payment_method)
    
    @property
    def delivery_status_color(self):
        """Get Bootstrap color class based on delivery status"""
        status_colors = {
            'TICKET_CREATED': 'info',
            'PACKAGE_RECEIVED': 'primary',
            'OUT_FOR_DELIVERY': 'warning',
            'DELIVERED': 'success',
            'CANCELLED': 'danger',
            'FAILED_TO_DELIVER': 'danger'
        }
        return status_colors.get(self.delivery_status, 'secondary')
    
    @property
    def can_update_status(self):
        """Check if order status can be updated"""
        if self.status == 'cancelled' and self.cancelled_by == 'user':
            return False
        return True
    
    def cancel_order(self, cancelled_by):
        """Cancel order and track who cancelled it"""
        from app.shipping.services import cancel_shipping_order
        
        # First try to cancel shipping order if it exists
        if self.delivery_order_id:
            try:
                cancel_shipping_order(self)
            except Exception as e:
                current_app.logger.error(f"Error cancelling shipping order: {str(e)}")
                # Continue with order cancellation even if shipping cancellation fails
        
        # Handle payment refund if needed
        if self.payment_status == 'paid' and self.stripe_payment_id:
            try:
                refund = refund_payment(self.stripe_payment_id)
                self.refund_id = refund.id
                self.payment_status = 'refunded'
            except Exception as e:
                current_app.logger.error(f"Error refunding payment: {str(e)}")
                raise Exception("Could not process refund. Please contact support.")
        
        self.status = 'cancelled'
        self.cancelled_by = cancelled_by
        
        # Clear shipping fields
        self.delivery_status = 'CANCELLED'
        self.delivery_updated_at = datetime.utcnow()
        
        db.session.commit()
    
    def update_delivery_status(self, status, status_code=None, notes=None):
        """Update delivery status and related fields"""
        self.delivery_status = status
        if status_code is not None:
            self.delivery_status_code = status_code
        if notes:
            self.delivery_notes = notes
        self.delivery_updated_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    # Relationships
    ordered_product = db.relationship('Product', backref=db.backref('product_order_items', lazy=True))
    
    @property
    def subtotal(self):
        return self.price * self.quantity
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'
