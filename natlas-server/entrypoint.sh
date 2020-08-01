#!/bin/bash
set +x

mkdir -p /data/{db,media}

flask db upgrade
chown -R www-data:www-data /data
exec runuser -u www-data -- "$@"
