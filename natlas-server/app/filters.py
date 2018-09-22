from app import app
from datetime import datetime

@app.template_filter('ctime')
def ctime(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f').strftime("%Y-%m-%d")