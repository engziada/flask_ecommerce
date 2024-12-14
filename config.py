import os
from dotenv import load_dotenv
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///shop.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@flaskshop.com')
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_TYPE = 'filesystem'
    
    # Security config
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', 'csrf-key')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Stripe settings
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    
    # Admin account
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # Pagination
    PRODUCTS_PER_PAGE = 12
    
    # Shipping Services
    ARAMEX_USERNAME = os.environ.get('ARAMEX_USERNAME')
    ARAMEX_PASSWORD = os.environ.get('ARAMEX_PASSWORD')
    ARAMEX_VERSION = os.environ.get('ARAMEX_VERSION', 'v1')
    ARAMEX_ACCOUNT_ENTITY = os.environ.get('ARAMEX_ACCOUNT_ENTITY')
    ARAMEX_ACCOUNT_NUMBER = os.environ.get('ARAMEX_ACCOUNT_NUMBER')
    ARAMEX_ACCOUNT_PIN = os.environ.get('ARAMEX_ACCOUNT_PIN')
    ARAMEX_ACCOUNT_COUNTRY_CODE = os.environ.get('ARAMEX_ACCOUNT_COUNTRY_CODE', 'GB')
    
    SHIPPING_ORIGIN_CITY = os.environ.get('SHIPPING_ORIGIN_CITY', 'London')
    SHIPPING_ORIGIN_COUNTRY = os.environ.get('SHIPPING_ORIGIN_COUNTRY', 'GB')
    
    EGYPOST_API_KEY = os.environ.get('EGYPOST_API_KEY')
    EGYPOST_API_SECRET = os.environ.get('EGYPOST_API_SECRET')

    # Bosta Settings
    BOSTA_API_KEY=os.environ.get('BOSTA_API_KEY')
    BOSTA_EMAIL=os.environ.get('BOSTA_EMAIL')
    BOSTA_PASSWORD=os.environ.get('BOSTA_PASSWORD')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Bosta test credentials
    BOSTA_EMAIL = os.environ.get('BOSTA_TEST_EMAIL', os.environ.get('BOSTA_EMAIL'))
    BOSTA_PASSWORD = os.environ.get('BOSTA_TEST_PASSWORD', os.environ.get('BOSTA_PASSWORD'))
    BOSTA_API_KEY = os.environ.get('BOSTA_TEST_API_KEY', os.environ.get('BOSTA_API_KEY'))