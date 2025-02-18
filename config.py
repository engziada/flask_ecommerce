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
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('true', '1', 't')
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
    # UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.normpath(os.path.join(basedir, 'app', 'static', 'uploads')))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Ensure the upload folder exists and is writable
    @staticmethod
    def init_upload_folder(app):
        upload_path = os.path.normpath(app.config['UPLOAD_FOLDER'])
        if not os.path.exists(upload_path):
            os.makedirs(upload_path, exist_ok=True)
        if not os.access(upload_path, os.W_OK):
            raise RuntimeError(f"Upload folder {upload_path} is not writable")
        app.config['UPLOAD_FOLDER'] = upload_path  # Update with normalized path

    # Stripe settings
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    
    # PayMob settings
    PAYMOB_API_KEY = os.environ.get('PAYMOB_API_KEY')
    PAYMOB_INTEGRATION_ID = os.environ.get('PAYMOB_INTEGRATION_ID')
    PAYMOB_IFRAME_ID = os.environ.get('PAYMOB_IFRAME_ID')
    PAYMOB_HMAC_SECRET = os.environ.get('PAYMOB_HMAC_SECRET')
    
    # PayMob callback URLs
    # For local testing, use ngrok URL. In production, use your domain
    PAYMOB_RETURN_URL = os.environ.get('PAYMOB_RETURN_URL', 'http://127.0.0.1:5000/order/paymob-callback')
    PAYMOB_CALLBACK_URL = os.environ.get('PAYMOB_CALLBACK_URL', PAYMOB_RETURN_URL)  # Use same URL for both by default
    
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
    BOSTA_API_KEY = os.environ.get('BOSTA_API_KEY')
    BOSTA_EMAIL = os.environ.get('BOSTA_EMAIL')
    BOSTA_PASSWORD = os.environ.get('BOSTA_PASSWORD', '').strip("'\"")  # Strip any quotes from password


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Bosta test credentials
    BOSTA_EMAIL = os.environ.get('BOSTA_TEST_EMAIL', os.environ.get('BOSTA_EMAIL'))
    BOSTA_PASSWORD = os.environ.get('BOSTA_TEST_PASSWORD', os.environ.get('BOSTA_PASSWORD'))
    BOSTA_API_KEY = os.environ.get('BOSTA_TEST_API_KEY', os.environ.get('BOSTA_API_KEY'))

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
