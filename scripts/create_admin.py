from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

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
    # You can modify these credentials as needed
    username = "admin"
    email = "admin@example.com"
    password = "Admin123!"  # Make sure to change this password
    
    create_admin_user(username, email, password)
