# Natlas Agent

The Natlas agent is responsible for collecting all of the information for the Natlas platform. It uses [nmap](https://nmap.org) to do port scans that are configured by the Natlas server, [aquatone](https://github.com/michenriksen/aquatone) to take web screenshots of any http ports, and [vncsnapshot](http://vncsnapshot.sourceforge.net/) to take screenshots of VNC servers. Once it's done scanning a target, it submits that data back to the server and then requests another target to scan.

## Backing Services

Backing services in the Natlas agent are defined via environment configs. They are as follows:

* A Natlas server of the same version as the agent

## Installation (Production)

Production ready docker containers for the Natlas agent are [available on dockerhub](https://hub.docker.com/r/natlas/agent).

In order to take screenshots, you'll need to use a custom seccomp profile for the container. This [seccomp profile](https://github.com/jessfraz/dotfiles/blob/master/etc/docker/seccomp/chrome.json) was originally created by [Jess Frazelle](https://github.com/jessfraz) and has been mirrored into the Natlas project for posterity.

Before launching your docker container, create an `agent_env` file containing the relevant configurations from [the config table](#the-config).

### Example ENV

At minimum, you'll want to define these configuration options. Get `NATLAS_AGENT_ID` and `NATLAS_AGENT_TOKEN` from the `/user/` profile page of your Natlas server.

```bash
mkdir /opt/natlas
echo "NATLAS_SERVER_ADDRESS=https://natlas.io" >> /opt/natlas/agent_env
echo "NATLAS_MAX_THREADS=25" >> /opt/natlas/agent_env
echo "NATLAS_AGENT_ID=this-is-example-id" >> /opt/natlas/agent_env
echo "NATLAS_AGENT_TOKEN=this-is-obviously-an-example-token" >> /opt/natlas/agent_env
```

### Grabbing the Chrome Seccomp Profile

```bash
wget https://raw.githubusercontent.com/natlas/natlas/main/natlas-agent/chrome.json -O /opt/natlas/chrome.json
```

### Launching the agent

Assuming you created files in the locations in the previous step, you can use these docker commands to download and launch the agent.

```bash
docker pull natlas/agent
docker run -d --name natlas_agent --restart=always --security-opt seccomp=/opt/natlas/chrome.json --cap-add=NET_ADMIN -v /opt/natlas/agent_env:/opt/natlas/natlas-agent/.env natlas/agent
```

## Installation (Development)

To setup for development, you'll want to fork this repository and then clone it from your fork. See our [contributing guidelines](/CONTRIBUTING.md) for more information.

Development makes use of docker through the `docker-compose.yml` file at the root of the repository. You can modify the desired environment variables and run `docker-compose up -d natlas-agent`. You can also run the complete stack by running ` docker-compose up -d `. **This method should ONLY be used for a development environment.**

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
| `NATLAS_AGENT_TOKEN` | `None` | Secret token needed when agent authentication is required. Generate this with the ID on the `/user/` page on the Natlas server.
| `NATLAS_SAVE_FAILS` | `False` | Optionally save scan data that fails to upload for whatever reason.
| `NATLAS_VERSION_OVERRIDE` | `None` | **Danger**: This can be optionally set for development purposes to override the version string that natlas thinks it's running. Doing this can have adverse affects and should only be done with caution. The only reason to really do this is if you're developing changes to the way host data is stored and presented.
| `SENTRY_DSN` | `""` | If set, enables automatic reporting of all exceptions to a [Sentry.io instance](https://sentry.io/). Example: `http://mytoken@mysentry.example.com/1` |

## Security

For more information about the security of the Natlas agent, or to report a vulnerability, please see the [Security Policy](/SECURITY.md)
