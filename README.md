## Venmo Auto Cashout

This is a small tool for automatically cashing out your venmo balance such that
each individual payment you recieve will have an associated bank-transfer
generated.

This can be used as a cron script to automatically cash out your venmo for you.

My main use for this is to be able to better balance my bank account by being
able to associate venmo transactions back to other charges in my personal
accounting software.

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
