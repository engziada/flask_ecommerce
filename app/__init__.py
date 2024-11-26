from flask import Flask
from config import Config
from app.extensions import db, migrate, bcrypt, mail, csrf, login_manager
from datetime import datetime
from flask_login import current_user

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Import models here to avoid circular imports
    from app.models import Product, Category, Review, Cart, Wishlist, Order, User

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Register blueprints
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)  # URL prefix is defined in the blueprint

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.shop import bp as shop_bp
    app.register_blueprint(shop_bp, url_prefix='/shop')

    # Print out all registered routes for debugging
    print("\nRegistered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.rule}")

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
            print(f"Error in context processor: {e}")
        return dict(
            cart_total=cart_total,
            categories=categories,
            current_year=datetime.now().year,
            now=datetime.utcnow()
        )

    return app
