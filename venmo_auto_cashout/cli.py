import argparse
import sqlite3

from os import getenv
from time import sleep
from typing import List, Union

from datetime import datetime, timedelta
from sentry_sdk import start_span, start_transaction
from venmo_api import Client, Transaction
from venmo_auto_cashout.venmo import load_venmo_transactions
from venmo_auto_cashout.lunchmoney import post_transactions_to_lunchmoney

# The Command Line Interface (CLI) for venmo-to-lunch-money.
def run_cli():
    parser = argparse.ArgumentParser(
        description="Automatically cash-out your Venmo balance as individual transfers"
    )
    parser.add_argument(
        "--quiet", action=argparse.BooleanOptionalAction, help="Do not produce any output"
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="Do not actually initiate bank transfers",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=30,
        help="Number of days to lookback for fetching Venmo transactions (defaults to 30)."
    )
    parser.add_argument(
        "--venmo-api-key",
        type=str,
        default=getenv("VENMO_API_KEY"),
        required=not getenv("VENMO_API_KEY"),
        help="Your venmo API token",
    )
    parser.add_argument(
        "--lunchmoney-api-key",
        type=str,
        required=not getenv("LUNCHMONEY_API_KEY"),
        default=getenv("LUNCHMONEY_API_KEY"),
    )

    args = parser.parse_args()

    def log(message: str):
        prefix = '[dry run]: ' if args.dry_run else ''
        if not args.quiet:
            print(f"{prefix}{message}")

    now : datetime = datetime.utcnow()
    start_time : datetime = datetime.combine((now - timedelta(days = args.lookback_days)), datetime.min.time())

    venmo_transactions : list[Transaction] = load_venmo_transactions(
        api_key = args.venmo_api_key,
        start_time = start_time,
        end_time = now,
        log = log
    )

    log(f"Finished fetching {len(venmo_transactions)} transactions from Venmo.")
    log(f"\n**Newest transaction:**\n{venmo_transactions[0]}")
    log(f"\n**Oldest transaction:**\n{venmo_transactions[-1]}")
    log(f"Attempting to post {len(venmo_transactions)} transactions to Lunch Money...")
    if args.dry_run:
        log(f"Dry run succeeded and did NOT post any actual data to Lunch Money!")
        return
    response = post_transactions_to_lunchmoney(
        api_key=args.lunchmoney_api_key,
        log=log,
        transactions=venmo_transactions,
    )
    num_duplicates = len(venmo_transactions) - len(response)
    if num_duplicates > 0:
        log(f"{num_duplicates} duplicate transactions were filtered out due to already being imported to Lunch Money.")
    log(f"Successfully posted {len(response)} new transactions to LunchMoney.")