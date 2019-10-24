#!/bin/sh

mkdir -p /data/{db,media} logs

DATABASE_FILE=${SQLALCHEMY_DATABASE_URI//sqlite:\/\/\//}
if [ ! -f "${DATABASE_FILE}" ]; then 
  echo "[+] Creating database"
  export FLASK_APP=./natlas-server.py
  flask db upgrade
fi

chown -R www-data:www-data /data
chown -R www-data:www-data logs
exec runuser -m -p -u www-data -- "$@"
