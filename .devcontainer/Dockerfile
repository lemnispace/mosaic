FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

# Install unzip
RUN apt-get update && apt-get install -y unzip

# Download and install AWS SAM CLI
RUN curl -Lo aws-sam-cli-linux-arm64.zip https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-arm64.zip
RUN unzip aws-sam-cli-linux-arm64.zip -d sam-installation
RUN ./sam-installation/install