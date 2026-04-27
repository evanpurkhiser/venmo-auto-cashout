FROM python:3.11-alpine

RUN apk add --update \
      curl \
      openssl-dev \
    && rm -rf /var/cache/apk/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

# Install dependencies first for better layer caching
COPY uv.lock pyproject.toml README.md /app/
RUN uv sync --frozen --no-install-project --no-dev

# Add python source and install the project
COPY venmo_auto_cashout /app/venmo_auto_cashout/
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

COPY dockerStart.sh /app/dockerStart.sh

ENTRYPOINT ["./dockerStart.sh"]
