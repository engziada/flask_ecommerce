# Flask E-commerce Application

A modern e-commerce web application built with Flask, featuring a responsive design, rich user interactions, and a comprehensive admin dashboard.

## Features

### Core Features
- User Authentication (Register, Login)
- Product Catalog with Categories
- Shopping Cart Management
- Order Processing
- User Profile Management
- Admin Dashboard

### Customer Features
- Browse products by categories
- Add/Remove items to cart
- Update cart quantities
- View product details
- Place orders
- View order history
- Manage profile information

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
  - Order history tracking

- User Management
  - View registered users
  - Manage user accounts

## Technical Stack

- Backend: Flask (Python)
- Database: SQLite/SQLAlchemy
- Frontend: HTML5, CSS3, JavaScript
- UI Framework: Bootstrap
- Icons: Font Awesome
- Form Handling: Flask-WTF
- Authentication: Flask-Login
- Database ORM: Flask-SQLAlchemy

## Project Structure
```
flask_ecommerce/
├── app/
│   ├── admin/             # Admin module
│   ├── auth/              # Authentication module
│   ├── cart/              # Shopping cart module
│   ├── main/              # Main application module
│   ├── static/            # Static assets (CSS, JS, images)
│   ├── templates/         # HTML templates
│   └── __init__.py        # Application factory
├── migrations/            # Database migrations
├── instance/             # Instance-specific files
├── requirements.txt      # Project dependencies
└── README.md            # Project documentation
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
5. Initialize the database:
   ```
   flask db upgrade
   ```
6. Run the application:
   ```
   flask run
   ```

## Access Information

- Main site: http://localhost:5000
- Admin dashboard: http://localhost:5000/admin

## Contributing

Feel free to submit issues and enhancement requests.