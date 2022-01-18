FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y build-essential git

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

WORKDIR /opt/src

# PCCommon
COPY pccommon/requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN rm -rf requirements.txt

# PCStac
COPY pcstac/requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN rm -rf requirements.txt

COPY .isort.cfg /opt/src/.isort.cfg
COPY pcstac/gunicorn_conf.py gunicorn_conf.py

COPY pcstac /opt/src/pcstac
COPY pccommon /opt/src/pccommon
# Use --no-deps flag because they were previously installed with requirement.txt
RUN pip install -e ./pccommon -e ./pcstac --no-deps

ENV APP_HOST=0.0.0.0
ENV APP_PORT=81

# Do not use --preload, because it doesn't work correctly with OpenCensus
CMD gunicorn pcstac.main:app -k uvicorn.workers.UvicornWorker \
    -c gunicorn_conf.py --bind ${APP_HOST}:${APP_PORT} --log-level info
