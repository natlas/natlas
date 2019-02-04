from flask import redirect, url_for, flash, render_template, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, \
    ResetPasswordForm, InviteConfirmForm
from app.models import User
from app.auth.email import send_password_reset_email
from app.auth import bp
from werkzeug.urls import url_parse

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
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
    if current_app.config['REGISTER_ALLOWED'].lower() == "false":
        flash("Sorry, we're not currently accepting new users. If you feel you've received this message in error, please contact an administrator.", "warning")
        return redirect(url_for('auth.login'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password', "info")
        return redirect(url_for('auth.login'))
    return render_template('auth/password_reset.html',
                           title='Reset Password', form=form, pwrequest=True)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', "success")
        return redirect(url_for('main.login'))
    return render_template('auth/password_reset.html', form=form)


@bp.route('/invite/<token>', methods=['GET', 'POST'])
def invite_user(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_invite_token(token)
    if not user:
        flash("Failed to verify invite token!", "danger")
        flash(User.verify_invite_token(token))
        return redirect(url_for('main.index'))
    form = InviteConfirmForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been set.', "success")
        return redirect(url_for('auth.login'))
    return render_template('auth/accept_invite.html', form=form)