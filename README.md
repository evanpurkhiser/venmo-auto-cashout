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

You may pass your [Lunchmoney](https://lunchmoney.app/) credentials as well to
have the script generate single-shot rules that will match the transaction and
apply the note from Venmo to the Lunchmoney transaction.

My main use for this is to be able to better balance my bank account by
associating Venmo transactions back to other charges in Lunchmoney. Typically
an incoming Venmo is a reimbursement for some other tranaction that I covered
for friends. I split the transaction that was to cover my friends such that the
charges net zero.

### Getting your API token

Assuming you have PDM setup you can run the following commands to retrieve your
token:

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
