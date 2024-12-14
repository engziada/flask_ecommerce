from app import create_app, db
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.address import Address
from app.models.cart import Cart
from app.models.review import Review
from werkzeug.security import generate_password_hash
import random
import uuid

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we already have data
        if User.query.first() is not None:
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('admin123')
        )
        admin.is_admin = True  # Set admin status after creation
        db.session.add(admin)
        
        # Create test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            password=generate_password_hash('test123')
        )
        db.session.add(test_user)
        
        # Create categories
        categories = [
            Category(name='Electronics', description='Electronic devices and gadgets'),
            Category(name='Clothing', description='Fashion and apparel'),
            Category(name='Books', description='Books and literature'),
            Category(name='Home', description='Home and garden items')
        ]
        for category in categories:
            db.session.add(category)
        
        # Commit to get category IDs
        db.session.commit()
        
        # Create sample products
        products = []
        for category in categories:
            for i in range(5):  # 5 products per category
                price = round(random.uniform(10.0, 1000.0), 2)
                stock = random.randint(0, 100)
                sku = f"{category.name[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"
                product = Product(
                    name=f'{category.name} Item {i+1}',
                    description=f'This is a sample {category.name.lower()} item {i+1}',
                    price=price,
                    stock=stock,
                    category_id=category.id,
                    sku=sku,
                    weight=random.uniform(0.1, 10.0),
                    dimensions=f"{random.randint(1,50)}x{random.randint(1,50)}x{random.randint(1,50)}",
                    is_active=True
                )
                products.append(product)
                db.session.add(product)
        
        # Commit to get product IDs
        db.session.commit()
        
        # Create sample addresses
        addresses = [
            Address(
                user=test_user,
                name='Test User',
                phone='1234567890',
                street='123 Test St',
                building_number='15',
                floor='3',
                apartment='301',
                city='Cairo',
                district='Nasr City',
                postal_code='12345',
                is_default=True
            ),
            Address(
                user=test_user,
                name='Test User',
                phone='0987654321',
                street='456 Sample Ave',
                building_number='22',
                floor='5',
                apartment='502',
                city='Alexandria',
                district='Miami',
                postal_code='54321',
                is_default=False
            )
        ]
        for address in addresses:
            db.session.add(address)
        
        # Create some sample reviews
        reviews = [
            Review(
                product_id=products[0].id,
                user_id=test_user.id,
                rating=5,
                comment="Great product, very satisfied!"
            ),
            Review(
                product_id=products[1].id,
                user_id=test_user.id,
                rating=4,
                comment="Good quality, fast delivery"
            )
        ]
        for review in reviews:
            db.session.add(review)
        
        # Add some items to test user's cart
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
        
        # Commit all changes
        db.session.commit()

if __name__ == '__main__':
    init_db()
