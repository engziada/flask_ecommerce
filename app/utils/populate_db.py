from app import create_app, db
from app.models.user import User
from app.models.product import Product, Category
from app.models.cart import Cart
from app.models.wishlist import Wishlist
from app.models.order import Order, OrderItem
from app.models.address import Address
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

def create_sample_data():
    app = create_app()
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("Created database tables")
        
        # Create admin user if not exists
        admin_email = app.config['ADMIN_EMAIL']
        admin_username = 'admin'
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                username=admin_username,
                email=admin_email,
                password=app.config['ADMIN_PASSWORD']
            )
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            print(f"Created admin user: {admin_email}")

        # Create sample categories
        categories = [
            {'name': 'Electronics', 'description': 'Electronic devices and accessories'},
            {'name': 'Clothing', 'description': 'Fashion and apparel'},
            {'name': 'Books', 'description': 'Books and literature'},
            {'name': 'Home & Garden', 'description': 'Home decor and garden supplies'},
            {'name': 'Sports', 'description': 'Sports equipment and accessories'}
        ]

        for cat_data in categories:
            if not Category.query.filter_by(name=cat_data['name']).first():
                category = Category(**cat_data)
                db.session.add(category)
        db.session.commit()

        # Create sample products
        products = [
            # Electronics
            {'name': 'Smartphone X', 'description': 'Latest smartphone with advanced features', 'price': 699.99, 'stock': 50, 'category_name': 'Electronics', 'weight': 0.2},
            {'name': 'Laptop Pro', 'description': 'High-performance laptop for professionals', 'price': 1299.99, 'stock': 30, 'category_name': 'Electronics', 'weight': 2.5},
            {'name': 'Wireless Earbuds', 'description': 'Premium wireless earbuds with noise cancellation', 'price': 159.99, 'stock': 100, 'category_name': 'Electronics', 'weight': 0.1},
            
            # Clothing
            {'name': 'Classic T-Shirt', 'description': 'Comfortable cotton t-shirt', 'price': 19.99, 'stock': 200, 'category_name': 'Clothing', 'weight': 0.2},
            {'name': 'Denim Jeans', 'description': 'High-quality denim jeans', 'price': 59.99, 'stock': 150, 'category_name': 'Clothing', 'weight': 0.5},
            {'name': 'Winter Jacket', 'description': 'Warm winter jacket with hood', 'price': 89.99, 'stock': 80, 'category_name': 'Clothing', 'weight': 1.0},
            
            # Books
            {'name': 'Python Programming', 'description': 'Comprehensive guide to Python', 'price': 39.99, 'stock': 100, 'category_name': 'Books', 'weight': 0.8},
            {'name': 'Web Development Basics', 'description': 'Introduction to web development', 'price': 29.99, 'stock': 120, 'category_name': 'Books', 'weight': 0.7},
            {'name': 'Data Science Handbook', 'description': 'Essential guide for data scientists', 'price': 49.99, 'stock': 90, 'category_name': 'Books', 'weight': 1.0},
            
            # Home & Garden
            {'name': 'Table Lamp', 'description': 'Modern LED table lamp', 'price': 39.99, 'stock': 60, 'category_name': 'Home & Garden', 'weight': 1.2},
            {'name': 'Plant Pot Set', 'description': 'Set of 3 decorative plant pots', 'price': 24.99, 'stock': 80, 'category_name': 'Home & Garden', 'weight': 1.5},
            {'name': 'Wall Clock', 'description': 'Minimalist wall clock', 'price': 19.99, 'stock': 70, 'category_name': 'Home & Garden', 'weight': 0.5},
            
            # Sports
            {'name': 'Yoga Mat', 'description': 'Non-slip yoga mat', 'price': 29.99, 'stock': 100, 'category_name': 'Sports', 'weight': 1.0},
            {'name': 'Dumbbells Set', 'description': 'Set of adjustable dumbbells', 'price': 149.99, 'stock': 40, 'category_name': 'Sports', 'weight': 10.0},
            {'name': 'Running Shoes', 'description': 'Comfortable running shoes', 'price': 79.99, 'stock': 90, 'category_name': 'Sports', 'weight': 0.6}
        ]

        for prod_data in products:
            category = Category.query.filter_by(name=prod_data['category_name']).first()
            if category and not Product.query.filter_by(name=prod_data['name']).first():
                product = Product(
                    name=prod_data['name'],
                    description=prod_data['description'],
                    price=prod_data['price'],
                    stock=prod_data['stock'],
                    category_id=category.id,
                    weight=prod_data['weight']
                )
                db.session.add(product)
        db.session.commit()

        # Create sample users
        users = [
            {'username': 'johndoe', 'email': 'john@example.com', 'password': 'password123', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'janesmith', 'email': 'jane@example.com', 'password': 'password123', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'mikejohnson', 'email': 'mike@example.com', 'password': 'password123', 'first_name': 'Mike', 'last_name': 'Johnson'}
        ]

        for user_data in users:
            if not User.query.filter_by(email=user_data['email']).first():
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password']
                )
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                db.session.add(user)
                
                # Add sample address for each user
                address = Address(
                    user=user,
                    name=f"{user_data['first_name']} {user_data['last_name']}",
                    street=f"{random.randint(1, 999)} Main St",
                    city=random.choice(['Cairo', 'Alexandria', 'Giza', 'Luxor']),
                    state='Cairo',
                    zip_code=str(random.randint(11111, 99999)),
                    country='Egypt',
                    phone=f"+20{random.randint(1000000000, 9999999999)}"
                )
                db.session.add(address)
        db.session.commit()

        # Add products to carts and wishlists
        users = User.query.filter(User.email != app.config['ADMIN_EMAIL']).all()
        products = Product.query.all()

        for user in users:
            # Add random products to cart
            for _ in range(random.randint(1, 4)):
                product = random.choice(products)
                if not Cart.query.filter_by(user_id=user.id, product_id=product.id).first():
                    cart_item = Cart(
                        user_id=user.id,
                        product_id=product.id,
                        quantity=random.randint(1, 3)
                    )
                    db.session.add(cart_item)

            # Add random products to wishlist
            for _ in range(random.randint(1, 5)):
                product = random.choice(products)
                if not Wishlist.query.filter_by(user_id=user.id, product_id=product.id).first():
                    wishlist_item = Wishlist(
                        user_id=user.id,
                        product_id=product.id
                    )
                    db.session.add(wishlist_item)

        db.session.commit()

        # Create sample orders
        order_statuses = ['pending', 'processing', 'shipped', 'delivered']
        payment_statuses = ['pending', 'paid']
        payment_methods = ['card', 'cod']

        for user in users:
            # Create 1-3 orders per user
            for _ in range(random.randint(1, 3)):
                order_date = datetime.now() - timedelta(days=random.randint(1, 30))
                address = Address.query.filter_by(user_id=user.id).first()
                
                order = Order(
                    user_id=user.id,
                    shipping_address_id=address.id,
                    status=random.choice(order_statuses),
                    payment_status=random.choice(payment_statuses),
                    payment_method=random.choice(payment_methods),
                    shipping_cost=10.0,
                    date_created=order_date,
                    subtotal=0.0,  # Will be updated after adding items
                    total=0.0      # Will be updated after adding items
                )
                db.session.add(order)
                db.session.flush()  # Get order ID

                # Add 1-5 products to each order
                subtotal = 0
                for _ in range(random.randint(1, 5)):
                    product = random.choice(products)
                    quantity = random.randint(1, 3)
                    item_price = product.price
                    subtotal += item_price * quantity

                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id,
                        quantity=quantity,
                        price=item_price
                    )
                    db.session.add(order_item)

                # Update order totals
                order.subtotal = subtotal
                order.total = subtotal + order.shipping_cost

        db.session.commit()
        print("Sample data has been created successfully!")

if __name__ == '__main__':
    create_sample_data()
