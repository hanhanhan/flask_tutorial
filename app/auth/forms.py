from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from ..models import User

class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class RegistrationForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(5,64), Email()])
    #Ch8 Flags and message are now keyword not postitional arguments
    #SQL is unicode string, make username unicode too? 
    username = StringField('Username', validators=[DataRequired(), Length(1,64), 
        Regexp('^\w*$', flags=0, 
        message='Username must consist of unicode characters.')])
    #Ch8 defined in order password, password2 in tut, but then password2 not defined
    #Regex unicode requirement?
    password = PasswordField('Password', validators=[DataRequired(), Length(3, 64),
        EqualTo('password2', "Passwords must match.")])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email is already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username is already registered.')

class ResetPasswordRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(Form):
    password = PasswordField('Password', validators=[DataRequired(), 
        EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password') 
