FROM python:3.9-alpine3.12

RUN apk add --update \
      curl \
      openssl-dev \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# Setup PDM
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
RUN pip install pdm
ENV PYTHONPATH=/usr/local/lib/python3.9/site-packages/pdm/pep582

# install python deps
COPY pdm.lock pyproject.toml /app/
RUN pdm install

# Add python source
COPY venmo_auto_cashout /app/venmo_auto_cashout/
RUN pdm install
