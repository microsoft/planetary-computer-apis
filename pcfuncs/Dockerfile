FROM mcr.microsoft.com/azure-functions/python:4-python3.8

# git required for pip installs from git
RUN apt update && apt install -y git
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY pccommon /home/site/pccommon

RUN mkdir -p /home/site/wwwroot
WORKDIR /home/site/wwwroot

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=pcfuncs/requirements.txt,target=/home/site/wwwroot/requirements.txt \
    pip install -r /home/site/wwwroot/requirements.txt

RUN --mount=type=cache,target=/root/.cache \
    --mount=type=bind,source=requirements-dev.txt,target=/home/site/requirements-dev.txt \
    pip install -r /home/site/requirements-dev.txt

ENV PYTHONPATH=/home/site/wwwroot
