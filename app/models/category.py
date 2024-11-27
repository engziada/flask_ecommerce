from datetime import datetime
from app.extensions import db

class Category(db.Model):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref=db.backref('category', lazy='select'), lazy='dynamic')

    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.slug = self._generate_slug()
        self.created_at = datetime.utcnow()
        self.updated_at = self.created_at

    def _generate_slug(self):
        """Generate a URL-friendly slug from the category name."""
        return self.name.lower().replace(' ', '-')

    def __repr__(self):
        return f'<Category {self.name}>'
