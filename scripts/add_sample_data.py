"""Script to populate the database with sample data."""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from faker import Faker
from app import create_app, db
from app.models.category import Category
from app.models.product import Product

# Initialize Flask app with development config
app = create_app()
fake = Faker()

# Sample categories with their respective products
SAMPLE_CATEGORIES = [
    {
        'name': 'Electronics',
        'description': 'Electronic devices and accessories',
        'products': [
            {
                'name': 'Smartphone',
                'description': 'High-end smartphone with latest features',
                'price': 699.99,
                'stock': 50,
                'image_url': 'https://picsum.photos/400/300?random=1',
                'sku': 'ELEC-SP-001',
                'weight': 0.2,
                'dimensions': '15x7x1 cm'
            },
            {
                'name': 'Laptop',
                'description': 'Powerful laptop for work and gaming',
                'price': 1299.99,
                'stock': 30,
                'image_url': 'https://picsum.photos/400/300?random=2',
                'sku': 'ELEC-LP-001',
                'weight': 2.5,
                'dimensions': '35x25x2 cm'
            },
            {
                'name': 'Wireless Earbuds',
                'description': 'Premium wireless earbuds with noise cancellation',
                'price': 199.99,
                'stock': 100,
                'image_url': 'https://picsum.photos/400/300?random=3',
                'sku': 'ELEC-WE-001',
                'weight': 0.1,
                'dimensions': '5x5x3 cm'
            }
        ]
    },
    {
        'name': 'Clothing',
        'description': 'Fashion and apparel',
        'products': [
            {
                'name': 'Cotton T-Shirt',
                'description': 'Comfortable cotton t-shirt in various colors',
                'price': 24.99,
                'stock': 200,
                'image_url': 'https://picsum.photos/400/300?random=4',
                'sku': 'CLO-TS-001',
                'weight': 0.2,
                'dimensions': '30x20x2 cm'
            },
            {
                'name': 'Jeans',
                'description': 'Classic fit denim jeans',
                'price': 49.99,
                'stock': 150,
                'image_url': 'https://picsum.photos/400/300?random=5',
                'sku': 'CLO-JN-001',
                'weight': 0.5,
                'dimensions': '40x30x5 cm'
            }
        ]
    },
    {
        'name': 'Books',
        'description': 'Books and literature',
        'products': [
            {
                'name': 'Python Programming',
                'description': 'Comprehensive guide to Python programming',
                'price': 39.99,
                'stock': 75,
                'image_url': 'https://picsum.photos/400/300?random=6',
                'sku': 'BOOK-PY-001',
                'weight': 1.0,
                'dimensions': '25x20x3 cm'
            },
            {
                'name': 'Web Development',
                'description': 'Modern web development techniques',
                'price': 44.99,
                'stock': 60,
                'image_url': 'https://picsum.photos/400/300?random=7',
                'sku': 'BOOK-WD-001',
                'weight': 1.2,
                'dimensions': '25x20x3 cm'
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
