# Flask E-commerce Platform

A robust e-commerce platform built with Flask, featuring a modern and responsive design with comprehensive e-commerce functionality.

## Features

### User Management
- User registration and authentication
- Profile management
- Password reset functionality
- Role-based access control (Admin, Customer)

### Product Management
- Product catalog with categories
- Product search functionality
- Product reviews and ratings
- Product image management
- Detailed product descriptions

### Shopping Experience
- Shopping cart functionality
- Wishlist management
- Product filtering and sorting
- Coupon system for discounts
- Order tracking

### Checkout Process
- Multiple shipping methods
- Address management
- Order confirmation
- Order history

### Admin Features
- Product management (CRUD operations)
- Order management
- User management
- Coupon management
- Sales analytics

### Additional Features
- Responsive design
- Form validation
- Error handling
- Session management
- Database migrations
- Security features

## Project Structure

```
flask_ecommerce/
├── app/                    # Main application package
│   ├── address/           # Address management module
│   ├── admin/             # Admin panel functionality
│   ├── auth/              # Authentication module
│   ├── cart/              # Shopping cart functionality
│   ├── coupons/           # Coupon system
│   ├── errors/            # Error handlers
│   ├── forms/             # Form definitions
│   ├── main/              # Main routes
│   ├── models/            # Database models
│   ├── order/            # Order processing
│   ├── reviews/          # Product reviews
│   ├── shipping/         # Shipping methods
│   ├── shop/             # Shop related views
│   ├── static/           # Static files (CSS, JS, images)
│   ├── templates/        # HTML templates
│   ├── utils/            # Utility functions
│   └── wishlist/         # Wishlist functionality
├── migrations/            # Database migrations
├── tests/                # Test suite
├── scripts/              # Utility scripts
├── config.py             # Configuration settings
├── requirements.txt      # Project dependencies
├── run.py               # Application entry point
└── wsgi.py              # WSGI entry point
```

## Key Files Description

- `config.py`: Application configuration settings
- `run.py`: Development server startup script
- `wsgi.py`: Production server entry point
- `init_db.py`: Database initialization script
- `migrate.py`: Database migration script
- `requirements.txt`: Project dependencies
- `app/__init__.py`: Application factory and initialization
- `app/extensions.py`: Flask extensions initialization
- `app/models/`: Database models for all entities
- `app/forms/`: WTForms form definitions
- `app/templates/`: Jinja2 templates
- `app/static/`: Static assets (CSS, JavaScript, images)

## Getting Started

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables in `.env`
6. Initialize the database: `python init_db.py`
7. Run migrations: `python migrate.py`
8. Start the development server: `python run.py`

## Environment Variables

Required environment variables in `.env`:
- `FLASK_APP`
- `FLASK_ENV`
- `SECRET_KEY`
- `DATABASE_URL`
- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`

## Testing

Run tests using: `python -m pytest`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Checkpoints

### Checkpoint 4 (2024-12-19)
- Fixed coupon functionality in checkout process
- Added proper coupon display in cart and checkout pages
- Implemented correct discount calculations for percentage and fixed amount coupons
- Ensured coupon discounts are properly applied throughout the order process
- Updated templates to show applied coupon details

To restore to this checkpoint:
```bash
git restore --source=checkpoint-4 .
```

## License

This project is licensed under the MIT License.

Last Updated: December 19, 2024