#!/bin/bash

TARGETVER="6.6.0"
ELASTICDOWNLOAD='https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.6.0.deb'

if [[ "$EUID" -ne 0 ]]; then
	echo "[!] This script needs elevated permissions to run."
	exit 2
fi

if ! which java >/dev/null; then
	echo "[+] Installing java: apt-get install -y default-jre"
	apt-get update && apt-get install -y default-jre
	if ! which java >/dev/null; then
		echo "[!] Failed to install java"
	else
		echo "[+] Successfully installed java: $(which java)"
	fi
else
	echo "[+] Found java: $(which java)"
fi

ELASTIC=$(dpkg -s elasticsearch)
STATUSSTR="Status: install ok installed"
VERSTR="Version: "

if ! echo "$ELASTIC" | grep "$STATUSSTR" >/dev/null; then
	echo "[+] Downloading Elasticsearch"
	DOWNLOAD=1
elif ! echo "$ELASTIC" | grep "$VERSTR" | grep "$TARGETVER" >/dev/null; then
	echo "[+] Updating Elasticsearch to $TARGETVER"
	DOWNLOAD=1
else
	echo "[+] Found Elasticsearch $TARGETVER" && exit 0
fi

if [ $DOWNLOAD -eq 1 ]; then
	wget $ELASTICDOWNLOAD -O /tmp/elasticsearch.deb -q
	if [ ! -f /tmp/elasticsearch.deb ]; then
		echo "[!] Failed to download Elasticsearch: $ELASTICDOWNLOAD" && exit 1
	else
		echo "[+] Succesfully downloaded Elasticsearch"
	fi
	dpkg -i /tmp/elasticsearch.deb
	ELASTIC=$(dpkg -s elasticsearch)
	if ! echo "$ELASTIC" | grep "$STATUSSTR" >/dev/null; then
		echo "[!] Failed to install Elasticsearch $TARGETVER" && exit 2
	else
		echo "[+] Successfully installed Elasticsearch $TARGETVER"
		rm /tmp/elasticsearch.deb
	fi
fi

if ! systemctl is-active --quiet elasticsearch; then
	echo "[+] Starting Elasticsearch"
	systemctl start elasticsearch
else
	echo "[+] Restarting Elasticsearch"
	systemctl restart elasticsearch
fi

if ! systemctl is-enabled --quiet elasticsearch; then
	echo "[+] Enabling Elasticsearch"
	systemctl enable elasticsearch
fi

if ! systemctl is-active --quiet elasticsearch; then
	echo "[!] Failed to start Elasticsearch!" && exit 3
fi
