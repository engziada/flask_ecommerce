from flask import Flask
from config import Config
from app.extensions import db, migrate, bcrypt, mail, csrf, login_manager
from datetime import datetime
from flask_login import current_user
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Load environment variables
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    env_file = os.path.join(basedir, '.env')
    
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        app.logger.warning('.env file not found!')
    
    app.config.from_object(config_class)

    # Set up logging
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Set up file handler for detailed logging
    file_handler = RotatingFileHandler(
        'logs/flask.log',
        maxBytes=10240,
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)

    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Flask E-commerce startup')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    
    # Initialize payment gateways
    with app.app_context():
        # Comment out Stripe initialization
        # from app.utils.stripe_utils import init_stripe
        # init_stripe()
        # app.logger.info('Stripe initialized with API keys')
        
        # Initialize PayMob
        from app.utils.paymob_utils import init_paymob
        init_paymob()
        app.logger.info('PayMob initialized with API keys')
    
    # Initialize upload folder and handle static files
    config_class.init_upload_folder(app)
    
    # In production, serve uploaded files from the persistent storage
    if os.environ.get('FLASK_ENV') == 'production':
        from flask import send_from_directory
        
        @app.route('/static/uploads/<path:filename>')
        def serve_upload(filename):
            """Serve uploaded files from the persistent storage in production"""
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    app.logger.info(f"Upload folder initialized at: {app.config['UPLOAD_FOLDER']}")
    
    # Import models here to avoid circular imports
    from app.models import Product, Category, Review, Cart, Wishlist, Order, User
    from app.models.shipping import ShippingCarrier, ShippingMethod, ShippingQuote

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Register blueprints
    blueprints = [
        ('errors', 'app.errors', None),
        ('auth', 'app.auth', '/auth'),
        ('main', 'app.main', None),
        ('cart', 'app.cart', '/cart'),
        ('wishlist', 'app.wishlist', '/wishlist'),
        ('order', 'app.order', '/order'),
        ('address', 'app.address', '/address'),
        ('reviews', 'app.reviews', '/reviews'),
        ('coupons', 'app.coupons', '/coupons'),
        ('shipping', 'app.shipping', '/shipping'),
        ('admin', 'app.admin', '/admin'), 
    ]

    for name, module, url_prefix in blueprints:
        try:
            bp = __import__(module, fromlist=['bp']).bp
            app.register_blueprint(bp, url_prefix=url_prefix)
            # app.logger.debug(f'Registered blueprint: {name} with prefix: {url_prefix}')
        except Exception as e:
            app.logger.error(f'Failed to register blueprint {name}: {str(e)}')

    # Template context processors
    @app.context_processor
    def inject_common_data():
        """Inject common data into all templates."""
        cart_total = 0
        categories = []
        try:
            if current_user.is_authenticated:
                cart_items = Cart.query.filter_by(user_id=current_user.id).all()
                cart_total = sum(item.quantity for item in cart_items)
            categories = Category.query.all()
        except Exception as e:
            app.logger.error(f"Error in context processor: {e}")

        def is_admin():
            return current_user.is_authenticated and getattr(current_user, 'is_admin', False)

        return dict(
            cart_total=cart_total,
            categories=categories,
            current_year=datetime.now().year,
            now=datetime.utcnow(),
            is_admin=is_admin
        )

    return app
