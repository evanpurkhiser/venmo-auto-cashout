import sqlite3
import argparse
from os import getenv
from typing import List, Union


from sentry_sdk import start_span, start_transaction
from venmo_api import Client, Transaction

from venmo_auto_cashout.lunchmoney import update_lunchmoney_transactions


def run_cli():
    parser = argparse.ArgumentParser(
        description="Automatically cash-out your Venmo balance as individual transfers"
    )

    parser.add_argument(
        "--quiet",
        action=argparse.BooleanOptionalAction,
        help="Do not produce any output",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="Do not actually initiate bank transfers",
    )
    parser.add_argument(
        "--allow-remaining",
        action=argparse.BooleanOptionalAction,
        help="Allow remaining balance to be cashed-out",
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
        help="File to tracks which transactions have been seen. Required for LM integration",
    )
    parser.add_argument(
        "--lunchmoney-token",
        type=str,
        default=getenv("LUNCHMONEY_TOKEN"),
        help="Enables Lunch Money integration for tracking venmo",
    )
    parser.add_argument(
        "--lunchmoney-category",
        type=str,
        default=getenv("LUNCHMONEY_CATEGORY"),
        help="The Lunch Money category to look for venmo transactions",
    )

    args = parser.parse_args()

    if args.lunchmoney_token and not args.transaction_db:
        parser.error("--transaction-db must be specified to use the LM integration")

    if len([x for x in (args.lunchmoney_token, args.lunchmoney_category) if x is not None]) == 1:
        parser.error("--lunchmoney-{token,category} are both required for LM integration")

    db_path: Union[str, None] = args.transaction_db
    db = None

    # Setup transactions table when sqlite-transaction-db option is set
    if db_path is not None:
        db = sqlite3.connect(db_path)
        db.cursor().execute(
            """
            CREATE TABLE IF NOT EXISTS seen_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_type TEXT NOT NULL,
                transaction_id TEXT NOT NULL,
                amount INT NOT NULL,
                note TEXT NOT NULL,
                target_actor TEXT NOT NULL,
                lunchmoney_transaction_id INT ,
                date_created TEXT DEFAULT (datetime('now'))
            );"""
        )

    # Get list of know transaction IDs
    seen_transaction_ids: Union[None, List[str]] = None

    if db:
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

        if current_balance == 0 and not db:
            tran.set_tag("has_transactions", False)
            output("Your venmo balance is zero. Nothing to do")
            return

        output("Your balance is ${:,.2f}".format(current_balance / 100))

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
                    if transaction.id not in seen_transaction_ids:
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
            output("\ndry-run. Not initiating transfers")
            return

        # Do not cash out if
        if not args.allow_remaining and remaining_balance > 0:
            output("\nRemaining balance without --allow-remaining. Not initiating transfers")
            return

        # Do the transactions
        with start_span(op="initiate_transfer"):
            for transaction in income_transactions:
                venmo.transfer.initiate_transfer(amount=transaction.amount)

            if remaining_balance > 0:
                venmo.transfer.initiate_transfer(amount=remaining_balance)

        # Update seen expense transaction
        if db:
            query = """
            INSERT INTO seen_transactions
            (transaction_type, transaction_id, amount, note, target_actor)
            VALUES(?, ?, ?, ?, ?)
            """
            records = [
                *[
                    ("income", t.id, t.amount, t.note, t.payer.display_name)
                    for t in income_transactions
                ],
                *[
                    ("expense", t.id, t.amount, t.note, t.payee.display_name)
                    for t in expense_transactions
                ],
            ]
            cursor = db.cursor()
            cursor.executemany(query, records)
            db.commit()

        # Update lunchmoney transactions
        if db and args.lunchmoney_token:
            update_lunchmoney_transactions(
                db,
                args.lunchmoney_token,
                args.lunchmoney_category,
                output,
            )

        output("\nAll money transferred out!")
