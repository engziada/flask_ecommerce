from app import create_app
from app.extensions import db
import sqlite3
import os

app = create_app()

with app.app_context():
    # Get the database path from app config
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shop.db')
        print(f"Trying absolute path: {db_path}")
    
    print(f"Using database at: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Drop the alembic_version table if it exists
        cursor.execute("DROP TABLE IF EXISTS alembic_version;")
        print("Dropped existing alembic_version table")
        
        # Create a new alembic_version table
        cursor.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL);")
        print("Created new alembic_version table")
        
        # Insert the initial migration version
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('7b47e24ad44d');")
        print("Set version to initial migration: 7b47e24ad44d")
        
        conn.commit()
        print("Changes committed successfully")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
        print("Database connection closed")
