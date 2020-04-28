# natlas-server

## Installing Elasticsearch

Natlas uses Elasticsearch 6.6 to store all of the scan results. If you want to run Elasticsearch locally on your natlas-server, simply run the `./setup-elastic.sh` script.

Alternatively, if you already have an elastic cluster that you'd like to use, you can add it to the `.env` file with the name `ELASTICSEARCH_URL`.


## The Setup

The setup script has been tested on Ubuntu 18.10:

```
$ sudo ./setup-server.sh prod
```

If you would like to run this in docker, you can modify the desired environment variables and run ` docker-compose up -d natlas-server `. You can also run the complete stack by running ` docker-compose up -d `. Note: This method is only suggested for a Development Environment.

Alternatively, you could setup a development environment with the setup-server.sh script. The main difference here is that in development, we don't setup a natlas user, chown the files to natlas:natlas, or do a webpack production build. Later on, this will also include setting up things like linting and testing that are not needed for prod but are for dev.

```
$ sudo ./setup-server.sh dev
```


## The Config

There are a number of config options that you can specify in a file called `.env` before initializing the database and launching the application. These options break down into two categories:

Can't be changed via the web interface (only `.env`):

| Variable | Default | Explanation |
|---|---|---|
| `SECRET_KEY` | `you-should-set-a-secret-key` | Used for CSRF tokens and sessions. The `setup-server.sh` script will generate a random value for you if you don't have an existing `SECRET_KEY` set. |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///metadata.db` | A SQLALCHEMY URI that points to the database to store natlas metadata in |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | A URL that points to the elasticsearch cluster to store natlas scan data in |
| `FLASK_ENV` | `production` | Used to tell flask which environment to run. Only change this if you are debugging or developing, and never leave your server running in anything but `production`.  |
| `FLASK_APP` | `natlas-server.py` | The file name that launches the flask application. This should not be changed as it allows commands like `flask run`, `flask db upgrade`, and `flask shell` to run.|
| `MEDIA_DIRECTORY` | `$BASEDIR/media/` | If you want to store media (screenshots) in a larger mounted storage volume, set this value to an absolute path. If you change this value, be sure to copy the contents of the previous media directory to the new location, otherwise old media will not render.|
| `NATLAS_VERSION_OVERRIDE` | `None` | **Danger**: This can be optionally set for development purposes to override the version string that natlas thinks it's running. Doing this can have adverse affects and should only be done with caution. The only reason to really do this is if you're developing changes to the way host data is stored and presented. |
| `SENTRY_DSN` | `""` | Enables automatic reporting of all exceptions to a [Sentry.io instance](https://sentry.io/). Example: http://mytoken@mysentry.example.com/1 |
| `OPENCENSUS_ENABLE` | `false` | Enables OpenCensus instrumentation to help identify performance bottlenecks. |
| `OPENCENSUS_SAMPLE_RATE` | `1.0` | Specifies the percentage of requests that are traced with OpenCensus. A number from 0 to 1. |
| `OPENCENSUS_AGENT` | `127.0.0.1:55678` | An OpenCensus agent or collector that this instance will emit traffic to. |


Can be changed via the web interface:

| Variable | Default | Explanation |
|---|---|---|
| `LOGIN_REQUIRED` | `False` | Require login to browse results |
| `REGISTER_ALLOWED` | `False` | Permit open registration (requires defined `MAIL_*` settings below) for new users |
| `MAIL_SERVER` | `localhost` | Mail server to use for invitations, registrations, and password resets |
| `MAIL_PORT` | `25` | Port that `MAIL_SERVER` is listening on |
| `MAIL_USE_TLS` | `False` | Whether or not to connect to `MAIL_SERVER` with TLS|
| `MAIL_USERNAME` | `""` | Username (if required) to connect to `MAIL_SERVER` |
| `MAIL_PASSWORD` | `""` | Password (if required) to connect to `MAIL_SERVER` |
| `MAIL_FROM` | `""` | Address to be used as the "From" address for outgoing mail |
| `LOCAL_SUBRESOURCES` | `False` | Use local subresources (js,css,fonts) instead of CDN resources |
| `CUSTOM_BRAND` | `""` | Custom branding for the navigation bar to help distinguish different natlas installations from one another |

For most installations, the defaults will probably be fine (with the exception of `SECRET_KEY`, but this should get generated automatically by `setup-server.sh`), however user invitations won't work without a valid mail server.


## Initializing the Database

The database should be initialized automatically during the `./setup-server` script, but if it is not for whatever reason, this is the manual steps required to intiialize or upgrade the database.

```
$ source venv/bin/activate
$ export FLASK_APP=./natlas-server.py
$ flask db upgrade
$ deactivate
```


## Setting the Scope

The scope and blacklist can be set server side without using the admin interface by running the `./add-scope.py` script from within the natlas `venv` with the `--scope` and `--blacklist` arguments, respectively. These each take a file name to read scope from. You may optionally specify `--verbose` to see exactly which scope items succeeded to import, failed to import, or already existed in the scope. A scope is **REQUIRED** for agents to do any work, however a blacklist is optional.

```
$ source venv/bin/activate
$ python3 add-scope.py --scope myscopefile.txt
$ python3 add-scope.py --blacklist myblacklist.txt
(optional) $ python3 add-scope.py --scope myscopefile.txt --blacklist myblacklist.txt --verbose
```


## Giving a User Admin Privilege

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


## Starting the Server

Starting the server is easy and can pretty much be handled entirely by the `run-server.sh` script. Simply navigate to the natlas-server folder (where this readme is) and `./run-server.sh`. This will start the flask application in your terminal, listening on localhost on port 5000. If you really want, you could change this to listen on a specific IP address on another port, but it is encouraged that you add nginx in front of your flask application.

Furthermore, you might think it's mighty inconvenient that the flask application is running in your terminal and now you can't close the terminal without shutting down the server. You can remediate this with a systemd unit (an example one is provided), or by simply launching the server inside a `screen` session.

When running in development, you will want to run webpack as a development server to monitor for changes to assets.

```
$ yarn run webpack --mode development --watch
```


## NGINX as a Reverse Proxy

As mentioned above, it is not really advisable to run the flask application directly on the internet (or even on your local network). The flask application is just that, an application. It doesn't account for things like SSL certificates, and modifying application logic to add in potential routes for things like Let's Encrypt should be avoided. Luckily, it's very easy to setup a reverse proxy so that all of this stuff can be handled by a proper web server and leave your application to do exactly what it's supposed to do.

To install nginx, you can simply `sudo apt-get install nginx`. Once it's installed, let's make a copy of provided nginx config:

```
$ sudo cp natlas/natlas-server/deployment/nginx /etc/nginx/sites-available/natlas
```

This nginx config expects that you'll be using TLS for your connections to the server. If you're hosting on the internet, letsencrypt makes this really easy. If you're not, you'll want to remove the TLS redirects. You should really be using a TLS certificate, though, even if it's only self-signed. All communications between both the users and the server, and the agents and the server will happen over this connection.  Go ahead and modify the lines that say `server_name <host>` and change `<host>` to whatever hostname your server will be listening on. Then, in the second server block, you'll want to set the `ssl_certificate` and `ssl_certificate_key` values to point to the correct SSL certificate and key. The final `location /` block is where the reverse proxying actually happens, specifically line `proxy_pass http://127.0.0.1:5000;`.


## Example Systemd Unit

An example systemd unit file is provided in `deployment/natlas-server.service`. It can be installed by copying it to `/etc/systemd/system/` and reloading the systemctl daemon.

```
$ sudo cp deployment/natlas-server.service /etc/systemd/system/natlas-server.service
$ sudo systemctl daemon-reload
$ sudo systemctl start natlas-server
```
