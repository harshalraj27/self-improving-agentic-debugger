FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ make \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash sandbox_user \
    && mkdir -p /app \
    && chown -R sandbox_user:sandbox_user /app

WORKDIR /app
USER sandbox_user
