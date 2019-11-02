![Natlas](https://0xda.de/img/natlas-1000px.png)

[![Release](https://img.shields.io/github/release/natlas/natlas.svg)](https://github.com/natlas/natlas/releases/latest)
![Last Commit](https://img.shields.io/github/last-commit/natlas/natlas.svg)
![Total Downloads](https://img.shields.io/github/downloads/natlas/natlas/total.svg)
![Code Size](https://img.shields.io/github/languages/code-size/natlas/natlas.svg)
[![Contributors](https://img.shields.io/github/contributors/natlas/natlas.svg)](https://github.com/natlas/natlas/graphs/contributors)
[![License](https://img.shields.io/badge/license-Apache%202-blue.svg?style=flat)](LICENSE)
[![Discord](https://img.shields.io/discord/638428906612850709?label=discord)](https://discord.gg/VMbyMMT)

[![Maintainability](https://api.codeclimate.com/v1/badges/321141e5cf7426874cd7/maintainability)](https://codeclimate.com/github/natlas/natlas/maintainability)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/natlas/natlas.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/natlas/natlas/alerts/)

# Summary

You've got a lot of maps and they are getting pretty unruly. What do you do? You put them in a book and call it an atlas. This is like that, except it's a website and it's a collection of nmaps. The Natlas server doubles as a task manager for the agents to get work, allowing you to control the scanning scope in one centralized place.


# Getting Started

To get started with your own deployment of Natlas, you're going to need a minimum of one server and one agent. The quickest way to accomplish this is to run an agent on the same host as the server. Installation instructions for the server and the agent are linked below in their associated readmes.

To begin with natlas:
```
$ cd /opt
$ git clone https://github.com/natlas/natlas.git
$ cd natlas
```

Alternatively, please download the respective tarballs from [natlas/releases](https://github.com/natlas/natlas/releases). 

Once you've got the code in /opt/natlas, please continue to setup either the server, the agent, or both, depending on your use case.


## natlas-server

The natlas-server is where the data gets stored and the web interface exists so that you can search through the data.

You can read more about setting up and running the server on the [natlas-server/README.md](natlas-server/README.md)


## natlas-agent

The natlas-agent is what fetches work from the server and actually performs the scans.

You can read more about setting up and running the agent on the [natlas-agent/README.md](natlas-agent/README.md)

# Contributing
Please review [CONTRIBUTING](CONTRIBUTING.md) for guidelines on how to contribute to natlas.

# Code Of Conduct
This project strives to adhere to the code of conduct outlined in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Please review the code of conduct before contributing.

# Security
Information about this project's security reporting guidelines as well as security related functionality are outlined in [SECURITY.md](SECURITY.md)

# Acknowledgements

* [Pinguino](http://www.pinguinokolb.com/) - Created Natlas logo/branding.
* [Dean Pierce](https://github.com/pierce403) - Created the initial project, nweb, that Natlas was built out of.
* [Topher Timzen](https://github.com/tophertimzen) - Testing, feedback, automation support.
* [Adam Jacques](https://github.com/ajacques) - Helping with Elasticsearch theory and just generally helping improve code quality
* [Ross Snider](https://github.com/rosswsnider) - Writing Cyclic PRNG for target selection
* [Everyone who has contributed.](https://github.com/natlas/natlas/graphs/contributors)

# Disclaimer

Natlas is a platform which makes use of many other open source projects, many of which have their own licenses. Natlas does not claim ownership of any projects that it uses, and does not represent any of said projects. To the best of the Natlas Author's knowledge, the use of these tools in the Natlas platform is not violating any licenses. Natlas is a free and open source project that does not make, nor seeks to make, any revenue from the use of the other open source tools in use.

For further inquiry about licensing, please see the respective projects' licenses.


# License

Copyright 2019 0xdade

Copyright 2016-2018 Intel Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
