from flask_wtf import FlaskForm
from wtforms import SubmitField


class RescanForm(FlaskForm):
    requestRescan = SubmitField("Request Rescan")
