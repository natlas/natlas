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

Installing Dependencies
------------------

```
$ apt-get install wkhtmltopdf vncsnapshot
```

Running the Server
------------------

Most people will be able to just do:

```
$ apt-get install virtualenv python3-pip
$ git clone https://github.com/pierce403/nweb.git
$ cd nweb
$ ./run-flask.sh
```
This starts the nweb server on port 5000.  Then, in a new terminal, edit scope.txt to point to the desired targets, and run:
```
python3 nmap-agent.py
```
This will start the scans, and you will soon be able to see the results in the web interface by browsing to http://127.0.0.1:5000


Headshotting
------------

The NWeb agent uses the tools **wkhtmltoimage** and **vncsnapshot** to gather "headshots" of servers it scans.  These tools should be available in most package repos, and must be installed seperately for headshotting to work properly.  These tools also require an active X session to work, so you may need to get creative if you are trying to run NWeb on a headless server.  I've found that the easiest solution to this problem is to run a VNC server, and you may need to hard code the DISPLAY variable into the getheadshot.py file.
