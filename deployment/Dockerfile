FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf install -y \
    ca-certificates \
    build-essential \
    tar \
    wget \
    unzip \
    jq \
    git \
    azure-cli \
    && tdnf clean all

# Install Azure Function Tools
RUN wget https://github.com/Azure/azure-functions-core-tools/releases/download/4.0.5700/Azure.Functions.Cli.linux-x64.4.0.5700.zip \
    && unzip Azure.Functions.Cli.linux-x64.4.0.5700.zip -d /usr/local/azure-functions-core-tools-4 \
    && chmod +x /usr/local/azure-functions-core-tools-4/func \
    && chmod +x /usr/local/azure-functions-core-tools-4/gozip \
    && ln -s /usr/local/azure-functions-core-tools-4/func /usr/local/bin/func \
    && ln -s /usr/local/azure-functions-core-tools-4/gozip /usr/local/bin/gozip

# Install Terraform
RUN wget -O terraform.zip https://releases.hashicorp.com/terraform/1.11.2/terraform_1.11.2_linux_amd64.zip \
    && unzip terraform.zip \
    && mv terraform /usr/local/bin

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
RUN wget https://get.helm.sh/helm-v3.14.4-linux-amd64.tar.gz \
    && tar -zxvf helm-v3.14.4-linux-amd64.tar.gz \
    && mv linux-amd64/helm /usr/local/bin/helm

# Install kubelogin
RUN curl -sL https://github.com/Azure/kubelogin/releases/download/v0.2.8/kubelogin-linux-amd64.zip --output kubelogin.zip \
    && unzip -j kubelogin.zip bin/linux_amd64/kubelogin -d /usr/local/bin/ \
    && rm -rf kubelogin.zip

# Install Jinja
RUN pip install Jinja2 pyyaml==6.0.2

WORKDIR /opt/src
