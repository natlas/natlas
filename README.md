nweb
========

nmap scan collection and search

Installing Elasticsearch
------------------------

NWeb now default to using elasticsearch for the backend.  Download the latest here:

https://www.elastic.co/downloads/elasticsearch

```
$ sudo apt-get install default-jre
$ sudo dpkg -i elasticsearch-XXXXXX.deb
$ sudo /etc/init.d/elasticsearch start
```

Running the Server
------------------

Most people will be able to just do:

```
$ apt-get install virtualenv python3-pip
$ git clone https://github.com/pierce403/nweb.git
$ cd nweb
$ ./run-server.sh
```
This starts the nweb server on port 5000.  Then, in a new terminal, edit scope.txt to point to the desired targets, and run:
```
python3 nweb_agent.py
```
This will start the scans, and you will soon be able to see the results in the web interface by browsing to http://127.0.0.1:5000


Headshotting
------------

The NWeb agent uses the tools **wkhtmltoimage** and **vncsnapshot** to gather "headshots" of servers it scans.  These tools should be available in most package repos, and must be installed seperately for headshotting to work properly.  These tools also require an active X session to work, so you may need to get creative if you are trying to run NWeb on a headless server.  I've found that the easiest solution to this problem is to run a VNC server, and you may need to hard code the DISPLAY variable into the getheadshot.py file.


Masscan
-------

Rather than using nmap to scan randomly, you may be interested in initally using masscan to gather your targets.  The tool **masscan.sh** will run an appropriate masscan scan (make sure **masscan** itself is in your path).  This script will use your existing scope.txt and blacklist.txt to figure out what it should scan.  Additonally there is a **ports.txt**, which tells masscan which ports it should be scanning.  It's currently populated with the nmap top 1000 ports, but that can be changed as desired.

Once the masscan.json file is created, you should be able to run **python massscan-upload.py** to load the masscan data into the elastic server.  When the masscan data is loaded, you'll notice /getwork is now returning port numbers.  This tells the nmap agent to only scan specific ports, so rather than scanning blind, nmap will only scan the specific ports that are open.

At the moment you will probabally want to delete the **masscan_services** and **masscan_hosts** indexes from elastic if you upload any new scan data, otherwise new insertions will be additive, and services that have gone down since the previous scan will not be removed from the list of available targets. To do this you can run the following

```
curl localhost:9200/_cat/indices?v
curl -XDELETE localhost:9200/masscan_services
curl -XDELETE localhost:9200/masscan_hosts
```
