FROM node:12-stretch as webpack
ARG NATLAS_VERSION=unknown

WORKDIR /app
COPY ["package.json", "yarn.lock", "/app/"]
ENV NATLAS_VERSION=$NATLAS_VERSION
RUN yarn --no-progress --frozen-lockfile --non-interactive
COPY . /app
RUN yarn run webpack --mode production

FROM python:3.8 as build

COPY Pipfile .
COPY Pipfile.lock .

RUN pip install pipenv
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy \
    && rm -rf Pipfile Pipfile.lock

WORKDIR /opt/natlas/natlas-server
COPY . /opt/natlas/natlas-server

# Prepare assets
COPY --from=webpack /app/app/static/dist app/static/dist

RUN python3 -m compileall .
RUN mkdir logs \
  && chown www-data logs

# Build final image
FROM python:3.8-slim

COPY --from=build /.venv /.venv
COPY --from=build /opt/natlas /opt/natlas

WORKDIR /opt/natlas/natlas-server/
VOLUME ["/data"]
ENV SQLALCHEMY_DATABASE_URI="sqlite:////data/db/metadata.db"
ENV MEDIA_DIRECTORY="/data/media/"
ENV FLASK_APP=./natlas-server.py
ENV FLASK_ENV=production
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PATH="/.venv/bin:$PATH"
EXPOSE 5000
ENTRYPOINT ["/bin/bash", "entrypoint.sh"]

CMD ["gunicorn", "-b", "0.0.0.0:5000", "natlas-server:app"]
