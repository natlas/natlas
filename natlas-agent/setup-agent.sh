#!/bin/bash
# sudo bash setup-agent.sh

WHOAMI=$(whoami)
FAIL=false

if [ $WHOAMI != "root" ]
then
    echo "[+] Setup running without permissions. System-wide changes cannot be made."
else
    echo "[+] Setup running with permissions. Automatic installation will be attempted."
fi

if ! hash python3 >/dev/null
then
    echo "[!] Python3 not found"
    if $WHOAMI == "root"
    then
        apt-get -y install python3.6
    else
        $FAIL=true
    fi
else
	echo "[+] Python3 found"
fi

if ! hash nmap >/dev/null
then
    echo "[!] nmap not found"
    if $WHOAMI == "root"
    then
        apt-get -y install nmap
    else
        $FAIL=true
    fi
else
	echo "[+] nmap found"
fi

if ! hash wkhtmltoimage >/dev/null
then
    echo "[!] wkhtmltoimage not found"
    if $WHOAMI == "root"
    then
        apt-get -y install wkhtmltopdf
    else
        $FAIL=true
    fi
else
	echo "[+] wkhtmltoimage found"
fi

if ! hash vncsnapshot >/dev/null
then
    echo "[!] vncsnapshot not found"
    if $WHOAMI == "root"
    then
        apt-get -y install vncsnapshot
    else
        $FAIL=true
    fi
else
	echo "[+] vncsnapshot found"
fi


echo "[+] Setup Complete"