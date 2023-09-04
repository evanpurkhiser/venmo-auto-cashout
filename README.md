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

In addition to automatic-cashout, this script can also integrate with
[Lunchmoney](https://lunchmoney.app/).

The script will look for transactions in Lunch Money which are part of an
arbitrary Venmo category, these transactions will be matched against previously
tracked Venmo transactions by matching the exact amount.

The Lunch Money transaction will then be updated with the Payee and Note from
the Venmo transction.

You will need to specify additional flags when running the script to do this.
It is also highly recommended that the script run on as a cron job in this case.

```
$ venmo-auto-cashout --token=XXX --lunchmoney-token=XXX -lunchmoney-group=z-venmo
Your balance is $0.00
Waiting 5 seconds before querying transactions...
There are 0 income transactions to cash-out
There are 1 expense transactions to track

 -> Expense: -$28.29 -- Randolf Tjandra (Volcano curry)

Lunch Money Updates: 1 / 1 transactions matched

 -> Randolf Tjandra (Volcano curry) → LM: 242330937

All money transfered out!
```

My main use for this is to be able to better balance my bank account by
associating Venmo transactions back to other charges in Lunchmoney. Typically
an incoming Venmo is a reimbursement for some other transaction that I covered
for friends. I split and then group the transaction that was to cover my
friends such that my categories reflect my "true spend" (e.g., I don't have a
bunch of \$100+ restaurants transactions)

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
