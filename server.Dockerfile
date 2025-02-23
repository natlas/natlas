FROM python:3.12-slim AS base

FROM node:20-bookworm AS webpack
ARG NATLAS_VERSION=unknown

WORKDIR /app
COPY server/package.json server/yarn.lock /app/
ENV NATLAS_VERSION=$NATLAS_VERSION
RUN yarn --no-progress --frozen-lockfile --non-interactive
COPY ./server/ /app
RUN yarn run webpack --mode production

FROM base AS build
COPY --from=ghcr.io/astral-sh/uv:0.6.2 /uv /uvx /bin/

RUN \
    --mount=type=bind,source=pyproject.toml,target=/pyproject.toml \
    --mount=type=bind,source=uv.lock,target=/uv.lock \
    --mount=type=cache,target=/root/.cache \
    uv sync --frozen --no-default-groups --only-group server

COPY ./server/ /server/

# Prepare assets
COPY --from=webpack /app/app/static/dist app/static/dist

# Build final image
FROM base

RUN rm -rf /var/cache/* /root /var/lib/apt/info/* /var/lib/apt/lists/* /var/lib/ghc /var/lib/dpkg /var/lib/log/* \
    && adduser --disabled-password --gecos "" --disabled-login docker

COPY --from=build /.venv/ /.venv/
COPY --from=build /server/ /server/

WORKDIR /server
ENV FLASK_APP=./natlas-server.py \
    FLASK_ENV=production \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PATH="/.venv/bin/:$PATH"
EXPOSE 5000
USER docker

CMD ["gunicorn", "-b", "0.0.0.0:5000", "natlas.asgi:application"]
