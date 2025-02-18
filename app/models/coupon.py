from datetime import datetime
from app.extensions import db

class Coupon(db.Model):
    """Coupon model for discount codes"""
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    discount_type = db.Column(db.String(20), nullable=False)  # 'percentage', 'fixed', or 'free_shipping'
    discount_amount = db.Column(db.Float, nullable=False)
    min_purchase_amount = db.Column(db.Float, default=0.0)
    max_discount_amount = db.Column(db.Float)  # Only for percentage discounts
    valid_from = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    usage_limit = db.Column(db.Integer)  # Maximum number of times this coupon can be used
    times_used = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, code, discount_type, discount_amount, min_purchase_amount=0.0,
                 max_discount_amount=None, valid_from=None, valid_until=None, 
                 usage_limit=None):
        print(f"Creating coupon with code: '{code}', length: {len(code)}, chars: {[c for c in code]}")
        self.code = code.strip().upper()
        print(f"Stored coupon code: '{self.code}', length: {len(self.code)}, chars: {[c for c in self.code]}")
        self.discount_type = discount_type
        self.discount_amount = discount_amount if discount_type != 'free_shipping' else 0
        self.min_purchase_amount = min_purchase_amount
        self.max_discount_amount = max_discount_amount
        self.valid_from = valid_from or datetime.utcnow()
        self.valid_until = valid_until
        self.usage_limit = usage_limit
        self.times_used = 0
        self.is_active = True

    def is_valid(self, cart_total=None):
        """Check if coupon is valid"""
        # Convert UTC now to the same timezone as valid_from
        now = datetime.utcnow()
        
        if not self.is_active:
            return False, "This coupon is no longer active"
            
        if self.valid_until and now > self.valid_until:
            return False, "This coupon has expired"
            
        # Compare the dates in UTC
        if self.valid_from and now < self.valid_from:
            return False, "This coupon is not yet valid"
            
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False, "This coupon has reached its usage limit"
            
        if cart_total and cart_total < self.min_purchase_amount:
            return False, f"Minimum purchase amount of ${self.min_purchase_amount} required"
            
        return True, "Coupon is valid"

    def calculate_discount(self, cart_total, shipping_cost=0):
        """Calculate discount amount based on cart total and shipping cost"""
        if self.discount_type == 'free_shipping':
            return shipping_cost
        elif self.discount_type == 'percentage':
            discount = cart_total * (self.discount_amount / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:  # fixed amount
            discount = min(self.discount_amount, cart_total)  # Don't exceed cart total
        return round(discount, 2)

    def use_coupon(self):
        """Increment the times_used counter"""
        self.times_used += 1
        db.session.commit()

    def to_dict(self):
        """Convert coupon to dictionary"""
        return {
            'id': self.id,
            'code': self.code,
            'discount_type': self.discount_type,
            'discount_amount': self.discount_amount,
            'min_purchase_amount': self.min_purchase_amount,
            'max_discount_amount': self.max_discount_amount,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'usage_limit': self.usage_limit,
            'times_used': self.times_used,
            'is_active': self.is_active
        }
