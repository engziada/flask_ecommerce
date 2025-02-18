from app import create_app
from app.extensions import db
from app.models.product import Product, ProductImage, ProductColor

app = create_app()

def update_database():
    """Update database schema with new tables"""
    with app.app_context():
        # Create new tables
        db.create_all()
        
        print("Database schema updated successfully!")

if __name__ == '__main__':
    update_database()
