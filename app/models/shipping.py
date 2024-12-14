from app import db
from datetime import datetime

class ShippingCarrier(db.Model):
    __tablename__ = 'shipping_carriers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)  # 'bosta', 'egypost'
    is_active = db.Column(db.Boolean, default=True)
    base_cost = db.Column(db.Float, nullable=False)  # Base shipping cost
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Default pickup location for this carrier
    default_location_id = db.Column(db.String(100), nullable=True)  # Store Bosta/EgyPost location ID
    default_location_data = db.Column(db.JSON, nullable=True)  # Store full location data
    
    # Relationships
    shipping_methods = db.relationship('ShippingMethod', backref='carrier', lazy='joined')
    
    def __repr__(self):
        return f'<ShippingCarrier {self.name}>'

class ShippingMethod(db.Model):
    __tablename__ = 'shipping_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    carrier_id = db.Column(db.Integer, db.ForeignKey('shipping_carriers.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(20), nullable=False)  # e.g., 'express', 'standard'
    description = db.Column(db.Text, nullable=True)
    estimated_days = db.Column(db.String(50), nullable=True)  # e.g., "2-3 days"
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ShippingMethod {self.name}>'

class ShippingQuote(db.Model):
    """Stores shipping cost calculations for orders"""
    __tablename__ = 'shipping_quotes'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    carrier_id = db.Column(db.Integer, db.ForeignKey('shipping_carriers.id'), nullable=False)
    method_id = db.Column(db.Integer, db.ForeignKey('shipping_methods.id'), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='EGP')
    quote_data = db.Column(db.JSON, nullable=True)  # Store full quote response
    is_selected = db.Column(db.Boolean, default=False)
    valid_until = db.Column(db.DateTime, nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    carrier = db.relationship('ShippingCarrier')
    method = db.relationship('ShippingMethod')
    order = db.relationship('Order', backref='shipping_quotes')
    
    def __repr__(self):
        return f'<ShippingQuote {self.id} for Order {self.order_id}>'
