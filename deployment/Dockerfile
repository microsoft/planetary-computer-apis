FROM ubuntu:18.04

RUN apt-get update
RUN apt-get install -y wget unzip curl gnupg \
    apt-transport-https \
    python3-pip \
    jq

# Install Terraform 0.14.4

RUN wget -O terraform.zip https://releases.hashicorp.com/terraform/0.14.4/terraform_0.14.4_linux_amd64.zip
RUN unzip terraform.zip
RUN mv terraform /usr/local/bin

# Install kubectl

RUN curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
RUN echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list
RUN apt-get update
RUN apt-get install -y kubectl

# Install Helm

RUN curl https://baltocdn.com/helm/signing.asc |  apt-key add -
RUN echo "deb https://baltocdn.com/helm/stable/debian/ all main" | tee /etc/apt/sources.list.d/helm-stable-debian.list
RUN apt-get update
RUN apt-get install helm=3.5.0-1

# Install azure client
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Jinja
RUN pip3 install Jinja2

WORKDIR /opt/src