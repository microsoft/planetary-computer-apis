FROM mcr.microsoft.com/azure-functions/python:4-python3.8

# git required for pip installs from git
RUN apt update && apt install -y git

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY pccommon /home/site/pccommon

RUN mkdir -p /home/site/wwwroot
WORKDIR /home/site/wwwroot

COPY pcfuncs/requirements.txt /home/site/wwwroot/requirements.txt
RUN pip install -r /home/site/wwwroot/requirements.txt

COPY requirements-dev.txt /home/site/
RUN pip install -r /home/site/requirements-dev.txt

ENV PYTHONPATH=/home/site/wwwroot
