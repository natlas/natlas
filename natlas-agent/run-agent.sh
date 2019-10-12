#!/bin/bash

export LC_ALL="C.UTF-8"
export LANG="C.UTF-8"

source venv/bin/activate

if [ ! -d logs ]; then
	mkdir logs
fi

PYTHON_COMMAND="$(which python3 || which python3.6)"


"${PYTHON_COMMAND}" ./natlas-agent.py