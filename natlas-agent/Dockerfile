FROM ubuntu:18.04
ARG DEBIAN_FRONTED=noninteractive
WORKDIR /opt/natlas/natlas-agent/

RUN mkdir -p /opt/natlas/natlas-agent/
COPY . /opt/natlas/natlas-agent

VOLUME ["/data"]

RUN env && bash ./setup-agent.sh

CMD [ "/bin/bash", "/opt/natlas/natlas-agent/run-agent.sh" ]