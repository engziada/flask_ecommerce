from datetime import datetime
from app.extensions import db
from app.models.category import Category

class ProductImage(db.Model):
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(200), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    def __init__(self, image_url, product_id, is_primary=False):
        self.image_url = image_url
        self.product_id = product_id
        self.is_primary = is_primary

class ProductColor(db.Model):
    __tablename__ = 'product_colors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    hex_code = db.Column(db.String(7), nullable=False)  # Store color in hex format (#RRGGBB)
    stock = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    def __init__(self, name, hex_code, product_id, stock=0):
        self.name = name
        self.hex_code = hex_code
        self.product_id = product_id
        self.stock = stock

class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    # Product details
    sku = db.Column(db.String(50), unique=True)
    weight = db.Column(db.Float)
    dimensions = db.Column(db.String(50))
    
    # Relationships
    images = db.relationship('ProductImage', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    colors = db.relationship('ProductColor', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref=db.backref('product', lazy='select'), lazy='dynamic', cascade='all, delete-orphan')
    cart_items = db.relationship('Cart', backref=db.backref('product', lazy='select'), lazy='dynamic', cascade='all, delete-orphan')
    wishlist_items = db.relationship('Wishlist', backref=db.backref('product', lazy='select'), lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, name, description, price, category_id, stock=0, sku=None, weight=None, dimensions=None, is_active=True):
        self.name = name
        self.description = description
        self.price = price
        self.category_id = category_id
        self.stock = stock
        self.sku = sku
        self.weight = weight
        self.dimensions = dimensions
        self.is_active = is_active
        self.is_deleted = False
    
    @property
    def primary_image(self):
        """Get the primary image for the product"""
        primary = self.images.filter_by(is_primary=True).first()
        if primary:
            return primary.image_url
        # Fallback to first image or default image
        first_image = self.images.first()
        return first_image.image_url if first_image else None

    @property
    def image_url(self):
        """Backward compatibility for old code that expects image_url"""
        return self.primary_image

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
            'category_id': self.category_id,
            'average_rating': self.average_rating
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'
