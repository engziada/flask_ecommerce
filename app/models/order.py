from app import db
from datetime import datetime
from app.utils.stripe_utils import refund_payment
from flask import current_app

class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        db.UniqueConstraint('stripe_payment_id', name='uq_order_stripe_payment_id'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
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
    stripe_payment_id = db.Column(db.String(100), nullable=True)  # Stripe PaymentIntent ID
    refund_id = db.Column(db.String(100), nullable=True)  # Stripe Refund ID
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
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
    def can_update_status(self):
        """Check if order status can be updated"""
        if self.status == 'cancelled' and self.cancelled_by == 'user':
            return False
        return True
    
    def cancel_order(self, cancelled_by):
        """Cancel order and track who cancelled it"""
        
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
