#!/usr/bin/env sh

sentry-cli monitors run "$SENTRY_MONITOR_ID" -- pdm run venmo-auto-cashout
