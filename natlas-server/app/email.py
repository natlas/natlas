from flask_mail import Message
from flask import current_app
from app import mail
from threading import Thread


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    Thread(
        target=send_async_email, args=(current_app._get_current_object(), msg)
    ).start()
