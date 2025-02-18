"""Script to populate the database with sample data."""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from app import create_app, db
from app.models.category import Category
from app.models.product import Product

# Initialize Flask app with development config
app = create_app()

# Sample categories with their respective products
SAMPLE_CATEGORIES = [
    {
        'name': 'Jewelry',
        'description': 'Elegant jewelry pieces for every occasion',
        'products': [
            {
                'name': 'Pearl Necklace',
                'description': 'Classic freshwater pearl necklace with 18k gold plating',
                'price': 299.99,
                'stock': 25,
                'image_url': 'https://picsum.photos/400/300?random=1',
                'sku': 'JWL-PN-001',
                'weight': 0.1,
                'dimensions': '20x5x3 cm'
            },
            {
                'name': 'Diamond Stud Earrings',
                'description': 'Timeless 14k white gold diamond studs',
                'price': 899.99,
                'stock': 15,
                'image_url': 'https://picsum.photos/400/300?random=2',
                'sku': 'JWL-DE-001',
                'weight': 0.05,
                'dimensions': '1x1x1 cm'
            },
            {
                'name': 'Gold Tennis Bracelet',
                'description': 'Elegant 18k gold bracelet with cubic zirconia',
                'price': 449.99,
                'stock': 20,
                'image_url': 'https://picsum.photos/400/300?random=3',
                'sku': 'JWL-GB-001',
                'weight': 0.08,
                'dimensions': '18x0.5x0.5 cm'
            }
        ]
    },
    {
        'name': 'Handbags',
        'description': 'Luxury handbags and purses',
        'products': [
            {
                'name': 'Leather Tote Bag',
                'description': 'Premium genuine leather tote with gold hardware',
                'price': 399.99,
                'stock': 30,
                'image_url': 'https://picsum.photos/400/300?random=4',
                'sku': 'BAG-LT-001',
                'weight': 0.8,
                'dimensions': '35x25x12 cm'
            },
            {
                'name': 'Evening Clutch',
                'description': 'Elegant satin clutch with crystal embellishments',
                'price': 149.99,
                'stock': 40,
                'image_url': 'https://picsum.photos/400/300?random=5',
                'sku': 'BAG-EC-001',
                'weight': 0.3,
                'dimensions': '25x15x5 cm'
            }
        ]
    },
    {
        'name': 'Accessories',
        'description': 'Fashion accessories and hair pieces',
        'products': [
            {
                'name': 'Silk Hair Scarf',
                'description': 'Pure silk scarf with floral print',
                'price': 79.99,
                'stock': 50,
                'image_url': 'https://picsum.photos/400/300?random=6',
                'sku': 'ACC-HS-001',
                'weight': 0.1,
                'dimensions': '90x90x0.1 cm'
            },
            {
                'name': 'Crystal Hair Pins',
                'description': 'Set of 3 crystal embellished hair pins',
                'price': 59.99,
                'stock': 45,
                'image_url': 'https://picsum.photos/400/300?random=7',
                'sku': 'ACC-HP-001',
                'weight': 0.05,
                'dimensions': '8x2x2 cm'
            }
        ]
    }
]

def add_sample_data():
    """Add sample categories and products to the database."""
    with app.app_context():
        try:
            # Clear existing data
            Product.query.delete()
            Category.query.delete()
            db.session.commit()
            
            print("Adding sample data...")
            
            # Add categories and their products
            for cat_data in SAMPLE_CATEGORIES:
                category = Category(
                    name=cat_data['name'],
                    description=cat_data['description']
                )
                db.session.add(category)
                db.session.flush()  # Get category ID
                
                # Add products for this category
                for prod_data in cat_data['products']:
                    product = Product(
                        name=prod_data['name'],
                        description=prod_data['description'],
                        price=prod_data['price'],
                        category_id=category.id,
                        stock=prod_data['stock'],
                        image_url=prod_data['image_url'],
                        sku=prod_data['sku'],
                        weight=prod_data['weight'],
                        dimensions=prod_data['dimensions']
                    )
                    db.session.add(product)
                
                print(f"Added category '{category.name}' with {len(cat_data['products'])} products")
            
            db.session.commit()
            print("\nSample data added successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding sample data: {str(e)}")
            raise

if __name__ == '__main__':
    add_sample_data()
