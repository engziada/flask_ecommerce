"""Script to clean all data from the database while preserving the structure."""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from app import create_app, db
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.order import Order
from app.models.review import Review
from app.models.cart import Cart  # Changed from CartItem
from app.models.wishlist import Wishlist  # Changed from WishlistItem
from app.models.address import Address
from app.models.coupon import Coupon

def confirm_cleanup():
    """Ask for confirmation before proceeding with database cleanup."""
    response = input(
        "\n⚠️  WARNING: This will delete all data from the database!\n"
        "Are you sure you want to proceed? (type 'yes' to confirm): "
    )
    return response.lower() == 'yes'

def clean_database():
    """Clean all data from the database while preserving the structure."""
    app = create_app()
    
    with app.app_context():
        if not confirm_cleanup():
            print("Database cleanup cancelled.")
            return

        try:
            print("\nStarting database cleanup...")
            
            # Delete data from all tables in correct order
            print("Deleting data from tables...")
            
            # Delete dependent tables first
            print("- Cleaning reviews...")
            Review.query.delete()
            
            print("- Cleaning cart items...")
            Cart.query.delete()  # Changed from CartItem
            
            print("- Cleaning wishlist items...")
            Wishlist.query.delete()  # Changed from WishlistItem
            
            print("- Cleaning orders...")
            Order.query.delete()
            
            print("- Cleaning products...")
            Product.query.delete()
            
            print("- Cleaning categories...")
            Category.query.delete()
            
            print("- Cleaning addresses...")
            Address.query.delete()
            
            print("- Cleaning coupons...")
            Coupon.query.delete()
            
            print("- Cleaning users...")
            User.query.delete()

            # Commit the changes
            db.session.commit()
            
            # Reset sequences for auto-incrementing IDs
            # Note: This is PostgreSQL specific. Modify if using different database
            if db.engine.url.drivername == 'postgresql':
                print("\nResetting ID sequences...")
                tables = [
                    'users', 'products', 'categories', 'orders', 
                    'reviews', 'cart_items', 'wishlist_items', 
                    'addresses', 'coupons'
                ]
                for table in tables:
                    db.session.execute(
                        f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1;"
                    )
                db.session.commit()

            print("\n✅ Database cleaned successfully!")
            print("You can now run add_sample_data.py to populate the database with fresh data.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error cleaning database: {str(e)}")
            raise

if __name__ == '__main__':
    clean_database()
