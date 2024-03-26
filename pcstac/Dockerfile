FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y build-essential git

ENV CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

WORKDIR /opt/src

COPY pcstac /opt/src/pcstac
COPY pccommon /opt/src/pccommon
RUN pip install -r ./pcstac/requirements-server.txt
RUN pip install -e ./pccommon -e ./pcstac[server]

ENV APP_HOST=0.0.0.0
ENV APP_PORT=81

CMD uvicorn pcstac.main:app --host ${APP_HOST} --port ${APP_PORT} --log-level info
