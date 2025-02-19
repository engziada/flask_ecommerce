from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, SelectField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, NumberRange, Optional, ValidationError, Length, Regexp
from werkzeug.datastructures import FileStorage
from app.models.product import Product
from app.utils import allowed_file
from flask import request
import re

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('Description')

class ProductImageForm(FlaskForm):
    """Form for product images"""
    image = FileField('Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only JPG, JPEG, PNG, and GIF images are allowed.')
    ])
    is_primary = BooleanField('Primary Image')

    def validate_image(self, field):
        """Validate the uploaded image"""
        if field.data and isinstance(field.data, FileStorage):
            if not allowed_file(field.data.filename):
                raise ValidationError('Invalid file type. Only JPG, JPEG, PNG, and GIF images are allowed.')
            
            # Check file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            field.data.seek(0, 2)  # Seek to end of file
            size = field.data.tell()  # Get size
            field.data.seek(0)  # Reset to beginning
            
            if size > max_size:
                raise ValidationError('File is too large. Maximum size is 5MB.')

class ProductForm(FlaskForm):
    """Form for creating and editing products"""
    name = StringField('Product Name', validators=[
        DataRequired(message='Product name is required.'),
        Length(min=2, max=100, message='Product name must be between 2 and 100 characters.')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(message='Product description is required.'),
        Length(min=10, max=2000, message='Description must be between 10 and 2000 characters.')
    ])
    price = DecimalField('Price (EGP)', validators=[
        DataRequired(message='Price is required.'),
        NumberRange(min=0, message='Price cannot be negative.'),
        NumberRange(max=1000000, message='Price cannot exceed 1,000,000 EGP.')
    ], places=2)
    stock = IntegerField('Stock', validators=[
        DataRequired(message='Stock is required.'),
        NumberRange(min=0, message='Stock cannot be negative.')
    ])
    category_id = SelectField('Category', validators=[
        DataRequired(message='Please select a category.')
    ], coerce=int)
    sku = StringField('SKU', validators=[
        Optional(),
        Length(max=20, message='SKU must be less than 20 characters.')
    ])
    weight = DecimalField('Weight (kg)', validators=[
        Optional(),
        NumberRange(min=0, message='Weight cannot be negative.')
    ], places=2)
    dimensions = StringField('Dimensions', validators=[
        Optional(),
        Length(max=50, message='Dimensions must be less than 50 characters.'),
        Regexp(r'^\d+(\.\d+)?\s*x\s*\d+(\.\d+)?\s*x\s*\d+(\.\d+)?$', message='Dimensions must be in format: length x width x height')
    ])
    is_active = BooleanField('Active')
    images = FieldList(FormField(ProductImageForm), min_entries=1)

    def __init__(self, *args, **kwargs):
        """Initialize the form"""
        super(ProductForm, self).__init__(*args, **kwargs)
        self.product_id = None

    def validate_sku(self, field):
        """Validate SKU uniqueness"""
        if field.data:
            # Clean SKU data - strip whitespace and convert to uppercase
            field.data = field.data.strip().upper()
            
            # Check if SKU exists for another product
            if self.product_id:
                exists = Product.query.filter(
                    Product.sku == field.data,
                    Product.id != self.product_id
                ).first()
            else:
                exists = Product.query.filter_by(sku=field.data).first()
            
            if exists:
                raise ValidationError('This SKU is already in use.')

    def validate_images(self, field):
        """Validate that at least one image is present"""
        has_image = False
        
        # Check for new uploaded images
        for image_form in field:
            if image_form.image.data and isinstance(image_form.image.data, FileStorage):
                has_image = True
                break
        
        # Check for existing images in the form submission
        if not has_image:
            for key in request.form:
                if key.startswith('existing_images-'):
                    has_image = True
                    break
        
        if not has_image:
            raise ValidationError('At least one product image is required.')
