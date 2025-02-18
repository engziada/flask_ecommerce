import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

# Sample users
SAMPLE_USERS = [
    {
        'username': 'john_doe',
        'email': 'john@example.com',
        'first_name': 'John',
        'last_name': 'Doe'
    },
    {
        'username': 'jane_smith',
        'email': 'jane@example.com',
        'first_name': 'Jane',
        'last_name': 'Smith'
    },
    {
        'username': 'mike_wilson',
        'email': 'mike@example.com',
        'first_name': 'Mike',
        'last_name': 'Wilson'
    },
    {
        'username': 'sarah_brown',
        'email': 'sarah@example.com',
        'first_name': 'Sarah',
        'last_name': 'Brown'
    },
    {
        'username': 'alex_taylor',
        'email': 'alex@example.com',
        'first_name': 'Alex',
        'last_name': 'Taylor'
    }
]

def create_sample_users():
    """Create sample non-admin users"""
    app = create_app()
    
    with app.app_context():
        users_added = 0
        
        for user_data in SAMPLE_USERS:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if existing_user:
                print(f"User {user_data['email']} already exists")
                continue
            
            # Create new user
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password='password123'  # Set password during initialization
            )
            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.is_admin = False
            
            db.session.add(user)
            users_added += 1
        
        try:
            db.session.commit()
            print(f"Successfully added {users_added} sample users")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding users: {str(e)}")

if __name__ == "__main__":
    create_sample_users()
