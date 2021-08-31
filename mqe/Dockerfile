FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y build-essential git

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

RUN mkdir -p /opt/src/mqe

COPY mqe/requirements.txt /opt/src/requirements.txt

WORKDIR /opt/src

RUN pip install -r requirements.txt

COPY mqe /opt/src/mqe
COPY pqecommon /opt/src/pqecommon

ENV APP_HOST=0.0.0.0
ENV APP_PORT=81

ENV PYTHONPATH=/opt/src/mqe:/opt/pqe:/opt/dev/:$PYTHONPATH

# Do not use --preload, because it doesn't work correctly with OpenCensus
CMD gunicorn mqe.main:app -k uvicorn.workers.UvicornWorker \
    -c /opt/src/mqe/gunicorn_conf.py --bind ${APP_HOST}:${APP_PORT} --log-level info
