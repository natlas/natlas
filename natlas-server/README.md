# Natlas Server

The Natlas server is a flask application that handles browsing and searching Natlas scan data, as well as distributing jobs to agents and collecting the results. It also offers an administrative web interface to make changes to scanning scope, exclusions, ports to scan for, and more.

## Backing Services

Backing services in the Natlas server are defined via environment configs. They are as follows:

* A SQL Database (SQLite is used if an external Database connection string is not supplied)
* An Elasticsearch 7.x Cluster
* (Optional) A mail server for user account related functionality

## Installation (Production)

Production-ready Natlas docker containers are [available on dockerhub](https://hub.docker.com/r/natlas/server).

Before you launch your Natlas server, ensure that you've already setup an [Elasticsearch](/README.md#Elasticsearch) cluster that your container will be able to reach. You'll then need to create your environment config file to mount into your container. Finally, choose whether you want to store media on the local filesystem in a mounted directory or if you want to use a docker volume. For simplicity, I'll be using a local filesystem mount.

### Example ENV

The following is an example ENV file that assumes your elasticsearch cluster is accessible at `172.17.0.2:9200` and that your mail server is accessible with authentication at `172.17.0.4`. If you do not have a mail server, remove `MAIL_` settings. A complete list of configuration options is [available below](#the-config).

```bash
#####
# Flask Settings
#####
SECRET_KEY=im-a-really-long-secret-please-dont-share-me
FLASK_ENV=production

#####
# Data Stores
#####
ELASTICSEARCH_URL=http://172.17.0.2:9200

# A mysql database via the mysqlclient driver
#SQLALCHEMY_DATABASE_URI=mysql://natlas:password@172.18.0.5/natlas

# A sqlite database with a custom name vs the default metadata.db
#SQLALCHEMY_DATABASE_URI=sqlite:////data/db/test.db

#####
# Mail settings
#####
MAIL_SERVER=172.17.0.4
MAIL_USERNAME=dade.murphy
MAIL_PASSWORD=this-is-an-invalid-password
MAIL_FROM=noreply@example.com

#####
# Natlas Specific Settings
#####
CONSISTENT_SCAN_CYCLE=True
DB_AUTO_MIGRATE=True
```

### Launching Natlas Server

```bash
docker pull natlas/server
docker run -d -p 5000:5000 --name natlas_server --restart=always -v /mnt/natlas_data:/data:rw -v /path/to/your/natlas_env:/opt/natlas/natlas-server/.env natlas/server
```

The Natlas server depends on the following:

* An `env` file that gets bind mounted to `/opt/natlas/natlas-server/.env`. This is automatically read by the natlas-server config and contains some subset of the values specified in [The Config](#the-config) table below. An [example](#example-ENV) is also provided.
* The `/data` directory which is where, by default, screenshots and the sqlite config database get stored.
* The `env` file needs to point `ELASTICSEARCH_URL` to the address of an elasticsearch node.

**NOTE:** If you used Natlas 0.6.10 or before, you may be used to running a `setup-server.sh` script. This has been removed in favor of the docker workflow. Docker makes the builds much more reliable and significantly easier to support than the janky setup script.

## Installation (Development)

To setup for development, you'll want to fork this repository and then clone it from your fork. See our [contributing guidelines](/CONTRIBUTING.md) for more information.

Development makes use of docker through the `docker-compose.yml` file at the root of the repository. You can modify the desired environment variables and run `docker-compose up -d natlas-server`. You can also run the complete stack by running ` docker-compose up -d `. **This method should ONLY be used for a development environment.**

## The Config

There are a number of config options that you can specify in the application environment or in a file called `.env` before initializing the database and launching the application. These options break down into two categories: environment configs and web configs.

### Environment Config

Environment configs are loaded from the environment or a `.env` file and require an application restart to change. Bind mounting a `.env` file to `/opt/natlas/natlas-server/.env` (rather than providing it as a docker env file) is *highly encouraged* so that passwords are not visible to the entire container.

| Variable | Default | Explanation |
|---|---|---|
| `SECRET_KEY` | Randomly generated | Used for CSRF tokens and sessions. You should generate a unique value for this in `.env`, otherwise sessions will be invalidated whenever the app restarts. |
| `DATA_DIR` | `/data` | Path to store any data that should be persisted. Sqlite database, any log files, and media files all go in subdirectories of this directory. |
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///$DATA_DIR/db/metadata.db` | A [SQLALCHEMY URI](https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/) that points to the database to store natlas metadata in. Supported types by natlas-server are: `sqlite:`, `mysql:` |
| `DB_AUTO_MIGRATE` | `False` | Automatically perform necessary data migrations when upgrading to a new version of natlas. Not recommended for multi-node deployments. |
| `ELASTICSEARCH_URL` | `http://localhost:9200` | A URL that points to the elasticsearch cluster to store natlas scan data in |
| `FLASK_ENV` | `production` | Used to tell flask which environment to run. Only change this if you are debugging or developing, and never leave your server running in anything but `production`.  |
| `FLASK_APP` | `natlas-server.py` | The file name that launches the flask application. This should not be changed as it allows commands like `flask run`, `flask db upgrade`, and `flask shell` to run.|
| `MEDIA_DIRECTORY` | `$DATA_DIR/media/` | If you want to store media (screenshots) in a larger mounted storage volume, set this value to an absolute path. If you change this value, be sure to copy the contents of the previous media directory to the new location, otherwise old media will not render.|
| `NATLAS_VERSION_OVERRIDE` | `None` | **Danger**: This can be optionally set for development purposes to override the version string that natlas thinks it's running. Doing this can have adverse affects and should only be done with caution. The only reason to really do this is if you're developing changes to the way host data is stored and presented. |
| `SENTRY_DSN` | `""` | Enables automatic reporting of all Flask exceptions to a [Sentry.io instance](https://sentry.io/). Example: `http://mytoken@mysentry.example.com/1` |
| `SENTRY_ENVIRONMENT` | `None` | Specifies the value to provided for the `environment` tag in Sentry. Use it to differentiate between different stages or stacks. e.g. `Beta` or `Prod` |
| `SENTRY_JS_DSN` | `""` | Enables automatic reporting of all JS errors to a [Sentry.io instance](https://sentry.io/). This is separate from `SENTRY_DSN` so you can report client-side errors separately from server-side. |
| `OPENCENSUS_ENABLE` | `false` | Enables OpenCensus instrumentation to help identify performance bottlenecks. |
| `OPENCENSUS_SAMPLE_RATE` | `1.0` | Specifies the percentage of requests that are traced with OpenCensus. A number from 0 to 1. |
| `OPENCENSUS_AGENT` | `127.0.0.1:55678` | An OpenCensus agent or collector that this instance will emit traffic to. |
| `MAIL_SERVER` | `None` | Mail server to use for invitations, registrations, and password resets |
| `MAIL_PORT` | `587` | Port that `MAIL_SERVER` is listening on |
| `MAIL_USE_TLS` | `True` | Whether or not to connect to `MAIL_SERVER` with STARTTLS |
| `MAIL_USE_SSL` | `False` | Whether or not to connect to `MAIL_SERVER` with SSL (E.g. Port 465) |
| `MAIL_USERNAME` | `None` | Username (if required) to connect to `MAIL_SERVER` |
| `MAIL_PASSWORD` | `None` | Password (if required) to connect to `MAIL_SERVER` |
| `MAIL_FROM` | `None` | Address to be used as the "From" address for outgoing mail. This is required if `MAIL_SERVER` is set. |
| `SERVER_NAME` | `None` | This should be set to the domain and optional port that your service will be accessed on. Do **NOT** include the scheme here. E.g. `example.com` or `10.0.0.15:5000` |
| `PREFERRED_URL_SCHEME` | `https` | You can optionally set this value to `http` if you're not using ssl. This should be avoided for any production environments. |
| `CONSISTENT_SCAN_CYCLE` | `False` | Setting this to `True` will cause the random scan order to persist between scan cycles. This will produce more consistent deltas between an individual host being scanned. **Note**: Changes to the scope will still change the scan order, resulting in one cycle of less consistent timing. |

### Web Config

Web configs are loaded from the SQL database and changeable from the web interface without requiring an application restart.

| Variable | Default | Explanation |
|---|---|---|
| `LOGIN_REQUIRED` | `True` | Require login to browse results |
| `REGISTER_ALLOWED` | `False` | Permit open registration for new users |
| `AGENT_AUTHENTICATION` | `True` | Optionally require agents to authenticate before being allowed to get or submit work |
| `CUSTOM_BRAND` | `""` | Custom branding for the navigation bar to help distinguish different natlas installations from one another |

## Setting the Scope

The scope and blacklist can be set server side without using the admin interface by running the `flask scope import` command from within the natlas container with the `--scope` and `--blacklist` arguments, respectively. If neither option is supplied, `--scope` is assumed.

You may optionally specify `--verbose` to see exactly which scope items succeeded to import, failed to import, or already existed in the database. If you're importing a lot of items, it is recommended that you redirect the results to a file.

```bash
docker exec -it $(docker ps | grep natlas/server | cut -d' ' -f1) flask scope import --verbose /data/bootstrap/myscopefile.txt > /data/bootstrap/import_results.json
```

A scope is **REQUIRED** for agents to do any work, however a blacklist is optional.

## Creating Your First User

In order to get started interacting with Natlas, you'll need an administrator account. Admins are allowed to make changes to the following via the web interface:

* application config
* the user list
* scanning scope
* scanning exclusions
* services that agents scan for

You can bootstrap your first admin account using the `flask user new` command. This command supports creating invitations for users with or without an email address. Whether the user will be invited as an admin or not is handled by the `--admin` flag.

**NOTE:** This script **requires** the `SERVER_NAME` environment option so that links can be generated correctly. This should be set to whatever you want the link to generate with(e.g. `SERVER_NAME=localhost:5000` will generate `https://localhost:5000/auth/invite?token=this-is-an-invalid-example-token`)

### With Email

If you have a mail server configured, you can specify the email address and the script will automatically send them an invitation email.

```bash
$ docker exec -e SERVER_NAME=example.com -it $(docker ps | grep natlas/server | cut -d' ' -f1) flask user new --email example@example.com --admin
Email sent to example@example.com via localhost
```

### Without Email

Alternatively, you can create a new user invitation link that can be given to anyone.

```bash
$ docker exec -e SERVER_NAME=example.com -it $(docker ps | grep natlas/server | cut -d' ' -f1) flask user new --admin
Accept invitation: http://example.com/auth/invite?token=this-is-an-invalid-example-token
```

## NGINX as a Reverse Proxy

It is not really advisable to run the flask application directly on the internet (or even on your local network). The flask application is just that, an application. It doesn't account for things like SSL certificates, and modifying application logic to add in potential routes for things like Let's Encrypt should be avoided. Luckily, it's very easy to setup a reverse proxy so that all of this stuff can be handled by a proper web server and leave your application to do exactly what it's supposed to do.

We provide an example nginx configuration file, however you should familiarize yourself with how to use and secure nginx.

1. [Installing Nginx](https://docs.nginx.com/nginx/admin-guide/installing-nginx/installing-nginx-open-source/)
2. [Nginx Reverse Proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
3. [Using Certbot with Nginx](https://certbot.eff.org/lets-encrypt/ubuntufocal-nginx)
4. [Nginx Security Controls](https://docs.nginx.com/nginx/admin-guide/security-controls/)
5. [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)

You can grab our example config to help get started:

```bash
sudo curl https://raw.githubusercontent.com/natlas/natlas/main/natlas-server/deployment/nginx > /etc/nginx/sites-available/natlas
```

## Security

For more information about the security of the Natlas server, or to report a vulnerability, please see the [Security Policy](/SECURITY.md)
