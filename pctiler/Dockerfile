FROM python:3.9-slim

# The devops Personal Access Token for accessing
# Azure Artifacts. Note: This will be visible as
# plain text in the docker build logs. Only use your
# PAT for development containers in your local environment.
# Azure Pipelines will utilize a temporary key for builds
# when building deploy images so that there is not arisk of
# exposure.
ARG DEVOPS_PAT

EXPOSE 8000

WORKDIR /opt/src

COPY pccommon /opt/src/pccommon
COPY pctiler /opt/src/pctiler
RUN pip install -e ./pccommon -e ./pctiler[server]

# GDAL config
ENV GDAL_CACHEMAX 200
ENV GDAL_INGESTED_BYTES_AT_OPEN 32768
ENV GDAL_DISABLE_READDIR_ON_OPEN EMPTY_DIR
ENV GDAL_HTTP_MERGE_CONSECUTIVE_RANGES YES
ENV GDAL_HTTP_MULTIPLEX YES
ENV GDAL_HTTP_VERSION 2
# Avoid segfault in rasterio 1.2.10 when reading compound CRS.
# https://github.com/rasterio/rasterio/issues/2415
ENV GTIFF_REPORT_COMPD_CS=0
ENV VSI_CACHE TRUE
ENV VSI_CACHE_SIZE 50000000
ENV CPL_VSIL_CURL_CACHE_SIZE 200000000

# TiTiler mosaic config
ENV MOSAIC_CONCURRENCY 1

ENV APP_HOST=0.0.0.0
ENV APP_PORT=80
CMD uvicorn pctiler.main:app --host ${APP_HOST} --port ${APP_PORT} --log-level info
