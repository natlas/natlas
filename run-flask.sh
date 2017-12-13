#!/bin/bash

export LC_ALL="C.UTF-8"
export LANG="C.UTF-8"
export FLASK_APP=./main.py

if ! hash virtualenv 2>/dev/null
then
    echo "virtualenv is required"
    exit 1
fi

if ! hash pip3 >/dev/null
then
    echo "you need pip3 installed"
    exit 1
fi

if [ ! -d venv ]
then
  virtualenv -p /usr/bin/python3 venv
fi

if [ ! -e venv/bin/activate ]
then
    echo "something is wrong with your venv setup"
    echo "bailing..."
    exit 1
fi
 
source venv/bin/activate
pip3 install flask
pip3 install netaddr
pip3 install elasticsearch

if [ ! -e nweb.db ]
then
    flask initdb
fi

while [ 1 == 1 ]
do
  echo `date` >> start.log
  flask run # --host=0.0.0.0
  sleep 5
done
