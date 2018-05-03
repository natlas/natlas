#!/bin/bash

export LC_ALL="C.UTF-8"
export LANG="C.UTF-8"
export FLASK_APP=./nweb_server.py

if ! hash virtualenv 2>/dev/null
then
    echo "[!] virtualenv not found"
    exit 1
fi

if ! hash pip3 >/dev/null
then
    echo "[!] pip3 not found"
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
    echo "" > config/blacklist.txt
fi

echo "[+] Entering virtual environment"
source venv/bin/activate
echo "[+] Attempting to install python dependencies"
pip3 install -r requirements.txt
