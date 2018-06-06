nweb
========

nmap scan collection and search

nweb-server
-------
The nweb-server is where the data gets stored and the web interface exists so that you can search through the data.

You can read more about setting up and running the server on the [nweb-server/README.md](nweb-server/README.md)


nweb-agent
-------
The nweb-agent is what fetches work from the server and actually performs the scans.

You can read more about setting up and running the agent on the [nweb-agent/README.md](nweb-agent/README.md)


[Optional] Masscan
-------

Rather than using nmap to scan randomly, you may be interested in initally using masscan to gather your targets.  The tool **masscan.sh** will run an appropriate masscan scan (make sure **masscan** itself is in your path).  This script will use your existing scope.txt and blacklist.txt to figure out what it should scan.  Additonally there is a **ports.txt**, which tells masscan which ports it should be scanning.  It's currently populated with the nmap top 1000 ports, but that can be changed as desired.

Once the masscan.json file is created, you should be able to run **python massscan-upload.py** to load the masscan data into the elastic server.  When the masscan data is loaded, you'll notice /getwork is now returning port numbers.  This tells the nmap agent to only scan specific ports, so rather than scanning blind, nmap will only scan the specific ports that are open.

At the moment you will probabally want to delete the **masscan_services** and **masscan_hosts** indexes from elastic if you upload any new scan data, otherwise new insertions will be additive, and services that have gone down since the previous scan will not be removed from the list of available targets. To do this you can run the following

```
curl localhost:9200/_cat/indices?v
curl -XDELETE localhost:9200/masscan_services
curl -XDELETE localhost:9200/masscan_hosts
```
