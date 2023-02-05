#!/usr/bin/env sh

if [ -z "$SENTRY_MONITOR_ID" ]; then
	pdm run venmo-auto-cashout
else
	sentry-cli monitors run "$SENTRY_MONITOR_ID" -- pdm run venmo-auto-cashout
fi
