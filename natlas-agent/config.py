import os
from dotenv import load_dotenv

class Config:

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASEDIR, '.env'))

    def __init__(self):
        self.server = os.environ.get('NATLAS_SERVER_ADDRESS') or 'http://127.0.0.1:5000' # url of server to get/submit work to
        self.max_threads = os.environ.get('NATLAS_MAX_THREADS') or 3 # maximum number of threads to utilize
        self.scan_local = os.environ.get('NATLAS_SCAN_LOCAL') or False # Are we allowed to scan local addresses?
        self.request_timeout = os.environ.get('NATLAS_REQUEST_TIMEOUT') or 15 # seconds, default time to wait for the server to respond
        self.backoff_max = os.environ.get('NATLAS_BACKOFF_MAX') or 300 # seconds, 5 minutes default
        self.backoff_base = os.environ.get('NATLAS_BACKOFF_BASE') or 1 # seconds