Natlas
========
You've got a lot of maps and they are getting pretty unruly. What do you do? You put them in a book and call it an atlas. This is like that, except it's a website and it's a collection of nmaps. Originally forked from [pierce403/nweb](https://github.com/pierce403/nweb).

Getting Started
----------------
To get started with your own deployment of Natlas, you're going to need at one server and at least one agent. The quickest way to accomplish this is to run an agent on the same host as the server. Installation instructions for the server and the agent are linked below in their associated readmes.

To begin with natlas:
```
$ cd /opt
$ git clone https://github.com/natlas/natlas.git
$ cd natlas
```

Once you've got the code in /opt/natlas, please continue to setup either the server, the agent, or both, depending on your use case.


natlas-server
-------------
The natlas-server is where the data gets stored and the web interface exists so that you can search through the data.

You can read more about setting up and running the server on the [natlas-server/README.md](natlas-server/README.md)


natlas-agent
------------
The natlas-agent is what fetches work from the server and actually performs the scans.

You can read more about setting up and running the agent on the [natlas-agent/README.md](natlas-agent/README.md)


License
-------
Copyright 2018 The Natlas Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


