import sqlite3
import venmo_api

from datetime import datetime
from time import sleep
from typing import Callable
from venmo_auto_cashout.transaction import Transaction, TransactionType

# Loads all Venmo transactions between the given start_time (inclusive) to the
# given end time (exclusive) and returns them as Transaction objects (see
# transaction.py).
def load_venmo_transactions(
    api_key: str,
    start_time: datetime,
    end_time: datetime,
    log: Callable[[str], None],
) -> list[Transaction]:
    venmo = venmo_api.Client(access_token=api_key)
    me : venmo_api.User = venmo.my_profile()
    if not me:
        raise Exception("Failed to load Venmo profile")

    return _paginated_load_transactions(venmo, me, start_time, end_time, log)

def _paginated_load_transactions(
    venmo: venmo_api.Client,
    me: venmo_api.User,
    start_time: datetime,
    end_time: datetime,
    log: Callable[[str], None],
) -> list[Transaction]:
    log("Waiting 5 seconds before fetching Venmo transactions...")
    sleep(5.0)
    transactions = []
    next_page = venmo.user.get_user_transactions(user=me)
    while next_page:
        for raw_transaction in next_page:
            transaction = _to_transaction(raw_transaction, me)
            # Once we've gone far enough back, no need to paginate anymore!
            if transaction.created_at < start_time:
                return transactions
            if transaction.created_at < end_time:
                transactions.append(transaction)
        log("Waiting 5 seconds before fetching next page of Venmo transactions...")
        sleep(5.0)
        next_page = next_page.get_next_page()
    return transactions

def _to_transaction(
    venmo_transaction: venmo_api.Transaction,
    me: venmo_api.User,
) -> Transaction:
    is_income = venmo_transaction.payee.username == me.username
    transaction_type = TransactionType.Income if is_income else TransactionType.Expense
    sign = 1.0 if is_income else -1.0
    amount = sign * venmo_transaction.amount
    return Transaction(
        id = venmo_transaction.id,
        transaction_type=transaction_type,
        created_at = datetime.fromtimestamp(venmo_transaction.date_created),
        payer = venmo_transaction.payer.display_name,
        payee = venmo_transaction.payee.display_name,
        amount = amount,
        note = venmo_transaction.note,
    )
