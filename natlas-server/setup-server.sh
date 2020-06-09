#!/bin/bash

export LC_ALL="C.UTF-8"
export LANG="C.UTF-8"
BASEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
SETUP_ENV=""

if [[ "$EUID" -ne 0 ]]; then
	echo "[!] This script needs elevated permissions to run."
	exit 2
fi

case $1 in
	"prod")
		echo "Setting up a production natlas environment"
		SETUP_ENV="prod" ;;
	"dev")
		echo "Setting up a development natlas environment"
		SETUP_ENV="dev" ;;
	*)
		echo "Please specify setup environment: prod or dev"
		exit 3 ;;
esac

if [[ ! -d logs ]]; then
	mkdir logs
fi

echo "[+] Updating apt repositories"
apt-get update >/dev/null

if [ "$SETUP_ENV" == "prod" ]; then
	if ! id -u "natlas" >/dev/null 2>&1; then
		echo "[+] Creating natlas group: groupadd -r natlas"
		groupadd -r natlas
		echo "[+] Creating natlas user: useradd -M -N -r -s /bin/false -d /opt/natlas natlas"
		useradd -M -N -r -s /bin/false -g natlas -d /opt/natlas natlas
		if ! id natlas >/dev/null 2>&1; then
			echo "[!] Failed to create natlas user"
		else
			echo "[+] Successfully created natlas user"
		fi
	else
		echo "[+] Found natlas user"
	fi
fi

ELASTIC=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9200/_nodes)
if [ "$ELASTIC" != "200" ]
then
	ELASTICMSG="[!] Elasticsearch not found on localhost:9200: Make sure you connect natlas to an elasticsearch instance."
	echo "$ELASTICMSG"
else
	echo "[+] Elasticsearch found: http://localhost:9200/_nodes"
fi

if ! which python3 >/dev/null; then
	echo "[+] Installing python3: apt-get -y install python3.6"
	apt-get -y install python3.6
	if ! which python3 >/dev/null; then
		echo "[!] Failed to install python3" && exit 1
	else
		echo "[+] Successfully installed python3: $(which python3)"
	fi
else
	echo "[+] Found python3: $(which python3)"
fi

if ! which node >/dev/null || ! node --version | grep "v12." >/dev/null; then
	echo "[+] Installing dependencies for nodejs: apt-get -y install curl dirmngr apt-transport-https lsb-release ca-certificates"
	apt-get -y install curl dirmngr apt-transport-https lsb-release ca-certificates
	echo "[+] Downloading NodeJS 12.x: curl -sL https://deb.nodesource.com/setup_12.x | bash -"
	curl -sL https://deb.nodesource.com/setup_12.x | bash -
	echo "[+] Installing NodeJS 12.x: apt-get  -y install nodejs"
	apt-get install -y nodejs
	if ! which node >/dev/null; then
		echo "[!] Failed to install nodejs" && exit 1
	else
		echo "[+] Successfully installed nodejs: $(which node)"
		echo "[+] Nodejs version: $(node --version)"
	fi
else
	echo "[+] Found Nodejs: $(which node)"
	echo "[+] Nodejs version: $(node --version)"
fi

if ! which yarn >/dev/null; then
	echo "[+] Fetching yarn gpg key: curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -"
	curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
	echo "[+] Adding yarn repository: echo \"deb https://dl.yarnpkg.com/debian/ stable main\" | tee /etc/apt/sources.list.d/yarn.list"
	echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
	echo "[+] Updating apt repositories"
	apt-get update >/dev/null
	echo "[+] Installing yarn: apt-get -y install yarn"
	apt-get -y install yarn
	if ! which yarn >/dev/null; then
		echo "[!] Failed to install yarn" && exit 1
	else
		echo "[+] Successfully installed yarn: $(which yarn)"
	fi
else
	echo "[+] Found yarn: $(which yarn)"
fi

echo "[+] Installing yarn dependencies"
yarn install --no-progress --frozen-lockfile
if [ "$SETUP_ENV" == "prod" ]; then
	echo "[+] Building assets for production"
	yarn run webpack --mode production
elif [ "$SETUP_ENV" == "dev" ]; then
	echo "[+] Building assets for production"
	yarn run webpack --mode development
fi

if ! which pip3 >/dev/null; then
	echo "[+] Installing pip3: apt-get -y install python3-pip"
	apt-get -y install python3-pip
	if ! which pip3 >/dev/null; then
		echo "[!] Failed to install pip3" && exit 2
	else
		echo "[+] Successfully installed python3: $(which pip3)"
	fi
else
	echo "[+] Found pip3: $(which pip3)"
fi

if ! which virtualenv >/dev/null; then
	echo "[!] Installing virtualenv: apt-get -y install virtualenv"
	apt-get -y install virtualenv
	if ! which virtualenv >/dev/null; then
		echo "[!] Failed to install virtualenv" && exit 3
	else
		echo "[+] Successfully installed virtualenv: $(which virtualenv)"
	fi
else
	echo "[+] Found virtualenv: $(which virtualenv)"
fi

if [ ! -d venv ]; then
	echo "[+] Creating new python3 virtualenv named venv"
	virtualenv -p /usr/bin/python3 venv
	if [ ! -d venv ]; then
		echo "[!] Failed to create virtualenv named venv" && exit 4
	else
		echo "[+] Successfully created virtualenv named venv"
	fi
else
	echo "[+] Found virtualenv named venv"
fi

if [ ! -e venv/bin/activate ]; then
	echo "[!] No venv activate script found: venv/bin/activate" && exit 5
else
	echo "[+] Entering virtual environment"
	# shellcheck disable=SC1091
	source venv/bin/activate
	echo "[+] Installing/updating natlas-server python dependencies"
	pip3 --disable-pip-version-check install -r requirements.txt --log pip.log -q
	echo "[+] Initializing/upgrading metadata database"
	if ! grep "FLASK_APP" .env >/dev/null 2>&1; then
		echo "FLASK_APP=natlas-server.py" >> .env
	fi

	if ! grep "SECRET_KEY" .env >/dev/null 2>&1; then
		if [ ! -z "$SECRET_KEY" ]; then
			echo "SECRET_KEY=$SECRET_KEY" >> .env
			echo "[+] Copying \$SECRET_KEY to .env"
		else
			echo "SECRET_KEY=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 32 | head -n 1)" >> .env
			echo "[+] Generating random SECRET_KEY"
		fi
	fi

	flask db upgrade
	echo "[+] Exiting virtual environment"
	deactivate
fi

if [ "$SETUP_ENV" == "prod" ]; then
	echo "[+] Giving natlas user ownership of all project files"
	chown -R natlas:natlas "$BASEDIR"
elif [ "$SETUP_ENV" == "dev" ]; then
	echo "[+] Giving current user ownership of all project files"
	if [ ! -z "$SUDO_USER" ]; then
		chown -R "$SUDO_USER":"$SUDO_USER" "$BASEDIR"
	fi
fi

echo "[+] Setup Complete"
echo "------------------"
if [ ! -z "${ELASTICMSG+x}" ]; then
	echo "$ELASTICMSG"
fi
echo "[+] An example systemd script can be found in deployment/natlas-server.service"
echo "[+] An example nginx config can be found in deployment/nginx"
echo "[+] We highly recommend you use nginx to proxy connections to the flask application."
