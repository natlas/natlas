![Natlas](https://0xda.de/img/natlas-1000px.png)

![Last Commit](https://img.shields.io/github/last-commit/natlas/natlas.svg)
[![Release](https://img.shields.io/github/release/natlas/natlas.svg)](https://github.com/natlas/natlas/releases/latest)
[![Contributors](https://img.shields.io/github/contributors/natlas/natlas.svg)](https://github.com/natlas/natlas/graphs/contributors)
[![License](https://img.shields.io/badge/license-Apache%202-blue.svg?style=flat)](LICENSE)

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

[![Server downloads](https://img.shields.io/docker/pulls/natlas/server?label=server%20downloads&logo=docker)](https://hub.docker.com/repository/docker/natlas/server)
[![Agent downloads](https://img.shields.io/docker/pulls/natlas/agent?label=agent%20downloads&logo=docker)](https://hub.docker.com/repository/docker/natlas/agent)

# Summary

You've got a lot of maps and they are getting pretty unruly. What do you do? You put them in a book and call it an atlas. This is like that, except it's a website and it's a collection of nmaps. Natlas' objective is to make it easy to perform continuous scanning and review collected data.

The goal of Natlas is not to identify a bunch of vulnerabilities, necessarily, but rather to identify exposure. Perhaps you want to make sure that no one is running ssh with password auth enabled. Or perhaps you want to look for any exposed nfs, smb, or rsync shares. Maybe you want to look for expiring or expired ssl certificates, or weak ssl ciphers being used. Since Natlas uses the popular [nmap](https://nmap.org) port scanner, you can easily use any default nmap scripts in your scans.

# Getting Started

To get started with your own deployment of Natlas, you're going to need a minimum of one elasticsearch node, one Natlas server and one Natlas agent. The quickest way to accomplish this is to run all three of these containers on the same server. Installation instructions for the server and the agent are linked below in their associated readmes.

The required deployment order is as follows:

1) [Elasticsearch](#Elasticsearch)
2) [Natlas Server](#Natlas-server)
3) [Natlas Agent(s)](#Natlas-agent)

**Note:** As of June 15, 2020, Natlas has moved to a docker-only deployment model.

## Elasticsearch

Because the Natlas server requires a connection to Elasticsearch in order to launch correctly, you should make sure you have an Elasticsearch node available before continuing with the next step. If you've never used Elasticsearch before, follow [Elastic's instructions](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html) for setting up a single node cluster with docker. Make sure to pay attention to the section on persisting the elastic data.

## Natlas Server

The Natlas server controls agent orchestration, scan configuration, and provides search and browse for the data stored in Elastic.

See the [Natlas Server README](natlas-server#installation-production) for instructions on installing the Natlas server.

## Natlas Agent

The Natlas agent is what fetches work from the server and actually performs the scans.

See the [Natlas Agent README](natlas-agent#installation-production) for instructions on installing the Natlas agent.

# Contributing

Please review our [contribution guidelines](CONTRIBUTING.md) for information on how to contribute to Natlas. To get started with development, please see [Project Setup](CONTRIBUTING.md#project-setup).

# Code Of Conduct

This project strives to adhere to the code of conduct outlined in our [code of conduct](CODE_OF_CONDUCT.md). Please review the code of conduct before contributing.

# Security

Information about this project's security reporting guidelines as well as security related functionality are outlined in our [Security guidelines](SECURITY.md).

# Acknowledgements

* [Pinguino](http://www.pinguinokolb.com/) - Created Natlas logo/branding.
* [Dean Pierce](https://github.com/pierce403) - Created the initial project, nweb, that Natlas was built out of.
* [Topher Timzen](https://github.com/tophertimzen) - Testing, feedback, automation support.
* [Adam Jacques](https://github.com/ajacques) - Helping with Elasticsearch theory and just generally helping improve code quality
* [Ross Snider](https://github.com/rosswsnider) - Writing Cyclic PRNG for target selection
* [Everyone who has contributed](https://github.com/natlas/natlas/graphs/contributors)

# Disclaimer

Natlas is a platform which makes use of many other open source projects, many of which have their own licenses. Natlas does not claim ownership of any projects that it uses, and does not represent any of said projects. To the best of the Natlas Author's knowledge, the use of these tools in the Natlas platform is not violating any licenses. Natlas is a free and open source project that does not make, nor seeks to make, any revenue from the use of the other open source tools in use.

For further inquiry about licensing, please see the respective projects' licenses.

# License

```text
Copyright 2020 0xdade
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
```
