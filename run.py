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

app = create_app()
migrate = Migrate(app, db)

# Initialize the database if it does not exist
if not os.path.exists('shop.db'):
    with app.app_context():
        db.create_all()
        print('Database initialized.')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
