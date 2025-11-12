FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf update -y \
    && tdnf install -y ca-certificates build-essential \
    && tdnf clean all

WORKDIR /opt/src

COPY pcstac /opt/src/pcstac
COPY pccommon /opt/src/pccommon
RUN --mount=type=cache,target=/root/.cache \
    pip install -U "setuptools>=65.5.1"
# The order of these pip installs is important :(
RUN --mount=type=cache,target=/root/.cache \
    pip install -r ./pccommon/requirements.txt
RUN --mount=type=cache,target=/root/.cache \
    pip install -r ./pcstac/requirements-server.txt
RUN --mount=type=cache,target=/root/.cache \
    pip install --no-deps -e ./pccommon -e ./pcstac[server]

ENV APP_HOST=0.0.0.0
ENV APP_PORT=81

# This value should match that which is used as the root_path in FastAPI, which
# is typically set via the APP_ROOT_PATH environment variable.
ENV APP_ROOT_PATH=""

CMD uvicorn pcstac.main:app --host ${APP_HOST} --port ${APP_PORT} --root-path ${APP_ROOT_PATH} --log-level info
