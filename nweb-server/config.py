import os

basedir = os.path.abspath(os.path.dirname(__file__))

ELASTICSEARCH_URL = ''
SCOPE_DOC = os.path.join(basedir, 'config/scope.txt')
BLACKLIST_DOC = os.path.join(basedir, 'config/blacklist.txt')
RESULTS_PER_PAGE = 100
PREVIEW_LENGTH = 100