import sqlite3
import argparse
from os import getenv
from time import sleep
from typing import List, Union


from sentry_sdk import start_span, start_transaction
from venmo_api import Client, Transaction
from venmo_auto_cashout.lunchmoney import generate_rules


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
        "--token",
        type=str,
        default=getenv("VENMO_API_TOKEN"),
        required=not getenv("VENMO_API_TOKEN"),
        help="Your venmo API token",
    )
    parser.add_argument(
        "--transaction-db",
        type=str,
        default=getenv("TRANSACTION_DB"),
        help="File to tracks which transactions have been seen, used for expense tracking",
    )
    parser.add_argument(
        "--lunchmoney-email",
        type=str,
        default=getenv("LUNCHMONEY_EMAIL"),
        help="Authenticate with Lunchmoney to add matching rules on cashout",
    )
    parser.add_argument(
        "--lunchmoney-password",
        type=str,
        default=getenv("LUNCHMONEY_PASSWORD"),
    )
    parser.add_argument(
        "--lunchmoney-otp-secret",
        type=str,
        default=getenv("LUNCHMONEY_OTP_SECRET"),
    )

    args = parser.parse_args()

    db_path: Union[str, None] = args.transaction_db
    db = None

    # Setup transactions table when sqlite-transaction-db option is set
    if db_path is not None:
        db = sqlite3.connect(db_path)
        db.cursor().execute(
            """
            CREATE TABLE IF NOT EXISTS seen_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT,
                date_created DATETIME DEFAULT (STRFTIME('%d-%m-%Y   %H:%M', 'NOW','localtime'))
            );"""
        )

    # We can track 'expenses' when the database AND lunchmoney API are configured
    track_expenses = db_path is not None and args.lunchmoney_email is not None

    # Get list of know transaction IDs
    seen_transaction_ids: Union[None, List[str]] = None

    if db and track_expenses:
        cursor = db.cursor()
        cursor.execute("SELECT transaction_id FROM seen_transactions")
        seen_transaction_ids = [row[0] for row in cursor.fetchall()]

    def output(msg: str):
        if not args.quiet:
            print(msg)

    with start_transaction(op="cashout", name="cashout") as tran:
        tran.set_tag("dry_run", args.dry_run)

        # Venmo API client
        with start_span(op="init_venmo_client"):
            venmo = Client(access_token=args.token)

        me = venmo.my_profile()
        if not me:
            raise Exception("Failed to load Venmo profile")

        current_balance: int = me.balance
        tran.set_tag("cashout_balance", "${:,.2f}".format(current_balance / 100))

        if current_balance == 0 and not track_expenses:
            tran.set_tag("has_transactions", False)
            output("Your venmo balance is zero. Nothing to do")
            return

        # Sleep for 5 seconds to make sure the transactions actually show up
        output("Your balance is ${:,.2f}".format(current_balance / 100))
        output("Waiting 5 seconds before querying transactions...")
        sleep(5.0)

        # XXX: There may be some leftover amount if the transactions do not match
        # up exactly to the current account balance.
        remaining_balance = current_balance

        income_transactions: List[Transaction] = []
        expense_transactions: List[Transaction] = []

        with start_span(op="get_transactions"):
            transactions = venmo.user.get_user_transactions(user=me)

            if transactions is None:
                raise Exception("Failed to load trnasctions")

            # Produce a list of eligible transactions
            for transaction in transactions:
                is_expense = transaction.payee.username != me.username

                # Extract expense transactions we haven't seen yet
                if is_expense:
                    if track_expenses and transaction.id not in seen_transaction_ids:
                        expense_transactions.append(transaction)

                # Only track income transactions until we've exhausted the
                # current balance
                elif transaction.amount <= remaining_balance:
                    remaining_balance = remaining_balance - transaction.amount
                    income_transactions.append(transaction)

        all_transactions = [*income_transactions, *expense_transactions]
        has_transactions = len(all_transactions) > 0

        tran.set_tag("has_transactions", has_transactions)
        tran.set_tag("income_count", len(income_transactions))
        tran.set_tag("expense_count", len(expense_transactions))

        tran.set_data(
            "income_transactions",
            [
                {"payer": t.payer.display_name, "amount": t.amount, "note": t.note}
                for t in income_transactions
            ],
        )
        tran.set_data(
            "expense_transactions",
            [
                {"payee": t.payee.display_name, "amount": t.amount, "note": t.note}
                for t in expense_transactions
            ],
        )

        # Show some details about what we're about to do
        output("There are {} income transactions to cash-out".format(len(income_transactions)))
        output("There are {} expense transactions to track".format(len(expense_transactions)))

        if has_transactions or remaining_balance > 0:
            output("")

        for transaction in income_transactions:
            output(
                " -> Income: +${price:,.2f} -- {name} ({note})".format(
                    name=transaction.payer.display_name,
                    price=transaction.amount / 100,
                    note=transaction.note,
                )
            )

        if remaining_balance > 0:
            output(" -> Income: ${:,.2f} of extra balance".format(remaining_balance / 100))

        for transaction in expense_transactions:
            output(
                " -> Expense: -${price:,.2f} -- {name} ({note})".format(
                    name=transaction.payee.display_name,
                    price=transaction.amount / 100,
                    note=transaction.note,
                )
            )

        # Nothing left to do in dry-run mode
        if args.dry_run:
            output("\ndry-run -- Not initiating transfers")
            return

        # Do the transactions
        with start_span(op="initiate_transfer"):
            for transaction in income_transactions:
                venmo.transfer.initiate_transfer(amount=transaction.amount)

            if remaining_balance > 0:
                venmo.transfer.initiate_transfer(amount=remaining_balance)

        # Create lunchmoney rules for each transaction
        if args.lunchmoney_email is not None:
            with start_span(op="lunchmoney_create_rules"):
                generate_rules(
                    transactions=all_transactions,
                    me=me,
                    email=args.lunchmoney_email,
                    password=args.lunchmoney_password,
                    otp_secret=args.lunchmoney_otp_secret,
                )

        # Update seen expense transaction
        if db and track_expenses:
            records = [(t.id,) for t in all_transactions]
            cursor = db.cursor()
            cursor.executemany("INSERT INTO seen_transactions (transaction_id) VALUES(?)", records)
            db.commit()

        output("\nAll money transfered out!")
