from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('Description')

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    sku = StringField('SKU', validators=[Optional(), Length(max=32)])
    weight = FloatField('Weight (kg)', validators=[Optional(), NumberRange(min=0)])
    dimensions = StringField('Dimensions', validators=[Optional(), Length(max=32)])
    is_active = BooleanField('Active', default=True)
