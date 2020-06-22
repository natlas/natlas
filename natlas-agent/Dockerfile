FROM python:3.6 as build

RUN export DEBIAN_FRONTEND=noninteractive \
	export BUILD_PKGS="unzip" \
	&& apt-get update \
	&& apt-get install --no-install-recommends -qy $BUILD_PKGS

RUN export AQUATONEURL='https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip' \
	&& wget $AQUATONEURL -O /tmp/aquatone.zip -q \
	&& unzip /tmp/aquatone.zip -d /tmp/aquatone

COPY Pipfile .
COPY Pipfile.lock .

RUN pip install pipenv
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy \
	&& rm -rf Pipfile Pipfile.lock deployment

COPY . /opt/natlas/natlas-agent

WORKDIR /opt/natlas/natlas-agent
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
COPY --from=build /opt/natlas /opt/natlas

# We have to copy packages like this because the python directory is different between python images and ubuntu images
# So the /.venv/bin/python3 symlink ends point pointing to something that doesn't exist
COPY --from=build /.venv/lib/python3.6/site-packages /usr/local/lib/python3.6/dist-packages
WORKDIR /opt/natlas/natlas-agent
USER www-data
ENV LC_ALL='C.UTF-8'

CMD ["python3", "/opt/natlas/natlas-agent/natlas-agent.py"]
