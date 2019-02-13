#!/bin/bash
# sudo bash setup-agent.sh

WHOAMI=$(whoami)
FAIL=false

if [ $WHOAMI != "root" ]
then
    echo '[+] Setup running without permissions. System-wide changes cannot be made.'
else
    echo '[+] Setup running with permissions. Automatic installation will be attempted.'
fi

if ! which python3 >/dev/null
then
    echo '[!] Python3 not found'
    if [ $WHOAMI == "root" ]
    then
        apt-get install -y python3.6
    else
        FAIL=true
    fi
else
	echo '[+] Python3 found'
fi

if ! which pip3 >/dev/null
then
    echo "[!] pip3 not found"
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
    echo "[!] virtualenv not found"
    if [ $WHOAMI == "root" ]
    then
        pip3 install virtualenv
    else
        FAIL=true
    fi
else
    echo "[+] virtualenv found"
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
else
    echo "[+] Entering virtual environment"
    source venv/bin/activate
    echo "[+] Attempting to install python dependencies"
    pip3 install -r requirements.txt
    echo "[+] Exiting virtual environment"
    deactivate
fi

if ! which nmap >/dev/null
then
    echo '[!] nmap not found'
    if [ $WHOAMI == "root" ]
    then
        apt-get install -y nmap
    else
        FAIL=true
    fi
else
	echo '[+] nmap found'
fi

if ! which chromium-browser >/dev/null
then
    echo '[!] chromium-browser not found.'
    if [ $WHOAMI == "root" ]
    then
        apt-get install -y chromium-browser
    else
        FAIL=true
    fi
else
    echo '[+] chromium-browser found'
fi

if ! which aquatone >/dev/null
then
    echo '[!] aquatone not found. Please install it by reviewing the instructions: https://github.com/michenriksen/aquatone#installation'
else
	echo '[+] aquatone found'
fi

if ! which xvfb-run >/dev/null
then
    echo '[!] xvfb not found'
    if [ $WHOAMI == "root" ] 
    then
        apt-get install -y xvfb
    else
        FAIL=true
    fi
else
    echo '[+] xvfb found'
fi

if ! which vncsnapshot >/dev/null
then
    echo '[!] vncsnapshot not found'
    if [ $WHOAMI == "root" ]
    then
        apt-get install -y vncsnapshot
    else
        FAIL=true
    fi
else
	echo '[+] vncsnapshot found'
fi

if [ $FAIL == "true" ]
then
    echo '[!] Errors occurred during setup. Please review the log and make sure all dependencies are installed.'
else
    echo '[+] Setup Complete'
fi
