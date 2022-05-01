from os import getenv

from venmo_auto_cashout.cli import run_cli
import sentry_sdk

sentry_dsn = getenv("SENTRY_DSN")
if sentry_dsn is not None:
    sentry_sdk.init(sentry_dsn, traces_sample_rate=1.0)


def main():
    run_cli()


if __name__ == "__main__":
    main()
