from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, List, Literal, Tuple
from lunchable import LunchMoney

from sqlite3 import Connection

from lunchable.models.transactions import TransactionObject, TransactionUpdateObject

# How many days back will we try and look for matching transactions? Anything
# older will be ignored forever
CUTOFF_DAYS = 30


def update_lunchmoney_transactions(
    db: Connection,
    token: str,
    category_name: str,
    output: Callable[[str], None],
):
    """
    Updates lunch money transactions with details from previously tracked venmo
    transactions. Works for both incoming and outgoing venmos.

    This is done by looking up Lunch Money transactions in the provided
    `category_name`. This category should be exclusive for venmo transactions,
    usually by setting up a Lunch Money rule to place venmo income / expenses
    into it. These transactions will then be matched against venmo transacitons
    that have not already had a lunchmoney_transaction_id associated to them in
    the database.
    """
    lunch = LunchMoney(access_token=token)

    try:
        category = next(c for c in lunch.get_categories() if c.name == category_name)
    except StopIteration:
        # TODO: What kind of error to show?
        output(f"xx: Cannot find Lunch Money category {category_name}")
        return

    # Find lunch money transactiosn that haven't been updated
    lm_transactions = [
        transaction
        for transaction in lunch.get_transactions(
            category_id=category.id,
            start_date=datetime.now() - timedelta(days=CUTOFF_DAYS),
            end_date=datetime.now(),
        )
        if
        # Ignore grouped transactions
        transaction.group_id is None and
        # Transactions with notes have already been updated
        transaction.notes is None
    ]

    @dataclass
    class VenmoRecord:
        id: int
        transaction_type: Literal["expense"] | Literal["income"]
        amount: int
        note: str
        target_actor: str

    columns = [f.name for f in fields(VenmoRecord)]

    # Find transactions that we haven't associated a lunch money transaction,
    # order by rescency so older transactions that were never correctly associated
    cursor = db.cursor()
    cursor.execute(
        f"""
        SELECT {",".join(columns)}
        FROM seen_transactions
        WHERE
            lunchmoney_transaction_id is NULL AND
            date_created < date('now', '-{CUTOFF_DAYS} day')
        ORDER BY date_created DESC"""
    )
    venmo_transactions = [VenmoRecord(*row) for row in cursor.fetchall()]

    # Track how many transactions we were able to match
    matched_transactions: List[Tuple[VenmoRecord, TransactionObject]] = []

    # Update lunch money and venmo transaction records
    for lm_txn in lm_transactions:
        transaction_type = "expense" if lm_txn.amount > 0 else "income"
        amount = int(Decimal(str(abs(lm_txn.amount))) * 100)

        try:
            matching_venmo = next(
                venmo_txn
                for venmo_txn in venmo_transactions
                if venmo_txn.transaction_type == transaction_type and venmo_txn.amount == amount
            )
        except StopIteration:
            # This can happen when a lunchmoney venmo transaction exists, but
            # there is no associated venmo transaction.
            #
            # This should basically never happen, but we may want to record
            # something when it does.
            continue

        matched_transactions.append((matching_venmo, lm_txn))

        # Update transaction in lunch money
        update = TransactionUpdateObject(
            payee=matching_venmo.target_actor,
            notes=matching_venmo.note,
        )
        lunch.update_transaction(lm_txn.id, update)

        # Record lunch money transaction ID
        cursor = db.cursor()
        cursor.execute(
            """
            UPDATE seen_transactions SET lunchmoney_transaction_id=? WHERE id=?
            """,
            (lm_txn.id, matching_venmo.id),
        )
        db.commit()

    count = f"{len(matched_transactions)} / {len(lm_transactions)}"
    output("")
    output(f"Lunch Money Updates: {count} transactions matched")

    if len(matched_transactions) > 0:
        output("")

    for venmo_txn, lm_txn in matched_transactions:
        output(f" -> {venmo_txn.target_actor} ({venmo_txn.note}) → LM: {lm_txn.id}")
