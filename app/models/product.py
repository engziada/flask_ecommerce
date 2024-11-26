from datetime import datetime
from app.extensions import db
from app.models.category import Category

class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    # Product details
    sku = db.Column(db.String(50), unique=True)
    weight = db.Column(db.Float)
    dimensions = db.Column(db.String(50))
    
    # Relationships
    reviews = db.relationship('Review', backref=db.backref('product', lazy='select'), lazy='dynamic', cascade='all, delete-orphan')
    cart_items = db.relationship('Cart', backref=db.backref('product', lazy='select'), lazy='dynamic', cascade='all, delete-orphan')
    wishlist_items = db.relationship('Wishlist', backref=db.backref('product', lazy='select'), lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, name, description, price, category_id, stock=0, image_url=None, sku=None, weight=None, dimensions=None):
        self.name = name
        self.description = description
        self.price = price
        self.category_id = category_id
        self.stock = stock
        self.image_url = image_url
        self.sku = sku
        self.weight = weight
        self.dimensions = dimensions
    
    @property
    def average_rating(self):
        """Calculate the average rating for the product"""
        ratings = [review.rating for review in self.reviews]
        return sum(ratings) / len(ratings) if ratings else 0
    
    def update_stock(self, quantity):
        """Update product stock"""
        if self.stock + quantity < 0:
            return False
        self.stock += quantity
        return True
    
    def to_dict(self):
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'image_url': self.image_url,
            'category_id': self.category_id,
            'average_rating': self.average_rating
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'
