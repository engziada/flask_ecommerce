"""Reset database and migrations."""
import os
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Drop all tables
    db.drop_all()
    
    # Remove alembic_version table if it exists
    with db.engine.connect() as conn:
        conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
        conn.commit()
    
    # Create all tables
    db.create_all()
