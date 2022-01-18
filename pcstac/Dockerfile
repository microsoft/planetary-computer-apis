FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y build-essential git

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

RUN mkdir -p /opt/src/pcstac

COPY pcstac/requirements.txt /opt/src/requirements.txt

WORKDIR /opt/src

RUN pip install -r requirements.txt

COPY .isort.cfg /opt/src/.isort.cfg
COPY pcstac /opt/src/pcstac
COPY pccommon /opt/src/pccommon

ENV APP_HOST=0.0.0.0
ENV APP_PORT=81

ENV PYTHONPATH=/opt/src/pcstac:$PYTHONPATH

# Do not use --preload, because it doesn't work correctly with OpenCensus
CMD gunicorn pcstac.main:app -k uvicorn.workers.UvicornWorker \
    -c /opt/src/pcstac/gunicorn_conf.py --bind ${APP_HOST}:${APP_PORT} --log-level info
