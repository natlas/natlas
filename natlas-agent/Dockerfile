FROM python:3.6.0 as build

RUN export DEBIAN_FRONTEND=noninteractive \
	export BUILD_PKGS="unzip" \
	&& apt-get update \
	&& apt-get install --no-install-recommends -qy $BUILD_PKGS

RUN export AQUATONEURL='https://github.com/michenriksen/aquatone/releases/download/v1.4.3/aquatone_linux_amd64_1.4.3.zip' \
	&& wget $AQUATONEURL -O /tmp/aquatone.zip -q \
	&& unzip /tmp/aquatone.zip -d /tmp/aquatone

WORKDIR /opt/natlas/natlas-agent
COPY requirements.txt /opt/natlas/natlas-agent

RUN pip3 --disable-pip-version-check --no-cache-dir install -r requirements.txt \
	&& rm -rf requirements.txt deployment

COPY . /opt/natlas/natlas-agent

RUN mkdir logs data tmp \
	&& chown www-data:www-data logs data tmp

RUN python3 -m compileall .

# Build final image
FROM ubuntu:18.04

RUN export DEBIAN_FRONTEND=noninteractive \
	&& apt-get update \
	&& apt-get install --no-install-recommends -qy python3 python3-pkg-resources chromium-browser nmap xvfb vncsnapshot libcap2-bin \
	&& setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip /usr/bin/nmap \
	&& rm -rf /var/cache/* /root /var/lib/apt/info/* /var/lib/apt/lists/* /var/lib/ghc /var/lib/dpkg /var/lib/log/*

COPY --from=build /tmp/aquatone/aquatone /usr/bin/aquatone
COPY --from=build /usr/local/lib/python3.6/site-packages /usr/local/lib/python3.6/dist-packages
COPY --from=build /opt/natlas /opt/natlas
WORKDIR /opt/natlas/natlas-agent
USER www-data
ENV LC_ALL='C.UTF-8'

CMD ["/usr/local/bin/python3", "/opt/natlas/natlas-agent/natlas-agent.py"]
