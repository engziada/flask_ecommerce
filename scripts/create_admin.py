"""Script to create the default admin account."""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from app import create_app, db
from app.models.user import User

def create_admin_user():
    """Create the default admin user if it doesn't exist."""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if admin is None:
            # Create new admin user
            admin = User(
                username='admin',
                email='admin@example.com',
            )
            admin.set_password('admin123')  # Set default password
            admin.is_admin = True  # Set admin flag
            admin.first_name = 'Admin'
            admin.last_name = 'User'
            
            # Add to database
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
            print("Email: admin@example.com")
            print("Password: admin123")
        else:
            print("Admin user already exists!")

if __name__ == '__main__':
    create_admin_user()
