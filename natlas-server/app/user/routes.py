from flask import render_template, redirect, url_for, current_app, flash, Response, abort, request
from flask_login import current_user
from app import db
from app.user import bp
from app.user.forms import ChangePasswordForm, DisplaySettingsForm, GenerateTokenForm, AgentNameForm
from app.models import User, Agent
from app.auth.wrappers import isAuthenticated, isAdmin
import ipaddress

@bp.route('/', methods=['GET', 'POST'])
@isAuthenticated
def profile():
    # Handle this case because isAuthenticated only applies when LOGIN_REQUIRED is true
    if current_user.is_anonymous:
        flash("You must be a user to access %s" % request.path, "warning")
        return redirect(url_for('main.index'))
    myagents = current_user.agents
    changePasswordForm = ChangePasswordForm(prefix="change-password")
    displaySettingsForm = DisplaySettingsForm(prefix="display-settings", results_per_page=current_user.results_per_page, \
        preview_length=current_user.preview_length)
    displaySettingsForm.results_per_page.choices = [(25,25), (50,50), (75,75), (100,100)]
    displaySettingsForm.preview_length.choices = [(25,25), (50,50), (75,75), (100,100)]

    generateTokenForm = GenerateTokenForm()
    agentNameForm = AgentNameForm()
    newAgentForm = AgentNameForm()

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
    return render_template("user/profile.html", changePasswordForm=changePasswordForm, displaySettingsForm=displaySettingsForm, \
        agents=myagents, generateTokenForm=generateTokenForm, agentNameForm=agentNameForm, newAgentForm=newAgentForm)

@bp.route('/agent/<string:agent_id>/newToken', methods=['POST'])
@isAuthenticated
def generateNewToken(agent_id):
    generateTokenForm = GenerateTokenForm()

    if generateTokenForm.validate_on_submit():
        myAgent = Agent.load_agent(agent_id)
        myAgent.token = Agent.generate_token()
        db.session.commit()
        flash("Agent %s has a new key of: %s" % (myAgent.agentid, myAgent.token), "success")
        return redirect(request.referrer)
    else:
        flash("Couldn't generate new token", "danger")
        return redirect(request.referrer)

@bp.route('/agent/<string:agent_id>/newName', methods=['POST'])
@isAuthenticated
def changeAgentName(agent_id):
    agentNameForm = AgentNameForm()

    if agentNameForm.validate_on_submit():
        myAgent = Agent.load_agent(agent_id)
        oldname = myAgent.friendly_name
        myAgent.friendly_name = agentNameForm.agent_name.data
        db.session.commit()
        flash("Agent name changed from %s to %s" % (oldname, myAgent.friendly_name), "success")
        return redirect(request.referrer)
    else:
        flash("Couldn't change agent name", "danger")
        return redirect(request.referrer)

@bp.route('/agent/newAgent', methods=['POST'])
@isAuthenticated
def newAgent():
    newAgentForm = AgentNameForm()

    if newAgentForm.validate_on_submit():
        myAgent = Agent(user_id=current_user.id, agentid=Agent.generate_agentid(), token=Agent.generate_token(), \
            friendly_name=newAgentForm.agent_name.data)
        db.session.add(myAgent)
        db.session.commit()
        flash("New Agent named %s created. Agent ID: %s Agent Token: %s" \
            % (myAgent.friendly_name, myAgent.agentid, myAgent.token), "success")
        return redirect(request.referrer)
    else:
        flash("Couldn't create new agent", "danger")
        return redirect(request.referrer)