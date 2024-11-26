from app.extensions import db

class Category(db.Model):
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    
    # Relationships
    products = db.relationship('Product', backref=db.backref('category', lazy='select'), lazy='dynamic')

    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.slug = self._generate_slug()

    def _generate_slug(self):
        """Generate a URL-friendly slug from the category name."""
        return self.name.lower().replace(' ', '-')

    def __repr__(self):
        return f'<Category {self.name}>'
