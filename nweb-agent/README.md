# nweb-agent

The Setup
------------
To get started using the nweb-agent, you should be able to simply run `setup-agent.sh`. Similar to the server, if this script is run with permissions it will try to automatically install the necessary packages, otherwise it will simply check for their existence and alert you if something was missing.

```
$ ./setup-agent.sh
```


The Config
------------
To make modifications to your agent, you can modify `config.py` to match your specifications. Currently, the agent pulls the max number of simultaneous threads to run, the timeout before you should consider a scan as too long and kill it, and the server to fetch work from. The defaults assume that your nweb-server is running on the same host as your nweb-agent, however it's easily changed as you deploy agents to more nodes.


Starting the Agent
------------
Once you've gone through the setup and made any necessary changes to the config, starting the agent is very easy:

```
python3 nweb_agent.py
```


[Optional] Headshotting
------------

The NWeb agent uses the tools **wkhtmltoimage** and **vncsnapshot** to gather "headshots" of servers it scans.  These tools should be available in most package repos, and must be installed for headshotting to work properly.  These tools also require an active X session to work, so you may need to get creative if you are trying to run nweb-agent on a headless server.  I've found that the easiest solution to this problem is to run a VNC server, and you may need to hard code the DISPLAY variable into the getheadshot.py file.

The setup script above will attempt to automatically install these, however you can manually install them like so:

```
$ sudo apt install wkhtmltopdf vncsnapshot
```


Example Systemd Unit
------------------
Below is an example systemd unit you can use to get nweb-agent running in systemd.

```
[Unit]
Description=Nweb Agent
After=network.target
 
[Service]
Type=simple
WorkingDirectory=/opt/nweb/nweb-agent
ExecStart=/usr/bin/python3 /opt/nweb/nweb-agent/nweb_agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```