# Flask E-commerce Application

A modern e-commerce web application built with Flask, featuring a responsive design, rich user interactions, and a comprehensive admin dashboard.

## Features

### Core Features
- User Authentication (Register, Login)
- Product Catalog with Categories
- Shopping Cart Management
- Multiple Payment Methods
- Wishlist Management
- Order Processing
- User Profile Management
- Admin Dashboard
- Toast Notifications

### Customer Features
- Browse products by categories
- Add/Remove items to cart
- Add/Remove items to wishlist
- Update cart quantities
- View product details
- Place orders with multiple payment options:
  - Credit Card (Stripe)
  - Cash on Delivery (COD)
- View order history
- Manage profile information
- Real-time feedback with toast notifications

### Admin Features
- Product Management
  - Add/Edit/Delete products
  - Image upload handling
  - Category assignment
  - Stock management
  - Pricing controls

- Category Management
  - Create/Edit/Delete categories
  - Product associations

- Order Management
  - View and manage orders
  - Update order status
  - Process COD payments
  - Order history tracking
  - Payment status tracking

- User Management
  - View registered users
  - Manage user accounts
  - Toggle admin privileges

### User Experience
- Modern and responsive design
- Real-time feedback with toast notifications
- Dynamic cart and wishlist updates
- Intuitive payment method selection
- Clear order status tracking
- Comprehensive error handling

## Technical Stack

### Backend
- Flask (Python)
- SQLite/SQLAlchemy
- Flask-Login for authentication
- Flask-WTF for forms and CSRF protection
- Flask-Migrate for database migrations
- Stripe API for payment processing

### Frontend
- HTML5, CSS3, JavaScript
- Bootstrap 5 for responsive design
- Font Awesome icons
- Custom toast notifications
- Dynamic UI updates
- AJAX for seamless interactions

### Payment Integration
- Stripe for card payments
- Custom implementation for COD
- Secure payment processing
- Payment status tracking

## Project Structure
```
flask_ecommerce/
├── app/
│   ├── admin/             # Admin module
│   ├── auth/              # Authentication module
│   ├── cart/              # Shopping cart module
│   ├── wishlist/          # Wishlist module
│   ├── order/            # Order processing module
│   ├── main/             # Main application module
│   ├── static/           # Static assets (CSS, JS, images)
│   │   ├── css/         # Stylesheets
│   │   ├── js/          # JavaScript files
│   │   └── images/      # Uploaded images
│   ├── templates/        # HTML templates
│   └── __init__.py      # Application factory
├── migrations/          # Database migrations
├── instance/           # Instance-specific files
├── requirements.txt    # Project dependencies
└── README.md          # Project documentation
```

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Set up environment variables:
   ```
   FLASK_APP=run.py
   FLASK_ENV=development
   SECRET_KEY=your-secret-key
   STRIPE_PUBLIC_KEY=your-stripe-public-key
   STRIPE_SECRET_KEY=your-stripe-secret-key
   ```
6. Initialize the database:
   ```
   flask db upgrade
   ```
7. Run the application:
   ```
   flask run
   ```

## Access Information

- Main site: http://localhost:5000
- Admin dashboard: http://localhost:5000/admin

Default admin credentials:
- Email: admin@example.com
- Password: adminpass

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.