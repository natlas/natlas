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
    if $WHOAMI == "root"
    then
        apt-get install -y python3.6
    else
        $FAIL=true
    fi
else
	echo '[+] Python3 found'
fi

if ! which nmap >/dev/null
then
    echo '[!] nmap not found'
    if $WHOAMI == "root"
    then
        apt-get install -y nmap
    else
        $FAIL=true
    fi
else
	echo '[+] nmap found'
fi

if ! which chromium-browser >/dev/null
then
    echo '[!] chromium-browser not found.'
    if $WHOAMI == "root"
    then
        apt-get install -y chromium-browser
    else
        $FAIL=true
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

if ! which vncsnapshot >/dev/null
then
    echo '[!] vncsnapshot not found'
    if $WHOAMI == "root"
    then
        apt-get install -y vncsnapshot
    else
        $FAIL=true
    fi
else
	echo '[+] vncsnapshot found'
fi


echo '[+] Setup Complete'