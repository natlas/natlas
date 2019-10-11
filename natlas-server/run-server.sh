#!/bin/bash

export LC_ALL="C.UTF-8"
export LANG="C.UTF-8"
export FLASK_APP=./natlas-server.py

source .env
source venv/bin/activate
DEPLOY_ENV=${FLASK_ENV:-production}

if [ ! -d logs ]; then
	mkdir logs
fi

if [ "$DEPLOY_ENV" == "development" ]
then
	echo "$(date) : Development" >> logs/start.log
	echo "$(date) : Development"
	flask run --with-threads # --host=0.0.0.0
else
	echo "$(date) : Production" >> logs/start.log
	echo "$(date) : Production"

	gunicorn -b "${BIND_ADDRESS:-127.0.0.1}":5000 natlas-server:app
fi
