# Natlas-agent

## Summary

Natlas-agent is the worker that is responsible for scanning and screenshotting hosts provided by the natlas-server that it is connected to.

## Backing Services

Backing services in natlas-agent are defined via environment configs. They are as follows:

* A natlas-server of the same version as the agent

## Installation (Production)

Production ready docker containers for natlas-agent are available on dockerhub. The current stable version is `0.6.10`.

In order to take screenshots, you'll need to use a custom seccomp profile for the container. This [seccomp profile](https://github.com/jessfraz/dotfiles/blob/master/etc/docker/seccomp/chrome.json) was originally created by [Jess Frazelle](https://github.com/jessfraz) and has been mirrored into the natlas project for posterity.

Before launching your docker container, create an `agent_env` file containing the relevant configurations from [the config table](#the-config).

```bash
wget https://raw.githubusercontent.com/natlas/natlas/main/natlas-agent/chrome.json -O chrome.json
docker pull natlas/agent:0.6.10
docker run -d --restart=always --security-opt seccomp=$(pwd)/chrome.json --cap-add=NET_ADMIN -v $(pwd)/agent_env:/opt/natlas/natlas-agent/.env natlas/agent:0.6.10
```

## Installation (Development)

To setup for development, you'll want to fork this repository and then clone it from your fork. See our [contributing guidelines](https://github.com/natlas/natlas/blob/main/CONTRIBUTING.md) for more information.

Development makes use of docker through the `docker-compose.yml` file at the root of the repository. You can modify the desired environment variables and run `docker-compose up -d natlas-agent`. You can also run the complete stack by running ` docker-compose up -d `. **This method is only suggested for a development environment.**

## The Config

All agent configurations are controlled via environment variables. To make modifications to your agent, you can modify environment variables to match your specifications. These options should be placed in a file called `.env` that gets mounted into your container in `/opt/natlas/natlas-agent/.env`. An [example](#example-ENV) is also provided.

Available options include:

| Variable | Default | Explanation |
|---|---|---|
| `NATLAS_SERVER_ADDRESS` | `http://127.0.0.1:5000` | The server to get work from and submit work to. |
| `NATLAS_IGNORE_SSL_WARN` | `False` | Ignore certificate errors when connecting to `NATLAS_SERVER_ADDRESS` |
| `NATLAS_MAX_THREADS` | `3` | Maximum number of concurrent scanning threads
| `NATLAS_SCAN_LOCAL` | `False` | Don't scan local addresses
| `NATLAS_REQUEST_TIMEOUT` | `15` (seconds) | Time to wait for the server to respond
| `NATLAS_BACKOFF_MAX` | `300` (seconds) | Maximum time for exponential backoff after failed requests
| `NATLAS_BACKOFF_BASE` | `1` (second) | Incremental time for exponential backoff after failed requests
| `NATLAS_MAX_RETRIES` | `10` | Number of times to retry a request to the server before giving up
| `NATLAS_AGENT_ID` | `None` | ID string that identifies scans made by this host, required for agent authentication, optional if agent authentication is not required. Get this from your `/user/` page on the Natlas server if agent authentication is enabled.
| `NATLAS_AGENT_TOKEN` | `None` | Secret token only needed when agent authentication is required. Generate this with the ID on the `/user/` page on the Natlas server.
| `NATLAS_SAVE_FAILS` | `False` | Optionally save scan data that fails to upload for whatever reason.
| `NATLAS_VERSION_OVERRIDE` | `None` | **Danger**: This can be optionally set for development purposes to override the version string that natlas thinks it's running. Doing this can have adverse affects and should only be done with caution. The only reason to really do this is if you're developing changes to the way host data is stored and presented.
| `SENTRY_DSN` | `""` | If set, enables automatic reporting of all exceptions to a [Sentry.io instance](https://sentry.io/). Example: `http://mytoken@mysentry.example.com/1` |

### Example ENV

```text
NATLAS_SERVER_ADDRESS=https://natlas.io
NATLAS_MAX_THREADS=10
NATLAS_AGENT_ID=dade-agent-01
```
