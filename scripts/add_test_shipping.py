from app import create_app, db
from app.models.shipping import ShippingCarrier, ShippingMethod
from datetime import datetime

def add_test_shipping_data():
    app = create_app()
    with app.app_context():
        # Create Bosta carrier
        bosta = ShippingCarrier(
            name='Bosta',
            code='bosta',
            is_active=True,
            base_cost=50.0,
            date_created=datetime.utcnow(),
            date_updated=datetime.utcnow(),
            default_location_id='cairo',
            default_location_data={
                'city': 'Cairo',
                'area': 'Nasr City'
            }
        )
        
        # Create Bosta methods
        bosta_standard = ShippingMethod(
            carrier=bosta,
            name='Standard Delivery',
            code='standard',
            description='2-3 business days',
            is_active=True,
            estimated_days=3,
            date_created=datetime.utcnow(),
            date_updated=datetime.utcnow()
        )
        
        bosta_express = ShippingMethod(
            carrier=bosta,
            name='Express Delivery',
            code='express',
            description='Next business day',
            is_active=True,
            estimated_days=1,
            date_created=datetime.utcnow(),
            date_updated=datetime.utcnow()
        )
        
        # Create EgyPost carrier
        egypost = ShippingCarrier(
            name='EgyPost',
            code='egypost',
            is_active=True,
            base_cost=30.0,
            date_created=datetime.utcnow(),
            date_updated=datetime.utcnow(),
            default_location_id='alexandria',
            default_location_data={
                'city': 'Alexandria',
                'area': 'Smouha'
            }
        )
        
        # Create EgyPost methods
        egypost_standard = ShippingMethod(
            carrier=egypost,
            name='Standard Post',
            code='standard',
            description='3-5 business days',
            is_active=True,
            estimated_days=5,
            date_created=datetime.utcnow(),
            date_updated=datetime.utcnow()
        )
        
        egypost_express = ShippingMethod(
            carrier=egypost,
            name='Express Post',
            code='express',
            description='2 business days',
            is_active=True,
            estimated_days=2,
            date_created=datetime.utcnow(),
            date_updated=datetime.utcnow()
        )
        
        # Add all objects to session
        db.session.add_all([
            bosta, bosta_standard, bosta_express,
            egypost, egypost_standard, egypost_express
        ])
        
        # Commit the changes
        db.session.commit()
        print("Test shipping carriers and methods added successfully!")

if __name__ == '__main__':
    add_test_shipping_data()
