# Use a smaller base image, like python:3.9-slim
FROM python:3.9-slim as build

# Install Micromamba
RUN apt-get update && apt-get install -y curl bzip2
RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba

COPY pctiler/environment.yaml /tmp/env.yaml

# Create a separate environment for the packages and remove unnecessary files
RUN micromamba create -p /opt/conda/envs/myenv -f /tmp/env.yaml && \
    micromamba clean --all --yes && \
    rm -rf /root/.cache /tmp/env.yaml

# Multi-stage build to reduce the final image size
FROM python:3.9-slim

# Copy the environment from the build stage
COPY --from=build /opt/conda/envs/myenv /opt/conda/envs/myenv
ENV PATH="/opt/conda/envs/myenv/bin:$PATH"

EXPOSE 8000

WORKDIR /opt/src
ARG MAMBA_DOCKERFILE_ACTIVATE=1

COPY pccommon /opt/src/pccommon
COPY pctiler /opt/src/pctiler

# Install the local modules in the new environment
# RUN /bin/bash -c "source activate myenv && python3 -m pip install -e ./pccommon -e ./pctiler[server]"
RUN /bin/bash -c "python3 -m pip install -e ./pccommon -e ./pctiler[server]"

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

# Run uvicorn as root. The build context user is $MAMBA_USER which doesn't have
# permission to bind to port 80.
USER root
CMD uvicorn pctiler.main:app --host ${APP_HOST} --port ${APP_PORT} --log-level info
