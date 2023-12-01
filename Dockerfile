FROM python:3.11

RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
  curl \
  cron \
  && apt-get clean && rm -rf /var/lib/apt/lists/*                                                                                                                │

WORKDIR /app

# Setup PDM
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
RUN pip install pdm
ENV PYTHONPATH=/usr/local/lib/python3.9/site-packages/pdm/pep582

# install python deps
COPY pdm.lock pyproject.toml README.md /app/
RUN pdm install --production

# Add python source
COPY venmo_auto_cashout /app/venmo_auto_cashout/
RUN pdm install --production

ENV SCHEDULE=NONE

COPY dockerStart.sh /app/dockerStart.sh

CMD ["./dockerStart.sh"]
