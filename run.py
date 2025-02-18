import os
from app import create_app, db
from flask_migrate import Migrate
from dotenv import load_dotenv

# Ensure environment variables are loaded
basedir = os.path.abspath(os.path.dirname(__file__))
env_file = os.path.join(basedir, '.env')
if os.path.exists(env_file):
    print(f'Loading environment from {env_file}')
    load_dotenv(env_file)
else:
    print('Warning: .env file not found!')

# Debug: Print Bosta settings
print('DEBUG: Environment Variables:')
print(f'BOSTA_EMAIL: {os.environ.get("BOSTA_EMAIL")}')
print(f'BOSTA_API_KEY: {os.environ.get("BOSTA_API_KEY")}')

app = create_app()

# Print the database URL
print(f'Database URL: {os.environ.get("DATABASE_URL")}')

# Initialize the database if it does not exist
if not os.path.exists('shop.db'):
    with app.app_context():
        db.create_all()
        print('Database initialized.')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
