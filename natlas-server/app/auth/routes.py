from flask import redirect, url_for, flash, render_template, request, current_app
from flask_login import login_user, logout_user
from app import db
from app.auth.forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordRequestForm,
    ResetPasswordForm,
    AcceptInviteForm,
)
from app.models import User, UserInvitation
from app.auth.email import send_auth_email, validate_email
from app.auth import bp
from app.auth.wrappers import is_not_authenticated, is_authenticated
from werkzeug.urls import url_parse


@bp.route("/login", methods=["GET", "POST"])
@is_not_authenticated
def login():
    form = LoginForm(prefix="login")
    if form.validate_on_submit():
        user = User.query.filter_by(email=User.validate_email(form.email.data)).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password", "danger")
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("main.index")
        return redirect(next_page)
    return render_template("auth/login.html", title="Sign In", form=form)


@bp.route("/logout")
@is_authenticated
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@bp.route("/register", methods=["GET", "POST"])
@is_not_authenticated
def register():
    if not current_app.config["REGISTER_ALLOWED"]:
        flash(
            "Sorry, we're not currently accepting new users. If you feel you've received this message in error, please contact an administrator.",
            "warning",
        )
        return redirect(url_for("auth.login"))
    form = RegistrationForm(prefix="register")
    if form.validate_on_submit():
        validemail = validate_email(form.email.data)
        if not validemail:
            return redirect(url_for("auth.register"))
        user = User(email=validemail, is_active=True)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Congratulations, you are now a registered user!", "success")
        return redirect(url_for("main.browse"))
    return render_template("auth/register.html", title="Register", form=form)


@bp.route("/reset_password_request", methods=["GET", "POST"])
@is_not_authenticated
def reset_password_request():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        validemail = validate_email(form.email.data)
        if not validemail:
            return redirect(url_for("auth.reset_password_request"))
        user = User.get_reset_token(validemail)
        if user:
            send_auth_email(user.email, user.password_reset_token, "reset")
        db.session.commit()
        flash("Check your email for the instructions to reset your password", "info")
        return redirect(url_for("auth.login"))
    return render_template(
        "auth/password_reset.html",
        title="Request Password Reset",
        form=form,
        pwrequest=True,
    )


@bp.route("/reset_password", methods=["GET", "POST"])
@is_not_authenticated
def reset_password():
    url_token = request.args.get("token", None)
    if not url_token:
        flash("No reset token found")
        return redirect(url_for("auth.login"))
    user = User.get_user_by_token(url_token)
    if not user:
        flash("Password reset token is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.expire_reset_token()
        db.session.commit()
        flash("Your password has been reset.", "success")
        return redirect(url_for("auth.login"))
    return render_template(
        "auth/password_reset.html", title="Reset Password", form=form
    )


@bp.route("/invite", methods=["GET", "POST"])
@is_not_authenticated
def invite_user():
    url_token = request.args.get("token", None)
    invite = UserInvitation.get_invite(url_token)
    if not invite:
        flash("Invite token is invalid or has expired", "danger")
        return redirect(url_for("auth.login"))

    supported_forms = {
        "invite": {"form": AcceptInviteForm, "template": "auth/accept_invite.html"},
        "register": {"form": RegistrationForm, "template": "auth/register.html"},
    }

    form_type = "invite" if invite.email else "register"
    form = supported_forms[form_type]["form"]()
    if form.validate_on_submit():
        email = invite.email if invite.email else form.email.data
        new_user = User.new_user_from_invite(invite, form.password.data, email=email)
        db.session.commit()
        login_user(new_user)
        flash("Your password has been set.", "success")
        return redirect(url_for("main.browse"))
    return render_template(
        supported_forms[form_type]["template"], title="Accept Invitation", form=form
    )
