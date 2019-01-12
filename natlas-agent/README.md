# Natlas-agent

The Setup
------------
To get started using the natlas-agent, you should be able to simply run `setup-agent.sh`. Similar to the server, if this script is run with permissions it will try to automatically install the necessary packages, otherwise it will simply check for their existence and alert you if something was missing.

```
$ ./setup-agent.sh
```


The Config
------------
To make modifications to your agent, you can modify `config.py` to match your specifications. Currently, the agent pulls the max number of simultaneous threads to run, the timeout before you should consider a scan as too long and kill it, and the server to fetch work from. The defaults assume that your natlas-server is running on the same host as your natlas-agent, however it's easily changed as you deploy agents to more nodes.


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
$ sudo apt install chromium-browser
```



[Optional] vncsnapshot
------------

The Natlas agent uses the `vncsnapshot` to gather snapshots of vnc servers it scans.  `vncsnapshot` can be found in most distribution repositories. This tool also requires an active X session to work, so you may need to get creative if you are trying to run natlas-agent on a headless server.  I've found that the easiest solution to this problem is to run a VNC server, and you may need to hard code the DISPLAY variable into the getheadshot.py file.

The setup script above will attempt to automatically install this, however you can manually install them like so:

```
$ sudo apt install vncsnapshot
```


Example Systemd Unit
------------------
Below is an example systemd unit you can use to get natlas-agent running in systemd.

```
[Unit]
Description=Natlas Agent
After=network.target
 
[Service]
Type=simple
WorkingDirectory=/opt/natlas/natlas-agent
ExecStart=/usr/bin/python3 /opt/natlas/natlas-agent/natlas-agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```