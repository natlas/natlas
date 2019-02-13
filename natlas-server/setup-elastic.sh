#!/bin/bash

ELASTICDOWNLOAD='https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.6.0.deb'

apt-get install -y default-jre
wget $ELASTICDOWNLOAD -O /tmp/elasticsearch.deb
dpkg -i /tmp/elasticsearch.deb
systemctl start elasticsearch