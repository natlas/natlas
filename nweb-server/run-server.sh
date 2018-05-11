#!/bin/bash

export LC_ALL="C.UTF-8"
export LANG="C.UTF-8"
export FLASK_APP=./nweb-server.py

source venv/bin/activate
while [ 1 == 1 ]
do
  echo `date` >> start.log
  flask run --with-threads # --host=0.0.0.0
  sleep 5
done
