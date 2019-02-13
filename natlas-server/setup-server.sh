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
    echo "[+] Updating apt repositories"
    apt-get update
fi

ELASTIC=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9200/_nodes)
if [ $ELASTIC != "200" ]
then
    ELASTICMSG="[!] Could not detect elasticsearch running on localhost:9200. Make sure you connect the server to an elasticsearch instance"
    echo $ELASTICMSG
else
    echo "[+] We got a response for http://localhost:9200/_nodes, we're assuming this is elasticsearch."
fi

if ! which python3 >/dev/null
then
    echo "[!] python3 not found: apt-get -y install python3.6"
    if [ $WHOAMI == "root" ]
    then
        apt-get -y install python3.6
    else
        FAIL=true
    fi
else
    echo "[+] python3 found"
fi

if ! which pip3 >/dev/null
then
    echo "[!] pip3 not found: apt-get -y install python3-pip"
    if [ $WHOAMI == "root" ]
    then
        apt-get -y install python3-pip
    else
        FAIL=true
    fi
else
    echo "[+] pip3 found"
fi

if ! which virtualenv >/dev/null
then
    echo "[!] virtualenv not found: pip3 install virtualenv"
    if [ $WHOAMI == "root" ]
    then
        pip3 install virtualenv
    else
        FAIL=true
    fi
else
    echo "[+] virtualenv found"
fi

if [ $FAIL == true ]
then
    echo "[!] Failed during python environment setup, we can't continue!"
    exit 1
fi

if [ ! -d venv ]
then
    echo "[+] Creating new python3 virtualenv named venv"
    virtualenv -p /usr/bin/python3 venv
fi

if [ ! -e venv/bin/activate ]
then
    echo "[!] No venv activate script found: venv/bin/activate"
    exit 1
fi

echo "[+] Entering virtual environment"
source venv/bin/activate
echo "[+] Attempting to install python dependencies"
pip3 install -r requirements.txt
echo "[+] Initializing metadata database"
echo "FLASK_APP=natlas-server.py" >> .env
flask db upgrade
echo "[+] Populating database with default configs"
python3 config.py
echo "[+] Exiting virtual environment"
deactivate
echo "[+] Setup Complete"
echo $ELASTICMSG
echo "[+] An example systemd script can be found in deployment/natlas-server.service"
echo "[+] An example nginx config can be found in deployment/nginx"
echo "[+] We highly recommend you use nginx to proxy connections to the flask application."