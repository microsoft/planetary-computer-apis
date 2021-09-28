FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y build-essential git

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

RUN mkdir -p /opt/src/mqe

COPY mqe/requirements.txt /opt/src/requirements.txt

WORKDIR /opt/src

RUN pip install -r requirements.txt

# This code used to depend on unreleased stac-fastapi
# RUN mkdir -p /opt/lib && \
#     cd /opt/lib && \
#     git clone --single-branch --branch master \
#     https://github.com/stac-utils/stac-fastapi.git && \
#     cd stac-fastapi && \
#     make pybase-install && \
#     make pgstac-install && \
#     make sqlalchemy-install
# RUN pip install pypgstac==0.2.8

COPY mqe /opt/src/mqe
COPY pqecommon /opt/src/pqecommon

ENV APP_HOST=0.0.0.0
ENV APP_PORT=81

ENV PYTHONPATH=/opt/src/mqe:/opt/pqe:/opt/dev/:$PYTHONPATH

# Do not use --preload, because it doesn't work correctly with OpenCensus
CMD gunicorn mqe.main:app -k uvicorn.workers.UvicornWorker \
    -c /opt/src/mqe/gunicorn_conf.py --bind ${APP_HOST}:${APP_PORT} --log-level info
