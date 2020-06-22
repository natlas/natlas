from flask import render_template, current_app
from app.email import send_email


def send_auth_email(email, token, token_type):
	token_types = {
		"reset": {
			"subject": "[Natlas] Reset Your Password",
			"template": "email/reset_password.txt"
		},
		"invite": {
			"subject": "[Natlas] You've been invited to Natlas!",
			"template": "email/user_invite.txt"
		}
	}
	send_email(
		token_types[token_type]["subject"],
		sender=current_app.config['MAIL_FROM'],
		recipients=[email],
		text_body=render_template(token_types[token_type]["template"], token=token)
	)
