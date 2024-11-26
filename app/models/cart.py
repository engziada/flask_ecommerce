from app.extensions import db
from datetime import datetime
from app.models.product import Product

class Cart(db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def subtotal(self):
        return self.product.price * self.quantity
    
    def __repr__(self):
        return f'<CartItem {self.id}>'
