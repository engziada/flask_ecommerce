from app import create_app, db
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.models.review import Review
from app.models.address import Address
from app.models.cart import Cart
from app.models.shipping import ShippingCarrier, ShippingMethod
from datetime import datetime
import random

app = create_app()

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()

        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com'
        )
        admin.set_password('admin123')
        admin.is_admin = True
        db.session.add(admin)

        # Create test user
        test_user = User(
            username='testuser',
            email='test@example.com'
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()

        # Create shipping carriers and methods
        bosta = ShippingCarrier(
            name='Bosta',
            code='bosta',
            base_cost=50.0,
            is_active=True
        )
        db.session.add(bosta)
        db.session.commit()

        standard_shipping = ShippingMethod(
            name='Standard Shipping',
            code='standard',
            carrier_id=bosta.id,
            estimated_days=3,
            is_active=True
        )
        db.session.add(standard_shipping)
        db.session.commit()

        # Create categories
        categories = [
            Category(name='Electronics', description='Electronic devices and gadgets'),
            Category(name='Clothing', description='Fashion and apparel'),
            Category(name='Books', description='Books and literature'),
            Category(name='Home & Kitchen', description='Home and kitchen items')
        ]
        db.session.add_all(categories)
        db.session.commit()

        # Create products
        products = []
        for i in range(20):
            category = random.choice(categories)
            product = Product(
                name=f'Product {i+1}',
                description=f'Description for product {i+1}',
                price=random.uniform(10.0, 1000.0),
                stock=random.randint(0, 100),
                category_id=category.id,
                sku=f'SKU{i+1:05d}',
                weight=random.uniform(0.1, 10.0),
                dimensions=f'{random.randint(1,50)}x{random.randint(1,50)}x{random.randint(1,50)}'
            )
            products.append(product)
        db.session.add_all(products)
        db.session.commit()

        # Create reviews
        reviews = []
        for product in products[:10]:  # Add reviews for first 10 products
            review = Review(
                user_id=test_user.id,
                product_id=product.id,
                rating=random.randint(1, 5),
                comment=f'Test review for product {product.id}'
            )
            reviews.append(review)
        db.session.add_all(reviews)
        db.session.commit()

        # Create address for test user
        address = Address(
            user_id=test_user.id,
            name='Test User',
            phone='01234567890',
            street='123 Test Street',
            building_number='45',
            floor='3',
            apartment='301',
            city='Cairo',
            district='Maadi',
            postal_code='12345',
            is_default=True
        )
        db.session.add(address)
        db.session.commit()

        # Add items to test user's cart
        cart_items = [
            Cart(
                user_id=test_user.id,
                product_id=products[0].id,
                quantity=2
            ),
            Cart(
                user_id=test_user.id,
                product_id=products[2].id,
                quantity=1
            )
        ]
        for cart_item in cart_items:
            db.session.add(cart_item)
        db.session.commit()

if __name__ == '__main__':
    init_db()
