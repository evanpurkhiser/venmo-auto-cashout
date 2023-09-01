## Venmo Auto Cashout

This is a small tool for automatically cashing out your Venmo balance such that
each individual payment you receive will have an associated bank-transfer
generated.

```
$ venmo-auto-cashout --token=XXX
Your balance is $74.95
There are 3 transactions to cash-out

 -> Transfer: $15.00 -- Mako (Dia beacon museum tickets)
 -> Transfer: $15.00 -- David (Dia beacon museum tickets)
 -> Transfer: $20.00 -- Randolf (Dinner)
 -> Transfer: $24.95 of remaining balance

All money transfered out!
```

This can be used as a cron script to automatically cash out your Venmo for you.

### Lunchmoney integration

> [!NOTE]
> I am currently re-writing lunch money support, this does not currently apply.

In addition to automatic-cashout, this script can also integrate with
[Lunchmoney](https://lunchmoney.app/) in the following two ways:

- **Income**: Any time a transaction is cashed out, a [Lunchmoney
  rule](https://support.lunchmoney.app/setup/rules) will be created that
  matches the exact amount, and will attach the transaction note from Venmo as
  a note on the matching Lunchmoney transaction. A tag will also be assigned
  to help denote new Venmo charges. The rule is single use, so after the
  matching transaction posts to your account the rule will go away.

  NOTE: Currently the tag ID and Payee name are hardcoded in lunchmoney.py,
  you may need to modify these for your use-case.

- **Expenses**: The script can track and create Lunchmoney rules for _sent_
  transactions as well. In this case a rule is created matching the exact
  expense amount.

  For this feature to work you **MUST** specify the `transaction-db` option,
  which maintains state about which expense transactions have been seen, so
  the script knows when new expenses appear.

My main use for this is to be able to better balance my bank account by
associating Venmo transactions back to other charges in Lunchmoney. Typically
an incoming Venmo is a reimbursement for some other transaction that I covered
for friends. I split the transaction that was to cover my friends such that my
categories reflect my "true spend" (e.g., I don't have a bunch of \$100+
restaurants transactions)

### Getting your API token

Assuming you have PDM setup you can run the following commands to retrieve your
token:

> [!IMPORTANT]
> You may disregard the `device-id`, we only need the token.

```
$ pdm run python
Python 3.9.6 (default, Aug 30 2021, 00:42:05)

>>> from venmo_api import Client
>>> Client.get_access_token(username='myemail@gmail.com', password='myPassword')

IMPORTANT: Take a note of your device-id to avoid 2-factor-authentication for your next login.
device-id: xxxx
IMPORTANT: Your Access Token will NEVER expire, unless you logout manually (client.log_out(token)).
Take a note of your token, so you don't have to login every time.

Successfully logged in. Note your token and device-id
access_token: xxxx
device-id: xxxx
```
