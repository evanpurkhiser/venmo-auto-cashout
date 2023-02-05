#!/usr/bin/env sh

if [ -z "$SENTRY_MONITOR_ID" ]; then
	exec pdm run venmo-auto-cashout
else
	exec sentry-cli monitors run "$SENTRY_MONITOR_ID" -- pdm run venmo-auto-cashout
fi
