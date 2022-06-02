## Venmo to Lunch Money

This is a small automation for syncing your Venmo transactions to [Lunch Money](https://my.lunchmoney.app/).

![Venmo transactions in Lunch Money](/screenshots/example_transaction.png?raw=true "Venmo Transactions in Lunch Money")

## Background

If you're like me, the worst part of any budgeting app is how it interacts with Venmo! A night out with friends where you all split the bill is suddenly a nightmare.

This tool erases this problem altogether! All you need to do is set this up to run regularly (e.g. via `cron` on your laptop whenever you login, or even remotely on a free heroku instance).

All of the transactions imported to Lunch Money from this tool will have the `Venmo API` tag so you can easily filter for them in Lunch Money.

## A note in idempotency

One huge pain in budgeting software is the fear of duplicate transactions. Luckily, this tool is _idempotent_, which means you can run it as many times as you'd like and you will _not_ introduce any duplicate transactions in Lunch Money 🎉.

This means you can run this as a cron script every 5 minutes, whenever you open your laptop, or even on a free Heroku instance for automagic syncing always :).

## Example

Here's an example of how to execute a dry run in a docker container to verify what _would_ be posted Lunch Money, without posting any actual data.

```
docker build . --tag venmo-to-lunchmoney && \
docker run venmo-to-lunchmoney \
--dry-run \
--days-lookback 60 \
--venmo-api-key "$VENMO_API_KEY" \
--lunchmoney-api-key "$LUNCH_MONEY_API_KEY"

[+] Building 7.6s (13/13) FINISHED
 => [internal] load build definition from Dockerfile                               0.0s
 ... (Boring Docker build logs)

[dry run]: Waiting 5 seconds before fetching Venmo transactions...
[dry run]: Waiting 5 seconds before fetching next page of Venmo transactions...
[dry run]: Waiting 5 seconds before fetching next page of Venmo transactions...
[dry run]: Finished fetching 81 transactions from Venmo.
[dry run]:
**Newest transaction:**
{
    "amount": 1500.0,
    "created_at": "2022-06-02 06:52:53",
    "id": "3551608897717469330",
    "note": "\ud83c\udf63",
    "payee": "Kahlil Oppenheimer",
    "payer": "Hannah Lynch",
    "transaction_type": "Income"
}
[dry run]:
**Oldest transaction:**
{
    "amount": -600.0,
    "created_at": "2022-04-03 01:42:01",
    "id": "3507965887474213405",
    "note": "Nachos (and Wi-Fi)",
    "payee": "Leah Lin",
    "payer": "Kahlil Oppenheimer",
    "transaction_type": "Expense"
}
[dry run]: Attempting to post 81 transactions to Lunch Money...
[dry run]: Dry run succeeded and did NOT post any actual data to Lunch Money!
```

I've even saved you a step and included the above as a bash script, so you can also just run:

```
$ ./execute.sh
```

Once you're ready to post real data, just remove the `--dry-run` parameter in the command above!

### Getting your Lunch Money API token

This is done easily in the Lunch Money app! Just go to:

```
Lunch Money dashboard > ⚙️ > Developers > Request New Access Token
```

### Getting your Venmo API token

\*\* IMPORTANT: This token is very sensitive as it has permissions to transfer money!. It also does NOT auto-expire. Never share this token with anyone. And never commit it to git or anywhere on the internet!

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

To expire your token (assuming the token is something like `a40fsdfhsfhdsfjhdkgljsdglkdsfj3j3i4349t34j7d`):

```
$ pdm run python
Python 3.9.6 (default, Aug 30 2021, 00:42:05)

>>> from venmo_api import Client
>>> client.log_out("Bearer a40fsdfhsfhdsfjhdkgljsdglkdsfj3j3i4349t34j7d")
```

## Forked from

This tool was originally forked from https://github.com/evanpurkhiser/venmo-auto-cashout, a tool that automates chunking up single venmo balances into individual pay out transactions. Huge props to that author (@evanpurkhiser) for laying down some inspiration for this tool!
