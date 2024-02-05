FROM ubuntu:latest as build

# Install Micromamba
RUN apt-get update && apt-get install -y curl bzip2
RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba

COPY pctiler/environment.yaml /tmp/env.yaml

# Create a separate environment for the packages and remove unnecessary files
RUN micromamba create -p /opt/conda/envs/myenv -f /tmp/env.yaml && \
    micromamba clean --all --yes && \
    rm -rf /root/.cache /tmp/env.yaml

# Start from a new stage to avoid copying the build environment, and
# copy the environment from the build stage
# Remove unnecessary files
RUN find /opt/conda/envs/myenv -type f -name "*.pyc" -exec rm -f {} \;
RUN rm -rf /opt/conda/envs/myenv/share/doc
RUN rm -rf /opt/conda/envs/myenv/share/locale
RUN rm -rf /opt/conda/envs/myenv/man
RUN rm -rf /opt/conda/envs/myenv/include

FROM ubuntu:latest

COPY --from=build /opt/conda/envs/myenv /opt/conda/envs/myenv
ENV PATH="/opt/conda/envs/myenv/bin:$PATH"

WORKDIR /opt/src

COPY pccommon /opt/src/pccommon
COPY pctiler /opt/src/pctiler

# Install the local modules in the new environment
RUN /bin/sh -c "python -m pip install --no-cache-dir -e ./pccommon -e ./pctiler[server]"

# Override starlette version
RUN /bin/sh -c "python -m pip install --upgrade --force-reinstall starlette==0.27.0"

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
