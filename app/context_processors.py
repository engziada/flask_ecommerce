from datetime import datetime
from flask_login import current_user
from app.models.cart import Cart

def utility_processor():
    cart_total = 0
    if current_user.is_authenticated:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        cart_total = sum(item.quantity for item in cart_items)
    return {
        'now': datetime.utcnow(),
        'cart_total': cart_total
    }
