from app import create_app
from app.extensions import db
from app.models.product import Product
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    # Check if the table exists
    inspector = inspect(db.engine)
    if not inspector.has_table("product"):
        db.create_all()
        print("Database tables created")
    
    # Get the table name from the model
    table_name = Product.__tablename__
    
    # Check if the column already exists
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    
    if 'is_deleted' not in columns:
        # Add the is_deleted column with default value False
        with db.engine.connect() as conn:
            conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN is_deleted BOOLEAN DEFAULT 0'))
            conn.commit()
        print(f"Added is_deleted column to {table_name} table")
    else:
        print("is_deleted column already exists")
