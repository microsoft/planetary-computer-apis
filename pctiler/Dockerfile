FROM pctiler-base:latest

COPY pctiler/environment.yaml /tmp/environment.yaml
RUN /opt/conda/bin/conda env update -f /tmp/environment.yaml
RUN source ~/.profile
# RUN /opt/conda/bin/conda activate base

RUN /opt/conda/bin/conda clean -afy \
    && find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
    && find /opt/conda/ -follow -type f -name '*.js.map' -delete

WORKDIR /opt/src

COPY pccommon /opt/src/pccommon
COPY pctiler /opt/src/pctiler

# Install the local modules in the new environment
# RUN /bin/sh -c "/opt/conda/python -m pip install --no-cache-dir -e ./pccommon -e ./pctiler[server]"
RUN /opt/conda/bin/conda develop ./pccommon ./pctiler[server]

# Remove unnecessary files
# RUN find /opt/conda/envs/myenv -type f -name "*.pyc" -exec rm -f {} \;
# RUN rm -rf /opt/conda/envs/myenv/share/doc
# RUN rm -rf /opt/conda/envs/myenv/share/locale
# RUN rm -rf /opt/conda/envs/myenv/man
# RUN rm -rf /opt/conda/envs/myenv/include

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

# # Run uvicorn as root. The build context user is $MAMBA_USER which doesn't have
# # permission to bind to port 80.
# USER root
CMD uvicorn pctiler.main:app --host ${APP_HOST} --port ${APP_PORT} --log-level info
