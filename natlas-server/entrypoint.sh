#!/bin/sh
set +x

mkdir -p /data/{db,media,logs}
ln -s /data/logs logs

flask db upgrade
chown -R www-data:www-data /data
exec runuser -u www-data -- "$@"
