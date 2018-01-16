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
