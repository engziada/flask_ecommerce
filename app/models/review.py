from datetime import datetime
from app.extensions import db

class Review(db.Model):
    """Review model for product reviews"""
    __table_args__ = {'extend_existing': True}
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __init__(self, product_id, user_id, rating, comment):
        self.product_id = product_id
        self.user_id = user_id
        self.rating = rating
        self.comment = comment

    def to_dict(self):
        """Convert review to dictionary"""
        return {
            'id': self.id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'product_id': self.product_id,
            'user_id': self.user_id
        }
        
    def __repr__(self):
        return f'<Review {self.id}>'
