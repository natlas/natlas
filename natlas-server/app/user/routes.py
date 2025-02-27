from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers.response import Response as wzResponse

from app import db
from app.models import Agent, User
from app.user import bp
from app.user.forms import (
    AgentNameForm,
    ChangePasswordForm,
    DisplaySettingsForm,
    GenerateTokenForm,
)


@bp.route("/", methods=["GET", "POST"])
@login_required  # type: ignore[misc]
def profile() -> str:
    myagents = current_user.agents
    changePasswordForm = ChangePasswordForm(prefix="change-password")
    displaySettingsForm = DisplaySettingsForm(
        prefix="display-settings",
        results_per_page=current_user.results_per_page,
        preview_length=current_user.preview_length,
        result_format=current_user.result_format,
    )
    displaySettingsForm.results_per_page.choices = [
        (25, 25),
        (50, 50),
        (75, 75),
        (100, 100),
    ]
    displaySettingsForm.preview_length.choices = [
        (25, 25),
        (50, 50),
        (75, 75),
        (100, 100),
    ]
    displaySettingsForm.result_format.choices = [(0, "Pretty"), (1, "Raw")]

    generateTokenForm = GenerateTokenForm()
    agentNameForm = AgentNameForm()

    if (
        changePasswordForm.changePassword.data
        and changePasswordForm.validate_on_submit()
    ):
        user = db.session.get(User, current_user.id)
        user.set_password(changePasswordForm.password.data)  # type: ignore[union-attr]
        db.session.commit()
        flash("Your password has been changed.", "success")
    elif (
        displaySettingsForm.updateDisplaySettings.data
        and displaySettingsForm.validate_on_submit()
    ):
        user = db.session.get(User, current_user.id)
        user.results_per_page = displaySettingsForm.results_per_page.data  # type: ignore[union-attr]
        user.preview_length = displaySettingsForm.preview_length.data  # type: ignore[union-attr]
        user.result_format = displaySettingsForm.result_format.data  # type: ignore[union-attr]
        db.session.commit()
        flash("Display settings updated.", "success")

    return render_template(
        "user/profile.html",
        changePasswordForm=changePasswordForm,
        displaySettingsForm=displaySettingsForm,
        agents=myagents,
        generateTokenForm=generateTokenForm,
        agentNameForm=agentNameForm,
    )


@bp.route("/agent/<string:agent_id>/newToken", methods=["POST"])
@login_required  # type: ignore[misc]
def generate_new_token(agent_id: str) -> wzResponse:
    generateTokenForm = GenerateTokenForm()

    if generateTokenForm.validate_on_submit():
        myAgent = Agent.load_agent(agent_id)
        myAgent.token = Agent.generate_token()  # type: ignore[union-attr]
        db.session.commit()
        flash(f"Agent {myAgent.agentid} has a new key of: {myAgent.token}", "success")  # type: ignore[union-attr]
    else:
        flash("Couldn't generate new token", "danger")
    return redirect(url_for("user.profile"))


@bp.route("/agent/<string:agent_id>/newName", methods=["POST"])
@login_required  # type: ignore[misc]
def change_agent_name(agent_id: str) -> wzResponse:
    agentNameForm = AgentNameForm()

    if agentNameForm.validate_on_submit():
        myAgent = Agent.load_agent(agent_id)
        oldname = myAgent.friendly_name  # type: ignore[union-attr]
        myAgent.friendly_name = agentNameForm.agent_name.data  # type: ignore[union-attr]
        db.session.commit()
        flash(
            f"Agent name changed from {oldname} to {myAgent.friendly_name}",  # type: ignore[union-attr]
            "success",
        )
    else:
        flash("Couldn't change agent name", "danger")
    return redirect(url_for("user.profile"))


@bp.route("/agent/newAgent", methods=["POST"])
@login_required  # type: ignore[misc]
def new_agent() -> wzResponse:
    newAgentForm = AgentNameForm()

    if newAgentForm.validate_on_submit():
        myAgent = Agent(
            user_id=current_user.id,
            agentid=Agent.generate_agentid(),
            token=Agent.generate_token(),
            friendly_name=newAgentForm.agent_name.data,
        )
        db.session.add(myAgent)
        db.session.commit()
        flash(
            f"New Agent named {myAgent.friendly_name} created. Agent ID: {myAgent.agentid} Agent Token: {myAgent.token}",
            "success",
        )
    else:
        flash("Couldn't create new agent", "danger")
    return redirect(url_for("user.profile"))
