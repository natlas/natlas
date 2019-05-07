# natlas-server

Installing Elasticsearch
------------------------
Natlas uses Elasticsearch 6.6 to store all of the scan results. If you want to run Elasticsearch locally on your natlas-server, simply run the `./setup-elastic.sh` script. 

Alternatively, if you already have an elastic cluster that you'd like to use, you can add it to the `.env` file with the name `ELASTICSEARCH_URL`.


The Setup
------------------
The setup script has been tested on Ubuntu 18.10:

```
$ sudo ./setup-server.sh
```

The Config
------------------
There are a number of config options that you can specify in a file called `.env` before initializing the database and launching the application. These options break down into two categories:

Can't be changed via the web interface (only `.env`):

- `SECRET_KEY` defaults to `you-should-set-a-secret-key`, however the `setup-server.sh` script will generate a random value for you if you don't have an existing `SECRET_KEY` set.
- `SQLALCHEMY_DATABASE_URI` defaults to a sqlite database in the natlas-server directory `sqlite:///metadata.db`
- `FLASK_ENV` defaults to `production` and should not be changed unless you are developing for natlas.
- `FLASK_APP` defaults to `natlas-server.py` and should not be changed. It's what allows commands like `flask run`, `flask db upgrade`, and `flask shell` to run.

Can be changed via the web interface:

- `LOGIN_REQUIRED` defaults to `False`
- `REGISTER_ALLOWED` defaults to `False`
- `ELASTICSEARCH_URL` defaults to `http://localhost:9200`
- `MAIL_SERVER` defaults to `localhost`
- `MAIL_PORT` defaults to `25`
- `MAIL_USE_TLS` defaults to `False`
- `MAIL_USERNAME` defaults to `""`
- `MAIL_PASSWORD` defaults to `""`
- `MAIL_FROM` defaults to `""`

For most installations, the defaults will probably be fine (with the exception of `SECRET_KEY`, which you should **absolutely** set), however user invitations won't work without a valid mail server. 


Initializing the Database
------------------
The database should be initialized automatically during the `./setup-server` script, but if it is not for whatever reason, this is the manual steps required to intiialize or upgrade the database.

```
$ source venv/bin/activate
$ export FLASK_APP=./natlas-server.py
$ flask db upgrade
$ deactivate
```


Setting the Scope
------------------
The scope and blacklist can be set server side without using the admin interface by running the `./add-scope.py` script from within the natlas `venv` with the `--scope` and `--blacklist` arguments, respectively. These each take a file name to read scope from. You may optionally specify `--verbose` to see exactly which scope items succeeded to import, failed to import, or already existed in the scope. A scope is **REQUIRED** for agents to do any work, however a blacklist is optional.

```
$ source venv/bin/activate
$ python3 add-scope.py --scope myscopefile.txt
$ python3 add-scope.py --blacklist myblacklist.txt
(optional) $ python3 add-scope.py --scope myscopefile.txt --blacklist myblacklist.txt --verbose
```


Giving a User Admin Privilege
------------------
In order to get started interacting with Natlas, you'll need an administrator account. Admins are allowed to make changes to the following via the web interface: 

- application config
- the user list
- the scope
- the blacklist
- services that agents scan for

To create a new admin account, ensure that you're in the natlas server `venv` and then run `./add-user.py --admin <email>`. If this email doesn't already exist in the User table, it will be created with admin privileges and a random password will be generated and spit out to the command line. If the email *does* already exist in the User table, it will be toggled to be an admin. This can be helpful if you accidentally remove yourself as an admin and can't get back into the admin interface.

```
$ source venv/bin/activate
$ python3 add-user.py --admin user@example.com
```


Starting the Server
------------------
Starting the server is easy and can pretty much be handled entirely by the `run-server.sh` script. Simply navigate to the natlas-server folder (where this readme is) and `./run-server.sh`. This will start the flask application in your terminal, listening on localhost on port 5000. If you really want, you could change this to listen on a specific IP address on another port, but it is encouraged that you add nginx in front of your flask application.

Furthermore, you might think it's mighty inconvenient that the flask application is running in your terminal and now you can't close the terminal without shutting down the server. You can remediate this with a systemd unit (an example one is provided), or by simply launching the server inside a `screen` session.


NGINX as a Reverse Proxy
------------------
As mentioned above, it is not really advisable to run the flask application directly on the internet (or even on your local network). The flask application is just that, an application. It doesn't account for things like SSL certificates, and modifying application logic to add in potential routes for things like Let's Encrypt should be avoided. Luckily, it's very easy to setup a reverse proxy so that all of this stuff can be handled by a proper web server and leave your application to do exactly what it's supposed to do.

To install nginx, you can simply `sudo apt-get install nginx`. Once it's installed, let's make a copy of provided nginx config:

```
$ sudo cp natlas/natlas-server/deployment/nginx /etc/nginx/sites-available/natlas
```

This nginx config expects that you'll be using TLS for your connections to the server. If you're hosting on the internet, letsencrypt makes this really easy. If you're not, you'll want to remove the TLS redirects. You should really be using a TLS certificate, though, even if it's only self-signed. All communications between both the users and the server, and the agents and the server will happen over this connection.  Go ahead and modify the lines that say `server_name <host>` and change `<host>` to whatever hostname your server will be listening on. Then, in the second server block, you'll want to set the `ssl_certificate` and `ssl_certificate_key` values to point to the correct SSL certificate and key. The final `location /` block is where the reverse proxying actually happens, specifically line `proxy_pass http://127.0.0.1:5000;`. 


Example Systemd Unit
------------------
An example systemd unit file is provided in `deployment/natlas-server.service`. It can be installed by copying it to `/etc/systemd/system/` and reloading the systemctl daemon.

```
$ sudo cp deployment/natlas-server.service /etc/systemd/system/natlas-server.service
$ sudo systemctl daemon-reload
$ sudo systemctl start natlas-server
```
