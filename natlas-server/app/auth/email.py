from flask import render_template, current_app
from app.email import send_email


def send_password_reset_email(user):
		token = user.new_token('reset')
		send_email(
			'[Natlas] Reset Your Password',
			sender=current_app.config['MAIL_FROM'],
			recipients=[user.email],
			text_body=render_template('email/reset_password.txt', user=user, token=token)
		)


def send_user_invite_email(user):
		token = user.new_token('invite')
		send_email(
			'[Natlas] You\'ve been invited to Natlas!',
			sender=current_app.config['MAIL_FROM'],
			recipients=[user.email],
			text_body=render_template('email/user_invite.txt', user=user, token=token)
		)
