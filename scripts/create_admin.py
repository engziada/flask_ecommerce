import os
import sys
from pathlib import Path

# Add the parent directory to Python path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_admin_user(username, email, password):
    app = create_app()
    with app.app_context():
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            # If user exists, make them admin
            user.is_admin = True
            print(f"Existing user {email} has been made admin")
        else:
            # Create new admin user
            user = User(
                username=username,
                email=email,
                password=password
            )
            user.is_admin = True
            db.session.add(user)
        
        db.session.commit()
        print(f"Admin user {email} has been created/updated successfully")

if __name__ == "__main__":
    # Get credentials from environment variables
    username = os.getenv("ADMIN_USERNAME", "admin")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "Admin123!")
    
    create_admin_user(username, email, password)
