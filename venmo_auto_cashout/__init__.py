from venmo_auto_cashout.cli import run_cli
import sentry_sdk

sentry_sdk.init(
    "https://6a82e95290ea41a6855178add346512a@o126623.ingest.sentry.io/6291319",
    traces_sample_rate=1.0,
)


def main():
    run_cli()


if __name__ == "__main__":
    main()
