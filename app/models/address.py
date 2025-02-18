from app.extensions import db
from datetime import datetime
from app.utils.city_mapping import BostaCityMapping

class Address(db.Model):
    __tablename__ = 'addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    street = db.Column(db.String(200), nullable=False)
    building_number = db.Column(db.String(20))
    floor = db.Column(db.String(10))
    apartment = db.Column(db.String(10))
    city = db.Column(db.String(50), nullable=False)
    district = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = db.relationship('Order', backref='shipping_address', lazy=True)

    @property
    def city_code(self):
        """Get the Bosta city code for this address"""
        return BostaCityMapping.get_code(self.city)

    @property
    def formatted_address(self):
        """Get a formatted string representation of the address"""
        parts = [
            f"{self.building_number} {self.street}" if self.building_number else self.street,
            self.district,
            self.city,
            self.postal_code
        ]
        return ", ".join(filter(None, parts))

    def to_dict(self):
        """Convert address to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'street': self.street,
            'building_number': self.building_number,
            'floor': self.floor,
            'apartment': self.apartment,
            'city': self.city,
            'district': self.district,
            'postal_code': self.postal_code,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Address {self.id}>'
