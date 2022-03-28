## Venmo Auto Cashout

This is a small tool for automatically cashing out your Venmo balance such that
each individual payment you receive will have an associated bank-transfer
generated.

This can be used as a cron script to automatically cash out your Venmo for you.

You may pass your [Lunchmoney](https://lunchmoney.app/) credentials as well to
have the script generate single-shot rules that will match the transaction and
apply the note from Venmo to the Lunchmoney transaction.

My main use for this is to be able to better balance my bank account by being
associating Venmo transactions back to other charges in Lunchmoney. This
way I can split the charges (such as a restraint bill I covered, but split
with friends) and group them with the Venmo reimbursement.

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
