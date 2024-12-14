from app import create_app, db
from app.models.address import Address
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from datetime import datetime

app = create_app()

def add_missing_columns():
    with app.app_context():
        with db.engine.connect() as conn:
            # Add district column if it doesn't exist
            try:
                conn.execute(text('ALTER TABLE addresses ADD COLUMN district VARCHAR(100)'))
                print("Successfully added district column to addresses table")
            except OperationalError as e:
                if "duplicate column name" in str(e):
                    print("District column already exists")
                else:
                    print(f"Error adding district column: {str(e)}")
            
            # Add postal_code column if it doesn't exist
            try:
                conn.execute(text('ALTER TABLE addresses ADD COLUMN postal_code VARCHAR(10)'))
                print("Successfully added postal_code column to addresses table")
            except OperationalError as e:
                if "duplicate column name" in str(e):
                    print("Postal code column already exists")
                else:
                    print(f"Error adding postal_code column: {str(e)}")

            # Add created_at column if it doesn't exist
            try:
                conn.execute(text('ALTER TABLE addresses ADD COLUMN created_at TIMESTAMP'))
                # Update existing rows with current timestamp
                conn.execute(text('UPDATE addresses SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL'))
                print("Successfully added created_at column to addresses table")
            except OperationalError as e:
                if "duplicate column name" in str(e):
                    print("created_at column already exists")
                else:
                    print(f"Error adding created_at column: {str(e)}")

            # Add updated_at column if it doesn't exist
            try:
                conn.execute(text('ALTER TABLE addresses ADD COLUMN updated_at TIMESTAMP'))
                # Update existing rows with current timestamp
                conn.execute(text('UPDATE addresses SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL'))
                print("Successfully added updated_at column to addresses table")
            except OperationalError as e:
                if "duplicate column name" in str(e):
                    print("updated_at column already exists")
                else:
                    print(f"Error adding updated_at column: {str(e)}")
            
            conn.commit()

if __name__ == '__main__':
    add_missing_columns()
