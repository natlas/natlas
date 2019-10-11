FROM ubuntu:18.04
ARG DEBIAN_FRONTED=noninteractive
WORKDIR /opt/natlas/natlas-server/

RUN mkdir -p /opt/natlas/natlas-server/
COPY . /opt/natlas/natlas-server

RUN env && bash ./setup-server.sh

CMD [ "/bin/bash", "/opt/natlas/natlas-server/run-server.sh" ]
