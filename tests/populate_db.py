from datetime import datetime
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models.user import User
from app.models.product import Product, Category
from app.models.review import Review
from app.models.address import Address

def populate_db():
    app = create_app()
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Clear existing data
        Review.query.delete()
        Product.query.delete()
        Category.query.delete()
        Address.query.delete()
        User.query.delete()

        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        admin.is_admin = True
        db.session.add(admin)

        # Create regular users
        users = []
        for i in range(1, 4):
            user = User(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password=f'password{i}'
            )
            users.append(user)
            db.session.add(user)

        # Create sample addresses
        addresses = [
            Address(
                user=users[0],
                name='Home',
                phone='+44 20 7123 4567',
                street='123 Main St',
                city='London',
                state='Greater London',
                country='United Kingdom',
                zip_code='SW1A 1AA',
                is_default=True
            ),
            Address(
                user=users[1],
                name='Work',
                phone='+44 161 456 7890',
                street='456 High St',
                city='Manchester',
                state='Greater Manchester',
                country='United Kingdom',
                zip_code='M1 1AD',
                is_default=True
            )
        ]
        for address in addresses:
            db.session.add(address)

        # Create categories
        categories = [
            Category(name='Electronics', description='Electronic devices and gadgets'),
            Category(name='Books', description='Physical and digital books'),
            Category(name='Clothing', description='Men\'s and women\'s apparel')
        ]
        for category in categories:
            db.session.add(category)

        # Commit categories to get their ids
        db.session.commit()

        # Create products
        products = [
            # Electronics
            Product(
                name='Smartphone X',
                description='Latest smartphone with amazing features',
                price=799.99,
                stock=50,
                category_id=categories[0].id,
                image_url='https://example.com/smartphone.jpg',
                weight=0.2,  # 200g
                sku='PHONE-X-001'
            ),
            Product(
                name='Laptop Pro',
                description='Professional laptop for work and gaming',
                price=1299.99,
                stock=30,
                category_id=categories[0].id,
                image_url='https://example.com/laptop.jpg',
                weight=2.5,  # 2.5kg
                sku='LAPTOP-PRO-001'
            ),
            # Books
            Product(
                name='Python Programming',
                description='Complete guide to Python programming',
                price=49.99,
                stock=100,
                category_id=categories[1].id,
                image_url='https://example.com/python-book.jpg',
                weight=0.8,  # 800g
                sku='BOOK-PY-001'
            ),
            Product(
                name='Web Development Basics',
                description='Learn web development from scratch',
                price=39.99,
                stock=75,
                category_id=categories[1].id,
                image_url='https://example.com/web-dev-book.jpg',
                weight=0.7,  # 700g
                sku='BOOK-WEB-001'
            ),
            # Clothing
            Product(
                name='Classic T-Shirt',
                description='Comfortable cotton t-shirt',
                price=19.99,
                stock=200,
                category_id=categories[2].id,
                image_url='https://example.com/tshirt.jpg',
                weight=0.2,  # 200g
                sku='SHIRT-001'
            ),
            Product(
                name='Denim Jeans',
                description='High-quality denim jeans',
                price=59.99,
                stock=150,
                category_id=categories[2].id,
                image_url='https://example.com/jeans.jpg',
                weight=0.5,  # 500g
                sku='JEANS-001'
            )
        ]
        for product in products:
            db.session.add(product)

        # Create reviews
        reviews = [
            Review(
                user_id=users[0].id,
                product_id=products[0].id,
                rating=5,
                comment='Great smartphone, very satisfied!'
            ),
            Review(
                user_id=users[1].id,
                product_id=products[0].id,
                rating=4,
                comment='Good phone but a bit expensive'
            ),
            Review(
                user_id=users[1].id,
                product_id=products[2].id,
                rating=5,
                comment='Excellent book for learning Python'
            )
        ]
        for review in reviews:
            db.session.add(review)

        # Commit all changes
        db.session.commit()
        print("Database populated successfully!")

if __name__ == '__main__':
    populate_db()
