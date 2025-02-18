"""Script to set up Bosta shipping carrier."""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from app import create_app, db
from app.models.shipping import ShippingCarrier, ShippingMethod

def setup_bosta():
    """Set up Bosta shipping carrier and methods."""
    app = create_app()
    with app.app_context():
        # Check if Bosta carrier exists
        bosta = ShippingCarrier.query.filter_by(code='bosta').first()
        if not bosta:
            print("Creating Bosta carrier...")
            bosta = ShippingCarrier(
                name='Bosta',
                code='bosta',
                is_active=True,
                base_cost=50.0  # Base shipping cost in EGP
            )
            db.session.add(bosta)
            db.session.commit()
            print("Bosta carrier created successfully!")
        else:
            print("Bosta carrier already exists!")
            
        # Check if Bosta methods exist
        method = ShippingMethod.query.filter_by(carrier_id=bosta.id, code='standard').first()
        if not method:
            print("Creating Bosta shipping methods...")
            methods = [
                {
                    'name': 'Standard Delivery',
                    'code': 'standard',
                    'description': 'Standard delivery service (2-3 business days)',
                    'estimated_days': '2-3 days'
                }
            ]
            
            for m in methods:
                method = ShippingMethod(
                    carrier_id=bosta.id,
                    name=m['name'],
                    code=m['code'],
                    description=m['description'],
                    estimated_days=m['estimated_days'],
                    is_active=True
                )
                db.session.add(method)
            
            db.session.commit()
            print("Bosta shipping methods created successfully!")
        else:
            print("Bosta shipping methods already exist!")

if __name__ == '__main__':
    setup_bosta()
