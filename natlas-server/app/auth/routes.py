from flask import redirect, url_for, flash, render_template, request, current_app, session
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, \
	ResetPasswordForm, InviteConfirmForm
from app.models import User, EmailToken
from app.auth.email import send_password_reset_email
from app.auth import bp
from werkzeug.urls import url_parse

@bp.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=User.validate_email(form.email.data)).first()
		if user is None or not user.check_password(form.password.data):
			flash('Invalid email or password', 'danger')
			return redirect(url_for('auth.login'))
		login_user(user, remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('main.index')
		return redirect(next_page)
	return render_template('auth/login.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	if not current_app.config['REGISTER_ALLOWED']:
		flash("Sorry, we're not currently accepting new users. If you feel you've received this message in error, please contact an administrator.", "warning")
		return redirect(url_for('auth.login'))
	form = RegistrationForm()
	if form.validate_on_submit():
		validemail = User.validate_email(form.email.data)
		if not validemail:
			flash("%s does not appear to be a valid, deliverable email address." % form.email.data, "danger")
			return redirect(url_for('auth.register'))
		user = User(email=validemail)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('Congratulations, you are now a registered user!', 'success')
		return redirect(url_for('auth.login'))
	return render_template('auth/register.html', title='Register', form=form)


@bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		validemail = User.validate_email(form.email.data)
		if not validemail:
			flash("%s does not appear to be a valid, deliverable email address." % form.email.data, "danger")
			return redirect(url_for('auth.reset_password_request'))
		user = User.query.filter_by(email=validemail).first()
		if user:
			send_password_reset_email(user)
		flash('Check your email for the instructions to reset your password', "info")
		return redirect(url_for('auth.login'))
	return render_template('auth/password_reset.html',
						   title='Request Password Reset', form=form, pwrequest=True)


@bp.route('/reset_password/<token>', methods=['GET'])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	session['reset_token'] = token
	return redirect(url_for('auth.do_password_reset'))

@bp.route('/reset_password/reset', methods=['GET', 'POST'])
def do_password_reset():
	token = session['reset_token']
	if not token:
		flash("Token not found!", "danger")
		return redirect(url_for('auth.login'))

	user = User.verify_reset_password_token(token)
	if not user:
		flash("Password reset token is invalid or has expired.", "danger")
		session.pop('reset_token', None) # remove the invalid token from the session
		return redirect(url_for('auth.login'))

	form = ResetPasswordForm()
	if form.validate_on_submit():
		user.set_password(form.password.data)
		EmailToken.expire_token(tokenstr=token)
		session.pop('reset_token', None) # remove the reset token from the session
		# No need to db.session.commit() because expire_token commits the session for us

		flash('Your password has been reset.', "success")
		return redirect(url_for('auth.login'))
	return render_template('auth/password_reset.html', title="Reset Password", form=form)


@bp.route('/invite/<token>', methods=['GET'])
def invite_user(token):
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	session['invite_token'] = token
	return redirect(url_for('auth.accept_invite'))

@bp.route('/invite/accept', methods=['GET', 'POST'])
def accept_invite():
	token = session['invite_token']
	if not token:
		flash("Token not found!", "danger")
		return redirect(url_for('auth.login'))
	
	user = User.verify_invite_token(token)
	if not user:
		flash("Invite token is invalid or has expired", "danger")
		session.pop('invite_token', None) # remove the invalid token from the session
		return redirect(url_for('auth.login'))

	form = InviteConfirmForm()
	if form.validate_on_submit():
		user.set_password(form.password.data)
		EmailToken.expire_token(tokenstr=token)
		session.pop('invite_token', None) # remove the invite token from the session
		# No need to db.session.commit() because expire_token commits the session for us

		flash('Your password has been set.', "success")
		return redirect(url_for('auth.login'))
	return render_template('auth/accept_invite.html', title="Accept Invitation", form=form)

