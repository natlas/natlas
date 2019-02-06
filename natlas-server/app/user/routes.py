from flask import render_template, redirect, url_for, current_app, flash, Response, abort
from flask_login import current_user
from app import db
from app.user import bp
from app.user.forms import ChangePasswordForm, DisplaySettingsForm
from app.models import User
from app.auth.wrappers import isAuthenticated, isAdmin
import ipaddress

@bp.route('/', methods=['GET', 'POST'])
@isAuthenticated
def profile():
    changePasswordForm = ChangePasswordForm(prefix="change-password")
    displaySettingsForm = DisplaySettingsForm(prefix="display-settings", results_per_page=current_user.results_per_page, \
        preview_length=current_user.preview_length)
    displaySettingsForm.results_per_page.choices = [(25,25), (50,50), (75,75), (100,100)]
    displaySettingsForm.preview_length.choices = [(25,25), (50,50), (75,75), (100,100)]
    if changePasswordForm.changePassword.data and changePasswordForm.validate_on_submit():
            user = User.query.get(current_user.id)
            user.set_password(changePasswordForm.password.data)
            db.session.commit()
            flash('Your password has been changed.', "success")
            return redirect(url_for('user.profile'))
    if displaySettingsForm.updateDisplaySettings.data and displaySettingsForm.validate_on_submit():
            user = User.query.get(current_user.id)
            user.results_per_page = displaySettingsForm.results_per_page.data
            user.preview_length = displaySettingsForm.preview_length.data
            db.session.commit()
            flash("Display settings updated.", "success")
            return redirect(url_for('user.profile'))
    return render_template("user/profile.html", changePasswordForm=changePasswordForm, displaySettingsForm=displaySettingsForm)