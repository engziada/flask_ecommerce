import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.product import Product
from app.models.user import User
from app.models.review import Review
import random
from datetime import datetime, timedelta

# Sample review comments
SAMPLE_COMMENTS = [
    "Great product! Exactly what I was looking for.",
    "The quality exceeded my expectations. Would definitely buy again!",
    "Good value for money. Fast delivery too.",
    "Very satisfied with this purchase. Highly recommended!",
    "Nice product but the delivery took longer than expected.",
    "Perfect fit for my needs. Will order more soon.",
    "Amazing quality and great customer service!",
    "Decent product for the price point.",
    "Better than what I expected. Very happy with my purchase.",
    "Good product but could be better packaged.",
    "Excellent quality and fast shipping!",
    "Just what I needed. Very happy with it.",
    "Product works great. No complaints!",
    "Solid product, would recommend to others.",
    "Really happy with this purchase. Worth every penny!"
]

def create_sample_reviews():
    """Create sample reviews for products"""
    app = create_app()
    
    with app.app_context():
        # Get all products and users
        products = Product.query.all()
        users = User.query.filter(User.is_admin == False).all()
        
        if not products:
            print("No products found in database")
            return
            
        if not users:
            print("No non-admin users found in database")
            return
        
        # Delete existing reviews
        Review.query.delete()
        
        reviews_added = 0
        
        # Add random reviews for each product
        for product in products:
            # Random number of reviews per product (2-5)
            num_reviews = random.randint(2, 5)
            
            # Get random users for reviews
            selected_users = random.sample(users, min(num_reviews, len(users)))
            
            for user in selected_users:
                # Random rating (3-5 stars, skewing positive)
                rating = random.choices([3, 4, 5], weights=[20, 40, 40])[0]
                
                # Random comment
                comment = random.choice(SAMPLE_COMMENTS)
                
                # Random date within last 3 months
                days_ago = random.randint(0, 90)
                review_date = datetime.utcnow() - timedelta(days=days_ago)
                
                # Create review
                review = Review(
                    product_id=product.id,
                    user_id=user.id,
                    rating=rating,
                    comment=comment
                )
                review.created_at = review_date
                review.updated_at = review_date
                
                db.session.add(review)
                reviews_added += 1
        
        try:
            db.session.commit()
            print(f"Successfully added {reviews_added} sample reviews")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding reviews: {str(e)}")

if __name__ == "__main__":
    create_sample_reviews()
