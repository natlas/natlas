FROM node:20-bookworm AS webpack
ARG NATLAS_VERSION=unknown

WORKDIR /app
COPY ["package.json", "yarn.lock", "/app/"]
ENV NATLAS_VERSION=$NATLAS_VERSION
RUN yarn --no-progress --frozen-lockfile --non-interactive
COPY . /app
RUN yarn run webpack --mode production

FROM python:3.12 AS build

COPY Pipfile Pipfile.lock ./

RUN pip install pipenv
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy \
    && rm -rf Pipfile Pipfile.lock

WORKDIR /opt/natlas/natlas-server
COPY . /opt/natlas/natlas-server

# Prepare assets
COPY --from=webpack /app/app/static/dist app/static/dist

RUN python3 -m compileall .

# Build final image
FROM python:3.12-slim

RUN rm -rf /var/cache/* /root /var/lib/apt/info/* /var/lib/apt/lists/* /var/lib/ghc /var/lib/dpkg /var/lib/log/* \
    && adduser --disabled-password --no-create-home --gecos "" --disabled-login docker

COPY --from=build /.venv /.venv
COPY --from=build /opt/natlas /opt/natlas

WORKDIR /opt/natlas/natlas-server/
ENV FLASK_APP=./natlas-server.py \
    FLASK_ENV=production \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PATH="/.venv/bin:$PATH"
EXPOSE 5000
USER docker

CMD ["gunicorn", "-b", "0.0.0.0:5000", "natlas-server:app"]
