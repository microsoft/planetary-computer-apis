FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y build-essential git

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

RUN mkdir -p /opt/src/pcstac

COPY pcstac/requirements.txt /opt/src/requirements.txt

WORKDIR /opt/src

RUN pip install -r requirements.txt

# TODO:
# This code used to depend on unreleased stac-fastapi
# Including fix from https://github.com/stac-utils/stac-fastapi/pull/271
# Remove after release >2.1.2
RUN mkdir -p /opt/lib/stac-fastapi && \
    cd /opt/lib/stac-fastapi && \
    git init && \
    git remote add origin https://github.com/stac-utils/stac-fastapi.git && \
    git fetch origin b7398ef536727ba3bfe5e8c8a794ecfad5baa09e && \
    git reset --hard FETCH_HEAD && \
    make pybase-install && \
    make pgstac-install && \
    make sqlalchemy-install

COPY .isort.cfg /opt/src/.isort.cfg
COPY pcstac /opt/src/pcstac
COPY pccommon /opt/src/pccommon

ENV APP_HOST=0.0.0.0
ENV APP_PORT=81

ENV PYTHONPATH=/opt/src/pcstac:$PYTHONPATH

# Do not use --preload, because it doesn't work correctly with OpenCensus
CMD gunicorn pcstac.main:app -k uvicorn.workers.UvicornWorker \
    -c /opt/src/pcstac/gunicorn_conf.py --bind ${APP_HOST}:${APP_PORT} --log-level info
