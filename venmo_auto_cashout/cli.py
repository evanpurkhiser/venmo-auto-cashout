import argparse
from os import getenv
from typing import List

from venmo_api import Client, Transaction


def run_cli():
    parser = argparse.ArgumentParser(
        description="Automatically cash-out your Venmo balance as individual transfers"
    )

    parser.add_argument(
        "--token",
        type=str,
        default=getenv("VENMO_API_TOKEN"),
        required=not getenv("VENMO_API_TOKEN"),
        help="Your venmo API token",
    )
    parser.add_argument(
        "--quiet", action=argparse.BooleanOptionalAction, help="Do not produce any output"
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="Do not actually initiate bank transfers",
    )

    args = parser.parse_args()

    def output(msg: str):
        if not args.quiet:
            print(msg)

    # Venmo API client
    venmo = Client(access_token=args.token)

    me = venmo.my_profile()
    if not me:
        raise Exception("Failed to load Venmo profile")

    current_balance: int = me.balance

    if current_balance == 0:
        output("Your venmo balance is zero. Nothing to do")
        return

    # XXX: There may be some leftover ammount if the transactions do not match
    # up exactly to the current account balance.
    remaining_balance = current_balance
    eligable_transactions: List[Transaction] = []

    transactions = venmo.user.get_user_transactions(user=me)
    if transactions is None:
        raise Exception("Failed to load trnasctions")

    # Produce a list of eligible transactions
    for transaction in transactions:
        # We're only interested in charge transactions
        if transaction.payment_type != "charge":
            continue

        # There are no more eligable transactions once we have accounted for
        # all of our account balance
        if transaction.amount > remaining_balance:
            break

        remaining_balance = remaining_balance - transaction.amount
        eligable_transactions.append(transaction)

    # Show some details about what we're about to do
    output("Your balance is ${:,.2f}".format(current_balance / 100))
    output("There are {} transactions to cash-out".format(len(eligable_transactions)))

    if len(eligable_transactions) > 0:
        output("")

    for transaction in eligable_transactions:
        output(
            " -> Transfer: ${price:,.2f} -- {name} ({note})".format(
                name=transaction.target.display_name,
                price=transaction.amount / 100,
                note=transaction.note,
            )
        )

    if remaining_balance > 0:
        output(" -> Transfer: ${:,.2f} of remaining balance".format(remaining_balance / 100))

    # Nothing left to do in dry-run mode
    if args.dry_run:
        output("\ndry-run -- Not initiating transfers")
        return

    # Do the transactions
    for transaction in eligable_transactions:
        venmo.transfer.initiate_transfer(amount=transaction.amount)

    if remaining_balance > 0:
        venmo.transfer.initiate_transfer(amount=remaining_balance)

    output("\nAll money transfered out!")
