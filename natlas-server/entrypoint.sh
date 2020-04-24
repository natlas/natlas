#!/bin/sh
set +x

mkdir -p /data/{db,media,logs}
ln -s /data/logs logs

DATABASE_FILE=${SQLALCHEMY_DATABASE_URI//sqlite:\/\/\//}
if [ ! -f "${DATABASE_FILE}" ]; then
  echo "[+] Creating database"
  flask db upgrade
fi

chown -R www-data:www-data /data
exec runuser -u www-data -- "$@"
