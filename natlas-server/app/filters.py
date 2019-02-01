from flask import Blueprint
from datetime import datetime

bp = Blueprint('filters', __name__)

@bp.app_template_filter('ctime')
def ctime(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f').strftime("%Y-%m-%d")