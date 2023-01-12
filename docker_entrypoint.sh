#!/usr/bin/env sh

sentry-cli --api-key "$SENTRY_API_KEY" monitors run "$SENTRY_MONITOR_ID" -- pdm run venmo-auto-cashout
