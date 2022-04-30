from typing import List
from requests.sessions import Session
import pyotp


from venmo_api import Transaction, User

LUNCHMONEY_API = "https://api.lunchmoney.app"

# Payee to match income
PAYEE_CREDIT = "Venmo Received"

# Payee to match expenses
PAYEE_EXPENSE = "Venmo Payed"

# The priority to make the rule on lunchmoney
RULE_PRIORITY = 5

# The tag ID to associate transactions that were recieved (credited)
RULE_VENMO_CREDIT = 31644

# The tag ID to associate transactions where it was an expense
RULE_VENMO_EXPENSE = 33232


def generate_rules(
    transactions: List[Transaction], me: User, email: str, password: str, otp_secret: str = None
):
    """
    Generates rules in lunchmoney.app for each Venmo transaction.

    The rules will match the exact amount of the Venmo transaction and will set
    the note from the Venmo transaction.
    """
    session = Session()

    # Authenticate username/password
    session.post(f"{LUNCHMONEY_API}/auth/login", json={"username": email, "password": password})

    # Authenticate with TOTP if set
    if otp_secret is not None:
        totp = pyotp.TOTP(otp_secret)
        totp_body = {
            "code": totp.now(),
            "remember": False,
            "test": False,
        }
        session.post(
            f"{LUNCHMONEY_API}/auth/totp/verify",
            json=totp_body,
        )

    # Create rules
    for transaction in transactions:
        is_expense = transaction.payee.username != me.username
        target_actor = transaction.payee if is_expense else transaction.payer

        session.post(
            f"{LUNCHMONEY_API}/rules",
            json={
                "conditions": {
                    "on_plaid": True,
                    "on_api": True,
                    "on_csv": True,
                    "amount": {
                        "match": "exactly",
                        "type": "expenses" if is_expense else "credits",
                        "value_1": transaction.amount / 100 * (1 if is_expense else -1),
                        "currency": "usd",
                        "value_2": None,
                    },
                    "payee": {
                        "name": PAYEE_EXPENSE if is_expense else PAYEE_CREDIT,
                        "match": "exact",
                    },
                    "priority": f"{RULE_PRIORITY}",
                },
                "actions": {
                    "notes": f"{target_actor.first_name}: {transaction.note}",
                    "tags": [RULE_VENMO_EXPENSE if is_expense else RULE_VENMO_CREDIT],
                    "stop_processing_others": True,
                    "one_time_rule": True,
                },
            },
        )
