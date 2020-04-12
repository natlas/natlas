#!/bin/bash
# sudo bash setup-agent.sh

AQUATONEURL='https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip'

if [[ "$EUID" -ne 0 ]]; then
	echo "[!] This script needs elevated permissions to run."
	exit 2
fi

echo "[+] Updating apt repositories"
apt-get update


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
	echo "[!] Installing virtualenv: pip3 install virtualenv"
	pip3 install virtualenv
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
	echo "[+] Installing/upgrading natlas-agent python dependencies"
	pip3 install -r requirements.txt --log pip.log -q
	echo "[+] Exiting virtual environment"
	deactivate
fi

if ! which nmap >/dev/null; then
	echo '[+] Installing nmap: apt-get install -y nmap'
	apt-get install -y nmap
	if ! which nmap >/dev/null; then
		echo "[!] Failed to install nmap" && exit 6
	else
		echo "[+] Successfully installed nmap: $(which nmap)"
	fi
else
	echo "[+] Found nmap: $(which nmap)"
fi

echo "[+] Setting capabilities for nmap"
if ! setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip $(which nmap) >/dev/null 2>&1; then
	echo "[!] Failed to set capabilities for nmap"
	exit 12
else
	echo "[+] Successfully set capabilities for nmap"
fi

if ! which chromium-browser >/dev/null; then
	echo '[+] Installing chromium-browser: apt-get install -y chromium-browser'
	apt-get install -y chromium-browser
	if ! which chromium-browser >/dev/null; then
		echo "[!] Failed to install chromium-browser" && exit 7
	else
		echo "[+] Successfully installed chromium-browser: $(which chromium-browser)"
	fi
else
	echo "[+] Found chromium-browser: $(which chromium-browser)"
fi

if ! which unzip >/dev/null; then
	echo '[+] Installing unzip: apt-get install -y unzip'
	apt-get install -y unzip
	if ! which unzip >/dev/null; then
		echo "[!] Failed to install unzip" && exit 8
	else
		echo "[+] Successfully installed unzip: $(which unzip)"
	fi
else
	echo "[+] Found unzip: $(which unzip)"
fi

if ! which xvfb-run >/dev/null; then
	echo '[+] Installing xvfb-run: apt-get install -y xvfb'
	apt-get install -y xvfb
	if ! which xvfb-run >/dev/null; then
		echo "[!] Failed to install xvfb-run" && exit 9
	else
		echo "[+] Successfully installed xvfb-run: $(which xvfb-run)"
	fi
else
	echo "[+] Found xvfb-run: $(which xvfb-run)"
fi

if ! which vncsnapshot >/dev/null; then
	echo '[+] Installing vncsnapshot: apt-get install -y vncsnapshot'
	apt-get install -y vncsnapshot
	if ! which vncsnapshot >/dev/null; then
		echo "[!] Failed to install vncsnapshot" && exit 10
	else
		echo "[+] Successfully installed vncsnapshot: $(which vncsnapshot)"
	fi
else
	echo "[+] Found vncsnapshot: $(which vncsnapshot)"
fi

# The old supported aquatone, 1.4.3, did not support the -version flag, so we can use this to tell if we need to upgrade
if ! which aquatone >/dev/null || aquatone -version 2>&1 | grep "flag provided but not defined: -version" >/dev/null; then
	echo '[+] Downloading Aquatone'
	wget $AQUATONEURL -O /tmp/aquatone.zip -q && unzip /tmp/aquatone.zip -d /tmp/aquatone && cp /tmp/aquatone/aquatone /usr/local/bin/aquatone
	rm -rf /tmp/aquatone.zip /tmp/aquatone
	if ! which aquatone >/dev/null; then
		echo "[!] Failed to install Aquatone" && exit 11
	else
		echo "[+] Successfully installed Aquatone: $(which aquatone)"
	fi
else
	echo "[+] Found Aquatone: $(which aquatone)"
fi

if [ ! -d data ]; then
	echo '[+] Creating data directory'
	mkdir data
	if [ ! -d data ]; then
		echo "[!] Failed to make data directory" && exit 12
	else
		echo "[+] Successfully created data directory"
	fi
else
	echo "[+] Found data directory"
fi

if [ ! -d logs ]; then
	echo '[+] Creating logs directory'
	mkdir logs
	if [ ! -d logs ]; then
		echo "[!] Failed to make logs directory" && exit 12
	else
		echo "[+] Successfully created logs directory"
	fi
else
	echo "[+] Found logs directory"
fi