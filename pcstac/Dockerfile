FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y build-essential git

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

WORKDIR /opt/src

COPY .isort.cfg .isort.cfg
COPY pcstac/gunicorn_conf.py gunicorn_conf.py

COPY pcstac pcstac
COPY pccommon pccommon
RUN pip install ./pccommon ./pcstac["server"]
RUN rm -rf pcstac pccommon

ENV APP_HOST=0.0.0.0
ENV APP_PORT=81

# Do not use --preload, because it doesn't work correctly with OpenCensus
CMD gunicorn pcstac.main:app -k uvicorn.workers.UvicornWorker \
    -c gunicorn_conf.py --bind ${APP_HOST}:${APP_PORT} --log-level info
