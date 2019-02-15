# Natlas-agent

The Setup
------------
To get started using the natlas-agent, you should be able to simply run `setup-agent.sh`. This script requires elevated privileges in order to install the necessary packages to run an agent. This script has been tested on Ubuntu 18.10.

```
$ sudo ./setup-agent.sh
```


The Config
------------
To make modifications to your agent, you can modify environment variables to match your specifications. Available options include:

- `NATLAS_SERVER_ADDRESS` defaults to `http://127.0.0.1:5000` - The server to get work from and submit work to.
- `NATLAS_MAX_THREADS` defaults to `3` - Maximum number of concurrent scanning threads
- `NATLAS_SCAN_LOCAL` defaults to `False` - Don't scan local addresses
- `NATLAS_REQUEST_TIMEOUT` defaults to `15` (seconds) - Time to wait for the server to respond
- `NATLAS_BACKOFF_MAX` defaults to `300` (seconds) - Maximum time for exponential backoff after failed requests
- `NATLAS_BACKOFF_BASE` defaults to `1` (second) - Incremental time for exponential backoff after failed requests

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