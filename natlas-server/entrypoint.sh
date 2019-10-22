#!/bin/sh

mkdir -p /data/{db,media}

chown -R www-data:www-data /data
exec runuser -u www-data -- "$@"
