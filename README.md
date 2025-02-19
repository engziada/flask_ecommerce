# Elite by Mai - Luxury Jewelry & Accessories E-commerce Platform

A sophisticated e-commerce platform specializing in women's jewelry, luxury handbags, and fashion accessories, built with Flask and featuring a modern, elegant design.

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

### Checkpoint 8 (2025-01-30)
- Fixed shipping cost calculation in checkout process
- Improved error handling for shipping cost API responses
- Added session storage for shipping costs to prevent recalculation
- Enhanced validation of shipping costs during order placement
- Fixed error handling in JavaScript for better UX

To restore to this checkpoint:
```bash
git restore --source=checkpoint-8 .
```

### Checkpoint 7 (2025-01-28)
- Enhanced shipping integration with Bosta
- Added proper city mapping functionality
- Improved checkout process with loading overlay
- Fixed shipping cost calculation
- Added proper error handling for shipping service
- Updated checkout UI/UX

To restore to this checkpoint:
```bash
git restore --source=checkpoint-7 .
```

### Checkpoint 6 (2025-01-28)
- Fixed Stripe payment integration
- Added stripe_customer_id field to User model
- Properly initialized Stripe API keys in app startup
- Fixed payment intent creation and customer ID handling
- Ensured proper Stripe configuration loading

To restore to this checkpoint:
```bash
git restore --source=checkpoint-6 .
```

### Checkpoint 5 (2025-01-25)
- Enhanced product management functionality
- Improved form styling and layout
- Removed color variations feature
- Added proper image handling with preview
- Updated form validation

To revert to this checkpoint:
```bash
git restore --source=checkpoint-5 .
```

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

### Checkpoint 9 (2025-02-01)
- Implemented soft delete functionality for products
- Added is_deleted column to Product model
- Enhanced admin product management with restore functionality
- Added proper CSRF token handling for product restoration
- Improved error logging and messages in product management
- Fixed product creation form validation and file upload handling

To restore to this checkpoint:
```bash
git restore --source=checkpoint-9 .
```

### Checkpoint 10 (2025-02-17)
- Updated social media links in footer (Facebook, Instagram, TikTok)
- Updated contact information with real business details
- Removed placeholder business hours and address
- Temporarily disabled contact form section
- Removed client-side coupon validation for better UX
- Fixed coupon application in cart functionality

To restore to this checkpoint:
```bash
git restore --source=checkpoint-10 .
```

### Checkpoint 11 (2025-02-18)
- Integrated PayMob payment gateway
- Added PayMob utilities and configuration
- Enhanced order management system
- Updated order templates and styling
- Added order confirmation page
- Improved logging system
- Added new test cases for PayMob integration
- Updated database schema for PayMob fields
- Updated .gitignore to properly handle sensitive files
- Cleaned up repository structure

To restore to this checkpoint:
```bash
git restore --source=checkpoint-11 .
```

### Checkpoint 12 (2025-02-19)
- Fixed template block naming in checkout page from 'extra_js' to 'scripts'
- Enhanced template consistency across the application
- Improved code organization in checkout process
- Ensured proper JavaScript loading in checkout page

To restore to this checkpoint:
```bash
git restore --source=checkpoint-12 .
```

### Checkpoint 10 (2025-02-19)
- Updated template block names for better consistency
- Changed `extra_js` block to `scripts` in multiple templates:
  - admin/product_form.html
  - wishlist/wishlist.html
  - shop/index.html
  - main/product_detail.html
  - main/category_products.html
- Improved template inheritance structure
- Enhanced code maintainability and readability

To restore to this checkpoint:
```bash
git restore --source=checkpoint-10 .
```

### Checkpoint 13 (2025-02-20)
- Fixed JSON serialization error in shop template
- Fixed wishlist functionality in shop page
- Properly handled current_user.is_authenticated method call
- Improved JavaScript code in shop template for better reliability
- Enhanced error handling for user authentication checks

To restore to this checkpoint:
```bash
git restore --source=checkpoint-13 .
```

## License

This project is licensed under the MIT License.

Last Updated: February 20, 2025