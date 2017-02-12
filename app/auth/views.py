from . import auth
from .. import db
from .forms import LoginForm, RegistrationForm, ResetPasswordRequestForm
from ..models import User
from ..email import send_email

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            #only takes one argument currently, no remember me functionality
            #login_user(user, form.remember_me.data)
            login_user(user, remember=form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, 
            password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm your account', 
            'auth/email/confirm.html', user=user, token=token)
        flash("Complete registration using the link in your confirmation email. The confirmation link will expire in an hour.")
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('Your registration is now complete. Make some songbooks!')
    else:
        flash('The confirmation link is invalid or expired.')
        return redirect(url_for('main.index'))

#need to exclude password reset
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        #update user last_seen in db
        current_user.ping()
        if not current_user.confirmed and request.endpoint[:5] != 'auth.':
            # and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

#modify to only require email, not login?
#modify to combine with 'unconfirmed' so user doesn't have to click through
@auth.route('/confirm/')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm your email', 'auth/email/confirm.html', 
         user=current_user, token=token)
    flash('A new confirmation email has been sent. ' 
        'It expires after an hour.')
    return redirect(url_for('main.index'))

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    form = ResetPasswordRequestForm()
    if not current_user.is_anonymous():
        redirect(url_for('main.index'))
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            token = user.generate_password_reset_token()
            send_email(user.email, 'Password Reset',
                'auth/email/reset_password_request.html', user=user, 
                token=token, next=request.args.get('next'))
            flash('A password reset link has been emailed. It expires after an hour.')
            return redirect(url_for('main.index'))
        #Security risk?
        if user is None:
            flash('We do not have that email in our system.')
    return render_template('auth/reset_password_request.html', form=form)

@auth.route('/reset-password/<token>')
def reset_password(token):
    if not current_user.is_anonymous():
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data)
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('You have successfully reset your password.')
            return redirect(url_for('auth.login'))
        flash('You were not successful at updating your password. ',
            'The link provided may be expired.')
    return redirect(url_for('auth.reset_password_request'))

