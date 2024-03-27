FROM python:3.9-slim

WORKDIR /opt/src

COPY pccommon /opt/src/pccommon
COPY pctiler /opt/src/pctiler

# Install the local modules in the new environment
RUN /bin/sh -c "python -m pip install -U 'setuptools>=65.5.1'"
# The order of these pip installs is important :(
RUN /bin/sh -c "python -m pip install -r ./pccommon/requirements.txt"
RUN /bin/sh -c "python -m pip install -r ./pctiler/requirements-server.txt"
RUN /bin/sh -c "python -m pip install --no-deps -e ./pccommon -e ./pctiler[server]"

# GDAL config
ENV GDAL_CACHEMAX 200
ENV GDAL_INGESTED_BYTES_AT_OPEN 32768
ENV GDAL_DISABLE_READDIR_ON_OPEN EMPTY_DIR
ENV GDAL_HTTP_MERGE_CONSECUTIVE_RANGES YES
ENV GDAL_HTTP_MULTIPLEX YES
ENV GDAL_HTTP_VERSION 2
ENV GDAL_HTTP_MAX_RETRY 3
ENV GDAL_HTTP_RETRY_DELAY 0.2
# Avoid segfault in rasterio 1.2.10 when reading compound CRS.
# https://github.com/rasterio/rasterio/issues/2415
ENV GTIFF_REPORT_COMPD_CS=0
ENV VSI_CACHE FALSE
ENV VSI_CACHE_SIZE 0
ENV CPL_VSIL_CURL_CACHE_SIZE 200000000

# Experimental flag to deallocate process memory quickly
ENV MALLOC_TRIM_THRESHOLD_=0

# TiTiler mosaic config
ENV MOSAIC_CONCURRENCY 1

ENV APP_HOST=0.0.0.0
ENV APP_PORT=80

CMD uvicorn pctiler.main:app --host ${APP_HOST} --port ${APP_PORT} --log-level info
