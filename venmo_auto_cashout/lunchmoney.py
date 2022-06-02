from lunchable import LunchMoney, TransactionInsertObject
from typing import Callable
from venmo_auto_cashout.transaction import Transaction

# Posts the given transactions to Lunch Money and returns a list of LunchMoney
# transaction IDs of the successful posts.  Duplicate transactions will be
# omitted from the returned list.
def post_transactions_to_lunchmoney(
    api_key: str,
    log: Callable[[str], None],
    transactions: list[Transaction],
) -> list[str]:
    lunchmoney_transactions = list(map(to_lunchmoney_transaction, transactions))

    lunch = LunchMoney(access_token=api_key)
    return lunch.insert_transactions(
        transactions = lunchmoney_transactions,
        debit_as_negative = True,
    )

def to_lunchmoney_transaction(transaction : Transaction) -> TransactionInsertObject:
    note = f"{transaction.other_person()}: {transaction.note}"
    return TransactionInsertObject(
        amount = transaction.amount / 100.0,
        date = transaction.created_at.date().isoformat(),
        external_id = transaction.id,
        notes = note,
        payee = transaction.payee,
        tags = ['Venmo API']
    )