from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        # Drop the alembic_version table if it exists
        conn.execute(text('DROP TABLE IF EXISTS alembic_version'))
        conn.commit()
    print("Removed alembic_version table if it existed")
