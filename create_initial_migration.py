from app import create_app
from app.extensions import db
from sqlalchemy import text
import os

app = create_app()

with app.app_context():
    # Remove existing migrations directory if it exists
    if os.path.exists('migrations'):
        import shutil
        shutil.rmtree('migrations')
    
    # Initialize migrations
    os.system('flask db init')
    
    # Create an initial migration
    os.system('flask db migrate -m "Initial migration"')
    
    # Apply the migration
    os.system('flask db upgrade')
    
print("Migration process completed")
