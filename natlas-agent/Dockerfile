FROM python:3.12-bookworm AS base

FROM base AS build

RUN export DEBIAN_FRONTEND=noninteractive \
	export BUILD_PKGS="unzip" \
	&& apt-get update \
	&& apt-get install --no-install-recommends -qy $BUILD_PKGS

RUN export AQUATONEURL='https://github.com/michenriksen/aquatone/releases/download/v1.7.0/aquatone_linux_amd64_1.7.0.zip' \
	&& wget $AQUATONEURL -O /tmp/aquatone.zip -q \
	&& unzip /tmp/aquatone.zip -d /tmp/aquatone \
	&& export DUMBINITURL='https://github.com/Yelp/dumb-init/releases/download/v1.2.2/dumb-init_1.2.2_amd64' \
	&& wget -O /tmp/dumb-init $DUMBINITURL \
	&& chmod +x /tmp/dumb-init

COPY Pipfile .
COPY Pipfile.lock .

RUN pip install pipenv
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy \
	&& rm -rf Pipfile Pipfile.lock deployment

COPY . /opt/natlas/natlas-agent

WORKDIR /opt/natlas/natlas-agent

RUN python3 -m compileall .

# Build final image
FROM base

RUN export DEBIAN_FRONTEND=noninteractive \
	&& apt-get update \
	&& apt-get install --no-install-recommends -qy chromium nmap xvfb vncsnapshot libcap2-bin \
	&& setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip /usr/bin/nmap \
	&& rm -rf /var/cache/* /root /var/lib/apt/info/* /var/lib/apt/lists/* /var/lib/ghc /var/lib/dpkg /var/lib/log/*

COPY --from=build /tmp/dumb-init /usr/bin/dumb-init
COPY --from=build /tmp/aquatone/aquatone /usr/bin/aquatone
COPY --from=build /opt/natlas /opt/natlas

RUN bash -c 'mkdir -p /data/{scans,conf,logs} \
	&& chown -R www-data:www-data /data'

COPY --from=build /.venv /.venv/
WORKDIR /opt/natlas/natlas-agent
USER www-data
ENV LC_ALL='C.UTF-8' \
    PATH="/.venv/bin:$PATH"
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["python3", "/opt/natlas/natlas-agent/natlas-agent.py"]
