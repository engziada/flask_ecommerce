from app import create_app, db
from app.models.user import User
from app.models.product import Product, Category
from app.models.address import Address
from werkzeug.security import generate_password_hash
import random

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
            password=generate_password_hash('admin123'),
            is_admin=True
        )
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
        
        # Create sample products
        products = []
        for category in categories:
            for i in range(5):  # 5 products per category
                price = round(random.uniform(10.0, 1000.0), 2)
                stock = random.randint(0, 100)
                product = Product(
                    name=f'{category.name} Item {i+1}',
                    description=f'This is a sample {category.name.lower()} item {i+1}',
                    price=price,
                    stock=stock,
                    category=category
                )
                products.append(product)
                db.session.add(product)
        
        # Create sample addresses
        addresses = [
            Address(
                user=test_user,
                first_name='Test',
                last_name='User',
                street_address='123 Test St',
                city='Cairo',
                state='Cairo',
                country='Egypt',
                phone='1234567890',
                is_default=True
            ),
            Address(
                user=test_user,
                first_name='Test',
                last_name='User',
                street_address='456 Sample Ave',
                city='Alexandria',
                state='Alexandria',
                country='Egypt',
                phone='0987654321',
                is_default=False
            )
        ]
        for address in addresses:
            db.session.add(address)
        
        # Commit all changes
        db.session.commit()

if __name__ == '__main__':
    init_db()
