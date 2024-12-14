from app import create_app, db
from app.models.shipping import ShippingCarrier, ShippingMethod

app = create_app()

with app.app_context():
    carrier = ShippingCarrier.query.first()
    print(f'Carrier: {carrier.name if carrier else None}')
    if carrier:
        methods = carrier.shipping_methods
        print(f'Methods: {[m.name for m in methods] if methods else None}')
    method = ShippingMethod.query.first()
    print(f'Method: {method.name if method else None}')
