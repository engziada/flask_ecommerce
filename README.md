# Flask E-Commerce Platform

A scalable and customizable e-commerce platform built with Flask.

## Features

- User Authentication and Authorization
- Product Management
- Shopping Cart
- Secure Checkout Process
- Order Management
- User Profiles
- Admin Dashboard
- Search Functionality
- Reviews and Ratings
- Email Notifications

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///shop.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## Project Structure

```
flask_ecommerce/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   └── templates/
├── migrations/
├── instance/
├── tests/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── run.py
```

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

Copyright (c) 2023 M.Ziada @ ZSoft

## Email Setup
Now, to use Gmail for sending emails, you'll need to:

Enable 2-Step Verification in your Google Account:
Go to your Google Account settings
Click on "Security"
Enable "2-Step Verification"
Generate an App Password:
Go to your Google Account settings
Click on "Security"
Under "2-Step Verification", click on "App passwords"
Select "Mail" as the app and "Other" as the device
Enter "Flask Shop" as the name
Click "Generate"
Copy the 16-character password
Update the .env file with your Gmail credentials:
Replace your-email@gmail.com with your actual Gmail address
Replace your-app-password with the 16-character app password you generated