FROM mcr.microsoft.com/azure-functions/python:4-python3.8

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true


# TODO: Ask about requirement of v3 for function proxies.
# # Install azure functions core tools
# ENV DEBIAN_VERSION=10

# RUN wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.asc.gpg
# RUN mv microsoft.asc.gpg /etc/apt/trusted.gpg.d/
# RUN wget -q https://packages.microsoft.com/config/debian/$DEBIAN_VERSION/prod.list
# RUN mv prod.list /etc/apt/sources.list.d/microsoft-prod.list
# RUN chown root:root /etc/apt/trusted.gpg.d/microsoft.asc.gpg
# RUN chown root:root /etc/apt/sources.list.d/microsoft-prod.list

# RUN apt-get update

# # Must use functions v3 to keep support for function proxies
# RUN apt-get install azure-functions-core-tools-3

COPY pccommon /home/site/pccommon

RUN mkdir -p /home/site/wwwroot
WORKDIR /home/site/wwwroot

COPY pcfuncs/requirements.txt /home/site/wwwroot/requirements.txt
RUN pip install -r /home/site/wwwroot/requirements.txt

COPY requirements-dev.txt /home/site/
RUN pip install -r /home/site/requirements-dev.txt