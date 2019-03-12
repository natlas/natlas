from flask import Blueprint
from datetime import datetime
from dateutil import parser

bp = Blueprint('filters', __name__)

@bp.app_template_filter('ctime')
def ctime(s, human=False):
    if human:
        return parser.parse(s).strftime("%Y-%m-%d %H:%M:%S %Z")
    return parser.parse(s).strftime("%Y-%m-%d %H:%M")