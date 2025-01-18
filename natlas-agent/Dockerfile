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

FROM base AS python_build
COPY --from=ghcr.io/astral-sh/uv:0.5.21 /uv /uvx /bin/
RUN \
    --mount=type=bind,source=pyproject.toml,target=/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/uv.lock \
    --mount=type=cache,target=/root/.cache \
    uv sync --frozen


COPY . /agent/

# Build final image
FROM base
WORKDIR /agent
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install --no-install-recommends -qy chromium nmap xvfb vncsnapshot libcap2-bin \
    && setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip /usr/bin/nmap \
    && adduser --disabled-password --gecos "" --disabled-login docker \
    && rm -rf /var/cache/* /root /var/lib/apt/info/* /var/lib/apt/lists/* /var/lib/ghc /var/lib/dpkg /var/lib/log/* \
    && bash -c 'mkdir -p /data/{scans,conf,logs}' \
    && chown -R docker:docker /data

COPY --from=build /tmp/dumb-init /usr/bin/dumb-init
COPY --from=build /tmp/aquatone/aquatone /usr/bin/aquatone
COPY --from=python_build /.venv/ /.venv/
COPY --from=python_build /agent/ /agent/


USER docker
ENV LC_ALL='C.UTF-8' \
    PATH="/.venv/bin:$PATH"
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["/agent/natlas-agent.py"]
