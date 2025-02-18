from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, login_manager, bcrypt

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    is_admin = db.Column(db.Boolean, default=False)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stripe_customer_id = db.Column(db.String(255), unique=True, nullable=True)  # Added for Stripe integration
    
    # Relationships
    addresses = db.relationship('Address', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('Cart', backref='user', lazy=True, cascade='all, delete-orphan')
    wishlist_items = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, username, email, password=None):
        self.username = username
        self.email = email
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """Set the user's password with complexity validation."""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one number")
        if not any(c in '!@#$%^&*()_+-=[]{};:,./<>?`~' for c in password):
            raise ValueError("Password must contain at least one special character")
            
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        self.last_password_change = datetime.utcnow()
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_cart_count(self):
        """Get the total number of items in the user's cart."""
        return sum(item.quantity for item in self.cart_items)
    
    def get_wishlist_count(self):
        """Get the total number of items in the user's wishlist."""
        return len(self.wishlist_items)
    
    def has_in_cart(self, product_id):
        """Check if a product is in the user's cart."""
        return any(item.product_id == product_id for item in self.cart_items)
    
    def has_in_wishlist(self, product_id):
        """Check if a product is in the user's wishlist."""
        return any(item.product_id == product_id for item in self.wishlist_items)
    
    def get_default_address(self):
        """Get the user's default shipping address."""
        return next((addr for addr in self.addresses if addr.is_default), None)
    
    def __repr__(self):
        return f'<User {self.username}>'
