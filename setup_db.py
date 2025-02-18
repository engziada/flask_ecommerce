from app import create_app
from app.extensions import db
from app.models import *  # Import all models
import os

def setup_database():
    app = create_app()
    with app.app_context():
        # Create all tables
        print("Creating all database tables...")
        db.create_all()
        print("Database tables created successfully")
        
        # Print table information
        print("\nDatabase tables created:")
        for table in db.metadata.tables.keys():
            print(f"- {table}")

if __name__ == '__main__':
    setup_database()
