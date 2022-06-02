import json

from datetime import datetime
from enum import Enum
from pprint import pprint

class TransactionType(str, Enum):
    Income = 'Income'
    Expense = 'Expense'

# Common representation of a transaction between Venmo and Lunch Money.
class Transaction:
    def __init__(
        self, 
        id: str,
        transaction_type: TransactionType,
        created_at: datetime,
        payer: str,
        payee: str,
        amount: int, # "Minor units" aka 1234 == $12.34
        note: str,
    ):
        self.id = id
        self.transaction_type = transaction_type
        self.created_at = created_at
        self.payer = payer
        self.payee = payee
        self.amount = amount
        self.note = note
    
    def __str__(self) -> str:
        return json.dumps(vars(self), indent=4, sort_keys=True, default=str)

    def other_person(self) -> str:
        if self.transaction_type is TransactionType.Income:
            return self.payer
        else:
            return self.payee