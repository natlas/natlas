#!/bin/bash

export LC_ALL="C.UTF-8"
export LANG="C.UTF-8"

WHOAMI=$(whoami)
FAIL=false

if [ $WHOAMI != "root" ]
then
    echo "[+] Setup running without permissions. System-wide changes cannot be made."
else
    echo "[+] Setup running with permissions. Automatic installation will be attempted."
fi

ELASTIC=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9200)
if [ $ELASTIC != "200" ]
then
    echo "[!] Could not detect elasticsearch running on localhost:9200. Make sure you connect the server to an elasticsearch instance in config.py"
else
    echo "[+] We got a response for http://localhost:9200, we're assuming this is elasticsearch."
fi

if ! hash python3 >/dev/null
then
    echo "[!] python3 not found"
    if $WHOAMI == "root"
    then
        apt-get -y install python3.6
    else
        $FAIL=true
    fi
else
    echo "[+] python3 found"
fi

if ! hash pip3 >/dev/null
then
    echo "[!] pip3 not found"
    if $WHOAMI == "root"
    then
        apt-get -y install python3-pip
    else
        $FAIL=true
    fi
else
    echo "[+] pip3 found"
fi

if ! hash virtualenv >/dev/null
then
    echo "[!] virtualenv not found"
    if $WHOAMI == "root"
    then
        pip3 install virtualenv
    else
        $FAIL=true
    fi
else
    echo "[+] virtualenv found"
fi

if [ $FAIL = true ]
then
    exit 1
fi

if [ ! -d venv ]
then
    echo "[+] Creating new python3 virtualenv named venv"
    virtualenv -p /usr/bin/python3 venv
fi

if [ ! -e venv/bin/activate ]
then
    echo "[!] No venv activate script found"
    exit 1
fi

if [ ! -e config/scope.txt ]
then
    echo "[+] Generating default config/scope.txt"
    echo "127.0.0.1" > config/scope.txt
fi

if [ ! -e config/blacklist.txt ]
then
    echo "[+] Creating empty config/blacklist.txt"
    echo "127.0.1.1" > config/blacklist.txt
fi

echo "[+] Entering virtual environment"
source venv/bin/activate
echo "[+] Attempting to install python dependencies"
pip3 install -r requirements.txt
echo "[+] Initializing metadata database"
export FLASK_APP=nweb-server.py
flask db upgrade
echo "[+] Exiting virtual environment"
deactivate
echo "[+] Setup Complete"