from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, TelField
from wtforms.validators import DataRequired, Email, Length, Optional

class ContactForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    
    phone = TelField('Phone Number', validators=[
        Optional(),
        Length(min=7, max=20, message='Please enter a valid phone number')
    ])
    
    address = StringField('Address', validators=[
        Optional(),
        Length(max=200, message='Address cannot exceed 200 characters')
    ])
    
    message = TextAreaField('Your Message', validators=[
        Optional(),
        Length(max=1000, message='Message cannot exceed 1000 characters')
    ])
    
    submit = SubmitField('Submit Form')
