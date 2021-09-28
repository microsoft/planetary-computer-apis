FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y build-essential git

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

RUN mkdir -p /opt/src/sas

COPY sas/requirements.txt /opt/src/requirements.txt

WORKDIR /opt/src

RUN pip install -r requirements.txt

RUN mkdir -p /opt/conf
COPY sas/gunicorn_conf.py /opt/src/sas/gunicorn_conf.py

ENV APP_HOST=0.0.0.0
ENV APP_PORT=80

ENV PYTHONPATH=/opt/src/sas:$PYTHONPATH
# Allow loading in local development codebases
ENV PYTHONPATH=/opt/dev:$PYTHONPATH

COPY pqecommon /opt/src/pqecommon
COPY sas/sas /opt/src/sas/sas
COPY sas/additional_collections.json /opt/src/sas/additional_collections.json
COPY sas/additional_containers.json /opt/src/sas/additional_containers.json

# Do not use --preload, because it doesn't work correctly with OpenCensus
CMD gunicorn sas.main:app -k uvicorn.workers.UvicornWorker \
    -c /opt/src/sas/gunicorn_conf.py --bind ${APP_HOST}:${APP_PORT} --log-level info
