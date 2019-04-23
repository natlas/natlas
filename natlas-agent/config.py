import os
from dotenv import load_dotenv

class Config:

    # Current Version
    NATLAS_VERSION="0.6.3"

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASEDIR, '.env'))

    def getInt(self, varname):
        tmp = os.environ.get(varname)
        if tmp:
            return int(tmp)
        return None

    def getBool(self, varname):
        tmp = os.environ.get(varname)
        if tmp and tmp.upper() == "TRUE":
            return True
        if tmp and tmp.upper() == "FALSE":
            return False
        return None

    def __init__(self):
        # url of server to get/submit work from/to
        self.server = os.environ.get('NATLAS_SERVER_ADDRESS') or 'http://127.0.0.1:5000' 

        # ignore warnings about SSL connections
        # you shouldn't ignore ssl warnings, but I'll give you the option
        # Instead, you should put the trusted CA certificate bundle on the agent and use the REQUESTS_CA_BUNDLE env variable
        self.ignore_ssl_warn = self.getBool('NATLAS_IGNORE_SSL_WARN') or False 

        # maximum number of threads to utilize
        self.max_threads = self.getInt('NATLAS_MAX_THREADS') or 3 

        # Are we allowed to scan local addresses?
        # By default, agents protect themselves from scanning their local network
        self.scan_local = self.getBool('NATLAS_SCAN_LOCAL') or False 

        # default time to wait for the server to respond
        self.request_timeout = self.getInt('NATLAS_REQUEST_TIMEOUT') or 15 # seconds

        # Maximum value for exponential backoff of requests, 5 minutes default 
        self.backoff_max = self.getInt('NATLAS_BACKOFF_MAX') or 300 # seconds

        # Base value to begin the exponential backoff
        self.backoff_base = self.getInt('NATLAS_BACKOFF_BASE') or 1 # seconds

        # Maximum number of times to retry submitting data before giving up
        # This is useful if a thread is submitting data that the server doesn't understand for some reason
        self.max_retries = self.getInt('NATLAS_MAX_RETRIES') or 10

        # Identification string that identifies the agent that performed any given scan
        # Used for database lookup and stored in scan output
        self.agent_id = os.environ.get("NATLAS_AGENT_ID") or None

        # Authentication token that agents can use to talk to the server API
        # Only needed if the server is configured to require agent authentication
        self.auth_token = os.environ.get("NATLAS_AGENT_TOKEN") or None
