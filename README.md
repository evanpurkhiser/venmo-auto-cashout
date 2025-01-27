## Venmo Auto Cashout

This is a small tool for automatically cashing out your Venmo balance such that
each individual payment you receive will have an associated bank-transfer
generated.

```
$ venmo-auto-cashout --token=XXX --allow-remaining
Your balance is $50
There are 3 transactions to cash-out

 -> Transfer: $15.00 -- Mako (Dia beacon museum tickets)
 -> Transfer: $15.00 -- David (Dia beacon museum tickets)
 -> Transfer: $20.00 -- Randolf (Dinner)

All money transferred out!
```

This can be used as a cron script to automatically cash out your Venmo for you.

### Consistent tracking

By default the tool will only cashout amounts ammounts that add up to the most
recent transactions. This is useful when the script is running on a cron-job
and you want to be sure it never misses an individual payment cash out (This
can happen when the tool runs immeidatley after a payment is received, but
before the payment appears in the transaction list)

If you wish to cash-out everything use the `--allow-remaining` option.
Otherwise the tool will exit when there is a remainder.

```
$ venmo-auto-cashout --token=XXX --allow-remaining
Your balance is $39.95
There are 3 transactions to cash-out

 -> Transfer: $15.00 -- Mako (Dia beacon museum tickets)
 -> Transfer: $24.95 of remaining balance

All money transferred out!
```

### Lunchmoney integration

In addition to automatic-cashout, this script can also integrate with
[Lunchmoney](https://lunchmoney.app/).

The script will look for transactions in Lunch Money which are part of an
arbitrary Venmo category, these transactions will be matched against previously
tracked Venmo transactions by matching the exact amount.

The Lunch Money transaction will then be updated with the Payee and Note from
the Venmo transaction.

You will need to specify additional flags when running the script to do this.
It is also highly recommended that the script run on as a cron job in this case.

```
$ venmo-auto-cashout --token=XXX --lunchmoney-token=XXX --lunchmoney-category=z-venmo
Your balance is $0.00
Waiting 5 seconds before querying transactions...
There are 0 income transactions to cash-out
There are 1 expense transactions to track

 -> Expense: -$28.29 -- Randolf Tjandra (Volcano curry)

Lunch Money Updates: 1 / 1 transactions matched

 -> Randolf Tjandra (Volcano curry) → LM: 242330937

All money transferred out!
```

My main use for this is to be able to better balance my bank account by
associating Venmo transactions back to other charges in Lunchmoney. Typically
an incoming Venmo is a reimbursement for some other transaction that I covered
for friends. I split and then group the transaction that was to cover my
friends such that my categories reflect my "true spend" (e.g., I don't have a
bunch of \$100+ restaurants transactions)

### Getting your API token

First, you'll need to grab the [trusted device ID from a venmo login](https://github.com/mmohades/Venmo/issues/86). Assuming you have PDM setup you can run the following commands to retrieve your
token:

> [!IMPORTANT]
> You may disregard the `device-id`, we only need the token.

```
$ pdm run python
Python 3.9.6 (default, Aug 30 2021, 00:42:05)

>>> from venmo_api import Client
>>> Client.get_access_token(username='myemail@gmail.com', password='myPassword', device_id="trusted-device-id")

IMPORTANT: Take a note of your device-id to avoid 2-factor-authentication for your next login.
device-id: xxxx
IMPORTANT: Your Access Token will NEVER expire, unless you logout manually (client.log_out(token)).
Take a note of your token, so you don't have to login every time.

Successfully logged in. Note your token and device-id
access_token: xxxx
device-id: xxxx
```

### Running on a schedule

The docker container supports running this script on a schedule. Here's how

```shell
docker pull evanpurkhiser/venmo-auto-cashout:latest
docker run -d \
  -e VENMO_API_TOKEN= \
  -e TRANSACTION_DB=/data/transactions.db \
  -e LUNCHMONEY_TOKEN= \
  -e LUNCHMONEY_CATEGORY= \
  -e SCHEDULE="0 0 * * *" \
  -v /path/to/your/transactions.db:/data/transactions.db \
  --name venmo-auto-cashout \
  evanpurkhiser/venmo-auto-cashout:latest
```

Or, in docker compose form:

```yaml
version: '3'
services:
  venmo-auto-cashout:
    image: evanpurkhiser/venmo-auto-cashout:latest
    environment:
      - VENMO_API_TOKEN=
      - TRANSACTION_DB=/data/transactions.db
      - LUNCHMONEY_TOKEN=
      - LUNCHMONEY_CATEGORY=
      - SCHEDULE=0 0 * * *
    volumes:
      - transaction_data:/data/transactions.db
    restart: always
volumes:
  transaction_data:
```

### ENV Variables

You can also set the following ENV variables instead of passing them as flags:

```
export VENMO_API_TOKEN=
export TRANSACTION_DB=
export LUNCHMONEY_TOKEN=
export LUNCHMONEY_CATEGORY=
```