# Natlas-agent

The Setup
------------
To get started using the natlas-agent, you should be able to simply run `setup-agent.sh`. Similar to the server, if this script is run with permissions it will try to automatically install the necessary packages, otherwise it will simply check for their existence and alert you if something was missing.

```
$ ./setup-agent.sh
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
python3 natlas-agent.py
```


[Optional] Aquatone
------------

The Natlas agent now supports the use of Aquatone if it's available. Aquatone relies on Chrome or Chromium. [More information about installing aquatone](https://github.com/michenriksen/aquatone#installation).

The setup script will check for the existence of chromium-browser and try to install it if you're running as root, however you can manually install it like so:

```
$ sudo apt install -y chromium-browser
```



[Optional] vncsnapshot
------------

The Natlas agent uses the `vncsnapshot` to gather snapshots of vnc servers it scans.  `vncsnapshot` can be found in most distribution repositories. In order to use vncsnapshot in a headless environment, we're going to take advantage of `xvfb-run`. 

The setup script above will attempt to automatically install this, however you can manually install them like so:

```
$ sudo apt install -y xvfb-run vncsnapshot
```


Example Systemd Unit
------------------
An example systemd unit is provided in `deployment/natlas-agent.service`