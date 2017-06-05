nweb
========

nmap scan collection and search

Getting Started
---------------

Most people will be able to just do:

```
$ git clone https://github.com/pierce403/nweb.git
$ cd nweb
$ ./run-flask.sh
```
This starts the nweb server on port 5000.  Then, in a new terminal, edit scope.txt to point to the desired targets, and run:
```
python3 nmap-agent.py
```
This will start the scans, and you will soon be able to see the results in the web interface by browsing to http://127.0.0.1:5000
