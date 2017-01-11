from flask_wtf import FlaskForm
#from flask_wtf import Form # tutorial format, docs say deprecated
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import Required, Length, Email, Regexp
from ..models import User
#User ValidationError

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


#can't this just inherit from EditProfileForm?
class EditProfileAdminForm(FlaskForm):
    email = StringField('Email',
            validators=[Required(), Length(1, 64), Email()])
    username = StringField('Username', validators=[Required(), Length(1, 64),
            Email(), Regexp('^[A-z][A-z_.0-9]*', 0, 
            'Usernames must begin with a letter and contain either letters, numbers, underscores or periods.')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=Length(0, 64))
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        #super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

        # would prefer not to update email field until confirmed
        # would also prefer not to tell user if email in use if not associated with their account
        def validate_email(self, field):
            if field.data != self.user.email and \
                    User.query.filter_by(username=field.data).first():
                raise ValidationError('This email is already registered.')

        def validate_username(self, field):
            if field.data != self.user.username and \
                    User.query.filter_by(username=field.data).first():
                raise ValidationError('This username is already in use.')


class PostForm(FlaskForm):
    body = TextAreaField("What's on you're mind?", validators=[Required()])
    submit = SubmitField('Submit')
    