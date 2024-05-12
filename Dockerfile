FROM python:3.11

RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
  curl \
  cron \
  && apt-get clean && rm -rf /var/lib/apt/lists/*                                                                                                                │

WORKDIR /app

# import production python configuration variables
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONSAFEPATH=1

# import pip production config
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_ROOT_USER_ACTION=ignore

# Setup PDM
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
RUN pip install pdm==2.15.2
# ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages/pdm/pep582

# install python deps
COPY pdm.lock pyproject.toml README.md /app/
RUN pdm install --production

# Add python source
COPY venmo_auto_cashout /app/venmo_auto_cashout/
RUN pdm install --production

ENV SCHEDULE=NONE

COPY dockerStart.sh /app/dockerStart.sh

CMD ["./dockerStart.sh"]
