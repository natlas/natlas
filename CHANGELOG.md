# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project (roughly) adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added
* Branding improvements
* Version is now visible in the server footer
* Back-to-top button
* Server doesn't interact with mismatched versions

### Changed
* Style improvements
* Communication between agent and server has been more standardized around json messaging

### Fixed
* Agent standalone mode got broken with the agent configurations, fixed the standalone default scanning options

## [v0.6.1] - Bugfixes
More information can be found at [natlas/v0.6.1](https://github.com/natlas/natlas/releases/tag/v0.6.1)

### Fixed
* /api/natlas-services no longer breaks the admin page
* Extraneous debugging print statements removed


## [v0.6.0] - Structured data, better config, agent authn
More information can be found at [natlas/v0.6.0](https://github.com/natlas/natlas/releases/tag/v0.6.0)

### Added
* Server/Agent authentication using agent ID and secret
* Servers can assign tags to scope ranges
* Logged in users can request hosts to be rescanned, which puts them in a priority work queue
* XML parsing of nmap data to provide some structured elasticsearch data
* JSON export for scan results
* Agents can optionally ignore SSL validation warnings
* Agents can give themselves a maximum retry target before giving up a submit call to the server

### Changed
* jQuery and Bootstrap have been significantly upgraded to more modern versions
* Server setup script generates new random secret key if one doesn't already exist
* Move away from raw data view and into using the structured data
* Agents now report back to the server regardless if the host is up or not, which allows us to better track how many times we're actually scanning hosts.
* Tabled data now appears in DataTables, which allow for sorting, searching, and pagination

### Fixed
* Agents properly clean up scan data that were inadvertently left around when scans timeout
* Agents no longer request extra work for their local queue, resulting in extra data loss when agents are stopped
* Tons of HTML errors were corrected

## [v0.5.4] - Server stability improvements
More information can be found at [natlas/v0.5.4](https://github.com/natlas/natlas/releases/tag/v0.5.4)

### Fixed
* Setup-elastic now enables the elasticsearch systemd unit so that it survives reboots


## [v0.5.3] - Server setup improvements
More information can be found at [natlas/v0.5.3](https://github.com/natlas/natlas/releases/tag/v0.5.3)

### Changed
* Setup-server uses apt to install virtualenv instead of pip3

## [v0.5.2] - Server setup improvements
More information can be found at [natlas/v0.5.2](https://github.com/natlas/natlas/releases/tag/v0.5.2)

### Fixed
* Setup-server handles user creation correctly now

### Changed
* Setup-server changes ownership of the files to not be owned by root once finished setting up. 

## [v0.5.1] - Agent bugfix, Responsive Views
More information can be found at [natlas/v0.5.1](https://github.com/natlas/natlas/releases/tag/v0.5.1)

### Changes
* Server has more responsive views

### Fixed
* Agent environment variables parse correctly now after correcting type casting


## [v0.5.0] - Initial Release
More Info can be found at [natlas/v0.5.0](https://github.com/natlas/natlas/releases/tag/v0.5.0)

### Server Added
* Automatic setup via setup scripts
* Server-side scripts for various management and bootstrap tasks
* Server-defined service database
* Server-defined agent config options
* Basic User-access controls
* Web service front end
* API agent access
* Example systemd and nginx deployment files

### Agent Added
* Use of nmap for port scans
* Headless web screenshots with [aquatone](https://github.com/michenriksen/aquatone)
* Headless VNC screenshots with vncsnapshot
* Configuration via .env file
* Ability to run in standalone mode