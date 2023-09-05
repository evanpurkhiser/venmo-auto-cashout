FROM python:3.11-alpine

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
COPY pdm.lock pyproject.toml README.md /app/
RUN pdm install

# Add python source
COPY venmo_auto_cashout /app/venmo_auto_cashout/
RUN pdm install

COPY dockerStart.sh /app/dockerStart.sh

ENTRYPOINT ["./dockerStart.sh"]
