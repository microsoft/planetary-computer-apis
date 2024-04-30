FROM mcr.microsoft.com/azure-cli:cbl-mariner2.0

# URL used to download the packages from the CFS
ARG INDEX_URL
ENV PIP_INDEX_URL=$INDEX_URL

# Setup pip and server dependencies
RUN python3 -m ensurepip --upgrade
RUN pip3 install fastapi uvicorn[standard] azure-identity

WORKDIR /opt/src

COPY . /opt/src

CMD uvicorn main:app --host 0.0.0.0 --port 8086 --reload --log-level info
