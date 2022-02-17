FROM python:3.8.7-buster

# The devops Personal Access Token for accessing
# Azure Artifacts. Note: This will be visible as
# plain text in the docker build logs. Only use your
# PAT for development containers in your local environment.
# Azure Pipelines will utilize a temporary key for builds
# when building deploy images so that there is not arisk of
# exposure.
ARG DEVOPS_PAT

EXPOSE 8000

RUN apt-get update && \
    apt-get install -y build-essential

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

RUN pip install --upgrade pip setuptools wheel

WORKDIR /opt/src

COPY pctiler/gunicorn_conf.py gunicorn_conf.py

COPY pccommon /opt/src/pccommon
COPY pctiler /opt/src/pctiler
RUN pip install -e ./pccommon -e ./pctiler[server]

# GDAL config
ENV GDAL_CACHEMAX 200
ENV GDAL_INGESTED_BYTES_AT_OPEN 16383
ENV GDAL_DISABLE_READDIR_ON_OPEN EMPTY_DIR
ENV GDAL_HTTP_MERGE_CONSECUTIVE_RANGES YES
ENV GDAL_HTTP_MULTIPLEX YES
ENV GDAL_HTTP_VERSION 2
ENV VSI_CACHE TRUE
ENV VSI_CACHE_SIZE 5000000

# TiTiler mosaic config
ENV MOSAIC_CONCURRENCY 1

ENV APP_HOST=0.0.0.0
ENV APP_PORT=80

# Do not use --preload, because it doesn't work correctly with OpenCensus
CMD gunicorn pctiler.main:app -k uvicorn.workers.UvicornWorker \
    -c gunicorn_conf.py --bind ${APP_HOST}:${APP_PORT} --log-level info
