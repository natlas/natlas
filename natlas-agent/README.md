# Natlas-agent

The Setup
------------
To get started using the natlas-agent, you should be able to simply run `setup-agent.sh`. This script requires elevated privileges in order to install the necessary packages to run an agent. This script has been tested on Ubuntu 18.04 and Ubuntu 18.10.

```
$ sudo ./setup-agent.sh
```


The Config
------------
To make modifications to your agent, you can modify environment variables to match your specifications. These options can be placed in a file called `.env` in the `natlas-agent` directory. Available options include:

- `NATLAS_SERVER_ADDRESS` defaults to `http://127.0.0.1:5000` - The server to get work from and submit work to.
- `NATLAS_IGNORE_SSL_WARN` defaults to `False` - Ignore certificate errors when connecting to `NATLAS_SERVER_ADDRESS`
- `NATLAS_MAX_THREADS` defaults to `3` - Maximum number of concurrent scanning threads
- `NATLAS_SCAN_LOCAL` defaults to `False` - Don't scan local addresses
- `NATLAS_REQUEST_TIMEOUT` defaults to `15` (seconds) - Time to wait for the server to respond
- `NATLAS_BACKOFF_MAX` defaults to `300` (seconds) - Maximum time for exponential backoff after failed requests
- `NATLAS_BACKOFF_BASE` defaults to `1` (second) - Incremental time for exponential backoff after failed requests
- `NATLAS_MAX_RETRIES` defaults to `10` - Number of times to retry a request to the server before giving up
- `NATLAS_AGENT_ID` defaults to `None` - ID string that identifies scans made by this host, required for agent authentication, optional if agent authentication is not required. Get this from your `/user/` page on the Natlas server if agent authentication is enabled.
- `NATLAS_AGENT_TOKEN` defaults to `None` - Secret token only needed when agent authentication is required. Generate this with the ID on the `/user/` page on the Natlas server.
- `NATLAS_VERSION_OVERRIDE` can be optionally set for development purposes to override the version string that natlas thinks it's running. Doing this can have adverse affects and should only be done with caution. The only reason to really do this is if you're developing changes to the way host data is stored and presented.

Starting the Agent
------------
Once you've gone through the setup and made any necessary changes to the config, starting the agent is very easy:

```
$ source venv/bin/activate
$ sudo python3 natlas-agent.py
```

You may want to run the agent in the background once you've confirmed everything is working. This can be achieved by running the above commands in a screen session, or alternatively (preferably) running it as a system service.

Example Systemd Unit
------------------
An example systemd unit is provided in `deployment/natlas-agent.service`. It can be installed by copying it to `/etc/systemd/system/` and reloading the systemctl daemon.

```
$ sudo cp deployment/natlas-agent.service /etc/systemd/system/natlas-agent.service
$ sudo systemctl daemon-reload
$ sudo systemctl start natlas-agent
```