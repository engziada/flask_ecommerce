from app import create_app, db
from app.models import *  # Import all models
import sqlite3
import os

app = create_app()

with app.app_context():
    # Create all tables first
    print("Creating database tables...")
    db.create_all()
    print("Database tables created")
    
    # Get the database path from app config
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shop.db')
        print(f"Using absolute path: {db_path}")
    
    print(f"Using database at: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(orders);")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add columns if they don't exist
        if 'paymob_order_id' not in columns:
            print("Adding paymob_order_id column...")
            cursor.execute("ALTER TABLE orders ADD COLUMN paymob_order_id VARCHAR(100);")
        
        if 'paymob_payment_id' not in columns:
            print("Adding paymob_payment_id column...")
            cursor.execute("ALTER TABLE orders ADD COLUMN paymob_payment_id VARCHAR(100);")
        
        conn.commit()
        print("Database schema updated successfully")
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(orders);")
        columns = [column[1] for column in cursor.fetchall()]
        print("\nCurrent orders table columns:")
        for column in columns:
            print(f"- {column}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
        print("\nDatabase connection closed")
