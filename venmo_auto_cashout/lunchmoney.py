from typing import List
from requests.sessions import Session
import pyotp


from venmo_api import Transaction

LUNCHMONEY_API = "https://api.lunchmoney.app"


# The name of the transaction on lunchmoney for Venmos
PAYEE_MATCH = "Venmo Received"


# The priority to make the rule on lunchmoney
RULE_PRIORITY = 5


# The tag ID to associate to the transaction
RULE_VENMO_TAG_ID = 31644


def generate_rules(
    transactions: List[Transaction], email: str, password: str, otp_secret: str = None
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
        session.post(
            f"{LUNCHMONEY_API}/rules",
            json={
                "conditions": {
                    "on_plaid": True,
                    "on_api": True,
                    "on_csv": True,
                    "amount": {
                        "match": "exactly",
                        "type": "credits",
                        "value_1": transaction.amount / 100 * -1,
                        "currency": "usd",
                        "value_2": None,
                    },
                    "payee": {"name": PAYEE_MATCH, "match": "exact"},
                    "priority": f"{RULE_PRIORITY}",
                },
                "actions": {
                    "notes": transaction.note,
                    "tags": [RULE_VENMO_TAG_ID],
                    "stop_processing_others": True,
                    "one_time_rule": True,
                },
            },
        )
