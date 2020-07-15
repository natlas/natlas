# natlas-server

## Summary

Natlas-server is a flask application that handles browsing and searching natlas scan data, as well as distributing jobs to agents and collecting the results. It also offers an administrative web interface to make changes to scanning scope, exclusions, ports to scan for, and more.

## Backing Services

Backing services in natlas-server are defined via environment configs. They are as follows:

* A SQL Database (SQLite is used if an external Database connection string is not supplied)
* An Elasticsearch 7.x Cluster
* (Optional) A mail server for user account related functionality

## Installation (Production)

Production-ready natlas docker containers are available on dockerhub. The current stable version is `0.6.10`, which uses Elasticsearch 6.x. If you pull from `main` then Elasticsearch 7.x is recommended, as a future version will drop support for ES6.

```bash
docker pull natlas/server:0.6.10
docker run -d -p 5000:5000 --restart=always -v natlas_ns-data:/data:rw -v $(pwd)/natlas_env:/opt/natlas/natlas-server/.env natlas/server:0.6.10
```

The natlas-server depends on the following:

* An `env` file that gets bind mounted to `/opt/natlas/natlas-server/.env`. This is automatically read by the natlas-server config and contains some subset of the values specified in [The Config](#the-config) table below. An [example](#example-ENV) is also provided.
* The `/data` directory which is where, by default, screenshots, logs, and the sqlite config database get stored.
* The `env` file needs to point `ELASTICSEARCH_URL` to the address of an elasticsearch node.

**NOTE:** If you used natlas 0.6.10 or before, you may be used to running a `setup-server.sh` script. This has been removed in favor of the docker workflow. Docker makes the builds much more reliable and significantly easier to support than the janky setup script.

## Installation (Development)

To setup for development, you'll want to fork this repository and then clone it from your fork. See our [contributing guidelines](https://github.com/natlas/natlas/blob/main/CONTRIBUTING.md) for more information.

Development makes use of docker through the `docker-compose.yml` file at the root of the repository. You can modify the desired environment variables and run `docker-compose up -d natlas-server`. You can also run the complete stack by running ` docker-compose up -d `. **This method is only suggested for a development environment.**

## The Config

There are a number of config options that you can specify in the application environment or in a file called `.env` before initializing the database and launching the application. These options break down into two categories: environment configs and web configs. For most installations, the defaults will probably be fine (with the exception of `SECRET_KEY`), however user invitations and password resets won't work without a valid mail server.

### Environment Config

Environment configs are loaded from the environment or a `.env` file and require an application restart to change. Bind mounting a `.env` file to `/opt/natlas/natlas-server/.env` is *highly encouraged* so that passwords are not visible to the entire container.

| Variable | Default | Explanation |
|---|---|---|
| `SECRET_KEY` | Randomly generated | Used for CSRF tokens and sessions. You should generate a unique value for this in `.env`, otherwise sessions will be invalidated whenever the app restarts. |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///metadata.db` | A [SQLALCHEMY URI](https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/) that points to the database to store natlas metadata in |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | A URL that points to the elasticsearch cluster to store natlas scan data in |
| `FLASK_ENV` | `production` | Used to tell flask which environment to run. Only change this if you are debugging or developing, and never leave your server running in anything but `production`.  |
| `FLASK_APP` | `natlas-server.py` | The file name that launches the flask application. This should not be changed as it allows commands like `flask run`, `flask db upgrade`, and `flask shell` to run.|
| `MEDIA_DIRECTORY` | `$BASEDIR/media/` | If you want to store media (screenshots) in a larger mounted storage volume, set this value to an absolute path. If you change this value, be sure to copy the contents of the previous media directory to the new location, otherwise old media will not render.|
| `NATLAS_VERSION_OVERRIDE` | `None` | **Danger**: This can be optionally set for development purposes to override the version string that natlas thinks it's running. Doing this can have adverse affects and should only be done with caution. The only reason to really do this is if you're developing changes to the way host data is stored and presented. |
| `SENTRY_DSN` | `""` | Enables automatic reporting of all Flask exceptions to a [Sentry.io instance](https://sentry.io/). Example: `http://mytoken@mysentry.example.com/1` |
| `SENTRY_JS_DSN` | `""` | Enables automatic reporting of all JS errors to a [Sentry.io instance](https://sentry.io/). This is separate from `SENTRY_DSN` so you can report client-side errors separately from server-side. |
| `OPENCENSUS_ENABLE` | `false` | Enables OpenCensus instrumentation to help identify performance bottlenecks. |
| `OPENCENSUS_SAMPLE_RATE` | `1.0` | Specifies the percentage of requests that are traced with OpenCensus. A number from 0 to 1. |
| `OPENCENSUS_AGENT` | `127.0.0.1:55678` | An OpenCensus agent or collector that this instance will emit traffic to. |
| `MAIL_SERVER` | `None` | Mail server to use for invitations, registrations, and password resets |
| `MAIL_PORT` | `587` | Port that `MAIL_SERVER` is listening on |
| `MAIL_USE_TLS` | `False` | Whether or not to connect to `MAIL_SERVER` with TLS|
| `MAIL_USERNAME` | `None` | Username (if required) to connect to `MAIL_SERVER` |
| `MAIL_PASSWORD` | `None` | Password (if required) to connect to `MAIL_SERVER` |
| `MAIL_FROM` | `None` | Address to be used as the "From" address for outgoing mail. This is required if `MAIL_SERVER` is set. |
| `SERVER_NAME` | `None` | This should be set to the domain and optional port that your service will be accessed on. Do **NOT** include the scheme here. E.g. `example.com` or `10.0.0.15:5000` |
| `PREFERRED_URL_SCHEME` | `https` | You can optionally set this value to `http` if you're not using ssl. This should be avoided for any production environments. |
| `CONSISTENT_SCAN_CYCLE` | `False` | Setting this to `True` will cause the random scan order to persist between scan cycles. This will produce more consistent deltas between an individual host being scanned. **Note**: Changes to the scope will still change the scan order, resulting in one cycle of less consistent timing. |

#### Example ENV

```text
SECRET_KEY=Y91gWepML8Bq1IqDO7MFy9LDbtuPrS3Z9Ge6TX3a
ELASTICSEARCH_URL=http://172.17.0.2:9200
FLASK_ENV=production
MAIL_SERVER=172.17.0.5
MAIL_FROM=noreply@example.com
```

### Web Config

Web configs are loaded from the SQL database and changeable from the web interface without requiring an application restart.

| Variable | Default | Explanation |
|---|---|---|
| `LOGIN_REQUIRED` | `True` | Require login to browse results |
| `REGISTER_ALLOWED` | `False` | Permit open registration for new users |
| `AGENT_AUTHENTICATION` | `True` | Optionally require agents to authenticate before being allowed to get or submit work |
| `CUSTOM_BRAND` | `""` | Custom branding for the navigation bar to help distinguish different natlas installations from one another |

## Setting the Scope

The scope and blacklist can be set server side without using the admin interface by running the `python add-scope.py --scope <file>` script from within the natlas container with the `--scope` and `--blacklist` arguments, respectively. These each take a file name to read scope from, which means you need to put them in a volume that is mounted in your container. You may optionally specify `--verbose` to see exactly which scope items succeeded to import, failed to import, or already existed in the scope. A scope is **REQUIRED** for agents to do any work, however a blacklist is optional.

```bash
$ docker exec -it $(docker ps | grep natlas | cut -d' ' -f1) /bin/bash
root@5dd0d2d6ecdf:/opt/natlas/natlas-server# python add-scope.py --scope /data/bootstrap/myscopefile.txt
root@5dd0d2d6ecdf:/opt/natlas/natlas-server# python add-scope.py --blacklist /data/bootstrap/myblacklistfile.txt
```

## Giving a User Admin Privilege

In order to get started interacting with Natlas, you'll need an administrator account. Admins are allowed to make changes to the following via the web interface:

* application config
* the user list
* scanning scope
* scanning exclusions
* services that agents scan for

You can bootstrap your first admin account using the `add-user.py` script. This script supports creating invitations for users with or without an email address. Whether the user will be invited as an admin or not is handled by the `--admin` flag. If a supplied email already exists in the User table, it will be toggled to be an admin. This can be helpful if you accidentally remove yourself as an admin and can't get back into the admin interface.

**NOTE:** This script **requires** setting the `SERVER_NAME` config option so that links can be generated correctly.

### With Email

If you have a mail server configured, you can specify the email address and the script will automatically send them an invitation email.

```bash
$ docker exec -it $(docker ps | grep natlas-server | cut -d' ' -f1) /bin/bash
root@5dd0d2d6ecdf:/opt/natlas/natlas-server# ./add-user.py --email example@example.com --admin
Sent example@example.com an invitation email via localhost
```

### Without Email

Alternatively, you can create a new user invitation link that can be given to anyone.

```bash
$ docker exec -it $(docker ps | grep natlas-server | cut -d' ' -f1) /bin/bash
root@5dd0d2d6ecdf:/opt/natlas/natlas-server# ./add-user.py --admin
Accept invitation: http://example.com/auth/invite?token=bGhLlBPiOcXos2XrbWiqAzGAO_RMT-mT2VNSLklkXJ0
```

## NGINX as a Reverse Proxy

It is not really advisable to run the flask application directly on the internet (or even on your local network). The flask application is just that, an application. It doesn't account for things like SSL certificates, and modifying application logic to add in potential routes for things like Let's Encrypt should be avoided. Luckily, it's very easy to setup a reverse proxy so that all of this stuff can be handled by a proper web server and leave your application to do exactly what it's supposed to do.

To install nginx, you can simply `sudo apt-get install nginx`. Once it's installed, you can use the provided example config as a starting point:

```bash
sudo curl https://raw.githubusercontent.com/natlas/natlas/main/natlas-server/deployment/nginx > /etc/nginx/sites-available/natlas
```

This nginx config expects that you'll be using TLS for your connections to the server. If you're hosting on the internet, letsencrypt makes this really easy. If you're not, you'll want to remove the TLS redirects. You should really be using a TLS certificate, though, even if it's only self-signed. All communications between both the users and the server, and the agents and the server will happen over this connection.  Go ahead and modify the lines that say `server_name <host>` and change `<host>` to whatever hostname your server will be listening on. Then, in the second server block, you'll want to set the `ssl_certificate` and `ssl_certificate_key` values to point to the correct SSL certificate and key. The final `location /` block is where the reverse proxying actually happens, specifically line `proxy_pass http://127.0.0.1:5000;`.
