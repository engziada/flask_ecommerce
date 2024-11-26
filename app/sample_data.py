"""Script to populate the database with sample data."""
from app import create_app
from app.models.product import Product
from app.models.category import Category
from app.models.review import Review
from app.models.user import User
from app.extensions import db
from datetime import datetime, timedelta
import random

# Sample review comments for different ratings
REVIEW_TEMPLATES = {
    5: [
        "Absolutely love it! Best purchase ever!",
        "Exceeded my expectations in every way.",
        "Outstanding quality and performance.",
        "Couldn't be happier with this product!",
        "Perfect in every way, highly recommend!"
    ],
    4: [
        "Very good product, minor improvements possible.",
        "Really happy with the purchase.",
        "Great value for money.",
        "Would recommend with slight reservations.",
        "Solid product, does what it promises."
    ],
    3: [
        "Decent product but has room for improvement.",
        "Good enough for the price.",
        "Met basic expectations.",
        "Average performance, nothing special.",
        "Serves its purpose but could be better."
    ],
    2: [
        "Below average, wouldn't buy again.",
        "Several issues need addressing.",
        "Not worth the price.",
        "Disappointed with the quality.",
        "Barely meets minimum expectations."
    ],
    1: [
        "Very disappointed with this purchase.",
        "Would not recommend at all.",
        "Save your money, look elsewhere.",
        "Multiple problems, poor quality.",
        "Regret buying this product."
    ]
}

def create_sample_reviews(product, users):
    """Create random reviews for a product."""
    # Generate between 3 and 8 reviews per product
    num_reviews = random.randint(3, 8)
    
    # Calculate average rating tendency (products more likely to have good ratings)
    base_rating = random.choice([4, 5])  # Most products tend to have good ratings
    
    for _ in range(num_reviews):
        # Generate rating with tendency towards the base rating
        rating = min(5, max(1, int(random.gauss(base_rating, 0.8))))
        
        # Select a random comment template for this rating
        comment = random.choice(REVIEW_TEMPLATES[rating])
        
        # Select a random user
        user = random.choice(users)
        
        review = Review(
            product_id=product.id,
            user_id=user.id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)

def create_sample_data():
    """Create sample categories and products."""
    # Create categories
    categories = [
        {
            'name': 'Electronics',
            'description': 'Electronic devices and accessories',
            'products': [
                {
                    'name': 'Smartphone X',
                    'description': 'Latest smartphone with 6.5" display and 5G capability',
                    'price': 799.99,
                    'stock': 50,
                    'image_url': 'https://via.placeholder.com/300x300.png?text=Smartphone+X'
                },
                {
                    'name': 'Laptop Pro',
                    'description': '15" laptop with Intel i7, 16GB RAM, 512GB SSD',
                    'price': 1299.99,
                    'stock': 30,
                    'image_url': 'https://via.placeholder.com/300x300.png?text=Laptop+Pro'
                },
                {
                    'name': 'Wireless Earbuds',
                    'description': 'True wireless earbuds with noise cancellation',
                    'price': 149.99,
                    'stock': 100,
                    'image_url': 'https://via.placeholder.com/300x300.png?text=Wireless+Earbuds'
                }
            ]
        },
        {
            'name': 'Clothing',
            'description': 'Fashion and apparel',
            'products': [
                {
                    'name': 'Classic T-Shirt',
                    'description': '100% cotton crew neck t-shirt',
                    'price': 19.99,
                    'stock': 200,
                    'image_url': 'https://via.placeholder.com/300x300.png?text=Classic+T-Shirt'
                },
                {
                    'name': 'Denim Jeans',
                    'description': 'Classic fit denim jeans',
                    'price': 49.99,
                    'stock': 150,
                    'image_url': 'https://via.placeholder.com/300x300.png?text=Denim+Jeans'
                }
            ]
        },
        {
            'name': 'Home & Kitchen',
            'description': 'Home appliances and kitchen essentials',
            'products': [
                {
                    'name': 'Coffee Maker',
                    'description': 'Programmable coffee maker with 12-cup capacity',
                    'price': 79.99,
                    'stock': 75,
                    'image_url': 'https://via.placeholder.com/300x300.png?text=Coffee+Maker'
                },
                {
                    'name': 'Stand Mixer',
                    'description': 'Professional stand mixer with 5-quart bowl',
                    'price': 299.99,
                    'stock': 40,
                    'image_url': 'https://via.placeholder.com/300x300.png?text=Stand+Mixer'
                }
            ]
        }
    ]

    # Create sample users for reviews if they don't exist
    sample_users = []
    usernames = ['john_doe', 'jane_smith', 'mike_wilson', 'sarah_jones', 'alex_brown', 
                'emma_davis', 'chris_miller', 'lisa_white', 'david_clark', 'amy_taylor']
    
    for username in usernames:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                email=f'{username}@example.com'
            )
            user.set_password('password123')
            db.session.add(user)
        sample_users.append(user)
    
    db.session.commit()

    # Create categories and products
    for category_data in categories:
        category = Category(
            name=category_data['name'],
            description=category_data['description']
        )
        db.session.add(category)
        db.session.commit()

        for product_data in category_data['products']:
            product = Product(
                name=product_data['name'],
                description=product_data['description'],
                price=product_data['price'],
                stock=product_data['stock'],
                image_url=product_data['image_url'],
                category_id=category.id
            )
            db.session.add(product)
            db.session.commit()
            
            # Add reviews for this product
            create_sample_reviews(product, sample_users)
    
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # First, clear existing data
        Review.query.delete()
        Product.query.delete()
        Category.query.delete()
        print("Cleared existing data.")
        
        # Create new sample data
        create_sample_data()
        print("Created sample data successfully!")
