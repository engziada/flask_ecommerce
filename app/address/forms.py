from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length
from app.shipping.services import BostaCityMapping

class AddressForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    street = StringField('Street Address', validators=[DataRequired()])
    building_number = StringField('Building Number')
    floor = StringField('Floor')
    apartment = StringField('Apartment')
    city = SelectField('City', validators=[DataRequired()], choices=BostaCityMapping.get_city_choices())
    district = StringField('District')
    postal_code = StringField('Postal Code')
    is_default = BooleanField('Set as Default Address')
