from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

class ContactForm(FlaskForm):
    """Contact form for user inquiries"""
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=2, max=50, message='Name must be between 2 and 50 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address'),
        Length(max=120, message='Email must be less than 120 characters')
    ])
    subject = StringField('Subject', validators=[
        DataRequired(),
        Length(min=5, max=100, message='Subject must be between 5 and 100 characters')
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=10, max=2000, message='Message must be between 10 and 2000 characters')
    ])
