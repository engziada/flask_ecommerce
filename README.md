# Flask E-commerce Application

A modern e-commerce web application built with Flask, featuring a responsive design and rich user interactions.

## Features

### Core Features
- User Authentication (Register, Login, Password Reset)
- Product Catalog with Categories
- Shopping Cart Management
- Secure Checkout Process
- User Profile Management
- Address Management
- Order History

### Enhanced Features
- Wishlist Management
  - Dynamic wishlist counter in navigation
  - Toggle items with heart icons
  - Quick view product details
  - Smooth animations for item removal
  - Cross-page consistency
  
- Advanced Cart Features
  - Real-time quantity updates
  - Dynamic total calculations
  - Stock availability checks
  - Quick view product details
  - Enhanced UI/UX

- Product Reviews System
  - Star ratings (1-5)
  - Detailed user comments
  - Form validation with error messages
  - CSRF protection
  - Review timestamps
  - User-specific reviews

- Quick View Modal
  - Shared modal component
  - Dynamic product loading
  - Add to cart functionality
  - Consistent experience

- Order Management System
  - Comprehensive order processing workflow
  - Status tracking with color-coded badges
  - Automated inventory management
  - Multiple address support

  #### Order Status Flow
```
[pending] → [processing] → [shipped] → [delivered]
    ↓           ↓            ↓
    └──────────[cancelled]───┘
```

Status Descriptions:
- `pending`: Initial state when order is placed
- `processing`: Order is being prepared for shipping
- `shipped`: Order has been handed over to shipping carrier
- `delivered`: Order has been received by customer
- `cancelled`: Order cancelled (possible before delivery)

#### Admin Features
- Order filtering by status
- Detailed order view with items and shipping info
- Restricted status transitions
- Order history tracking
- Automated stock management

#### Customer Features
- Order tracking
- Order history view
- Multiple shipping addresses
- Real-time order status updates

### Technical Features
- CSRF Protection
- Form Validation
- Error Handling
- Flash Messages
- Responsive Design
- AJAX Interactions
- Database Migrations
- Context Processors
- Blueprint Structure

## Project Structure
```
flask_ecommerce/
├── app/
│   ├── auth/             # Authentication routes and forms
│   ├── main/             # Main application routes
│   ├── models/           # Database models
│   ├── static/           # Static files (CSS, JS, images)
│   ├── templates/        # Jinja2 templates
│   │   ├── auth/        # Authentication templates
│   │   ├── main/        # Main application templates
│   │   └── includes/    # Reusable template components
│   ├── forms/           # Form classes
│   └── extensions.py    # Flask extensions
├── migrations/          # Database migrations
├── tests/              # Test files
├── config.py           # Configuration files
├── requirements.txt    # Python dependencies
└── run.py             # Application entry point
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd flask_ecommerce
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
set FLASK_APP=run.py
set FLASK_ENV=development
```

5. Initialize the database:
```bash
flask db upgrade
python -m app.sample_data  # Load sample data
```

6. Run the application:
```bash
flask run
```

## Sample Data
The application comes with a sample dataset including:
- Product categories (Electronics, Clothing, Home & Kitchen)
- Sample products with images and descriptions
- User accounts for testing
- Product reviews with ratings and comments

## Development

### Database Migrations
```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

### Running Tests
```bash
python -m pytest
```

## Security Features
- CSRF Protection on all forms
- Secure password hashing
- Protected API endpoints
- Input validation
- Error logging
- Session management

## Future Improvements
1. Product review system enhancements
2. Advanced search and filtering
3. Product recommendations
4. Social sharing features
5. Performance optimizations
6. Enhanced admin interface
7. Order tracking system
8. Email notifications
9. Payment gateway integration
10. Inventory management

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.