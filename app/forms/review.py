"""Review form."""
from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class ReviewForm(FlaskForm):
    """Review form."""
    rating = SelectField('Rating', 
                        choices=[(5, '5 - Excellent'),
                                (4, '4 - Very Good'),
                                (3, '3 - Good'),
                                (2, '2 - Fair'),
                                (1, '1 - Poor')],
                        coerce=int,
                        validators=[DataRequired()])
    comment = TextAreaField('Your Review', 
                          validators=[DataRequired(),
                                    Length(min=10, max=500, 
                                          message='Review must be between 10 and 500 characters')])
    submit = SubmitField('Submit Review')
