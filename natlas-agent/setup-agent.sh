#!/bin/bash
# sudo bash setup-agent.sh

WHOAMI=$(whoami)
FAIL=false
AQUATONEURL='https://github.com/michenriksen/aquatone/releases/download/v1.4.3/aquatone_linux_amd64_1.4.3.zip'

if [ $WHOAMI != "root" ]
then
    echo '[+] Setup running without permissions. System-wide changes cannot be made.'
else
    echo '[+] Setup running with permissions. Automatic installation will be attempted.'
    echo "[+] Updating apt repositories"
    apt-get update
fi

if ! which python3 >/dev/null
then
    echo '[!] Python3 not found: apt-get install -y python3.6'
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

if [ ! -d venv ]
then
    echo "[+] Creating new python3 virtualenv named venv"
    virtualenv -p /usr/bin/python3 venv
fi

if [ ! -e venv/bin/activate ]
then
    echo "[!] No venv activate script found: venv/bin/activate"
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
    echo '[!] nmap not found: apt-get install -y nmap'
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
    echo '[!] chromium-browser not found: apt-get install -y chromium-browser'
    if [ $WHOAMI == "root" ]
    then
        apt-get install -y chromium-browser
    else
        FAIL=true
    fi
else
    echo '[+] chromium-browser found'
fi

if ! which unzip >/dev/null
then
    echo "[!] unzip not found: apt-get install -y unzip"
    if [ $WHOAMI == "root" ]
    then
        apt-get install -y unzip
    else
        FAIL=true
    fi
else
    echo "[+] unzip found"
fi

if ! which aquatone >/dev/null
then
    AQUAMSG='[!] aquatone not found. Please install it by reviewing the instructions: https://github.com/michenriksen/aquatone#installation'
    echo $AQUAMSG
    if [ $WHOAMI == "root" ]
    then
        wget $AQUATONEURL -O /tmp/aquatone.zip && unzip /tmp/aquatone.zip -d /tmp/aquatone && cp /tmp/aquatone/aquatone /usr/local/bin/aquatone
        rm -rf /tmp/aquatone.zip /tmp/aquatone
        if ! which aquatone >/dev/null
        then
            echo "[!] Aquatone failed to install automatically"
        else
            echo "[+] Aquatone installed successfully"
        fi
    else
        FAIL=true
    fi
else
	echo '[+] aquatone found'
fi

if ! which xvfb-run >/dev/null
then
    echo '[!] xvfb not found: apt-get install -y xvfb'
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
    echo '[!] vncsnapshot not found: apt-get install -y vncsnapshot'
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
    if ! which aquatone >/dev/null
    then
        echo $AQUAMSG
    fi
    echo '[+] Setup Complete'
fi
