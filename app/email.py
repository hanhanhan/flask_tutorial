from threading import Thread 
from flask import render_template, current_app
from flask_mail import Message
from . import mail


def send_async_mail(app, message):
    with app.app_context():
        mail.send(message)

def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    message = Message(app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject, 
        sender=app.config['MAIL_SENDER'], recipients=[to])
    message.body = render_template(template, **kwargs)
    message.html = render_template(template, **kwargs)
    thr = Thread(target=send_async_mail, args=[app, message])
    thr.start()
    return thr