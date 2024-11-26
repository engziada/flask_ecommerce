from app import db
from datetime import datetime

class Order(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    subtotal = db.Column(db.Float, nullable=False)
    shipping_cost = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
