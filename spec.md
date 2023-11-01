# Spec

e.g. !addsale (or similar) [wine_name] [buyer] [price]
!delivered [pid] -> validate if you are the seller for said wine
!paid [pid] -> validate if you are the seller or buyer for said wine
!cancel [pid] -> only seller can cancel
!list -> show transactions you are still not delivered or not paid on

it may (though perhaps over complicating things) be also useful to store like, paid_timestamp, delivered_timestamp, cancel, cancelled_timestamp, but I'm a bit less fussed about that right now albeit appreciate its probably better to get that right up front rather than retrofit

## User Flows

### List wine for sale

seller: `/list <wine_name> <buyer> <price>`
ledger_bot: Add details to AirTable
ledger_bot: Post: "<sale_details> / Approved: NO @<buyer> please approve this sale by reacting with <approval_emoji>. / Paid: No, waiting on <paid_enoji>. / Delivered: No, waiting on <delivered_emoji>.
buyer: Reacts to ledger_bot with <approval_emoji>
ledger_bot: Set <sale_approved> to `TRUE`
ledger_bot: Update post: […] Approved: Yes, on <approved_date>. […]"

### Mark wine as paid

EITHER: buyer or seller (replying to original sale): /paid
OR: buyer or seller reacts to <bot_post> with <paid_emoji>
ledger_bot: Post "@<buyer> (or seller), @<seller> has marked this as paid. Please react with <paid_emoji> to approve.
buyer: Reacts to post
ledger_bot: Deletes previous <bot_post>, updates AirTable, creates new <bot_post>

### Mark wine as delivered

EITHER: buyer or seller (replying to original sale): /delivered
OR: buyer or seller reacts to <bot_post> with <delivered_emoji>
ledger_bot: Post "@<buyer> (or seller), @<seller> has marked this as delivered. Please react with <delivered_emoji> to approve.
buyer: Reacts to post
ledger_bot: Deletes previous <bot_post>, updates AirTable, creates new <bot_post>

### Cancel

Seller (replying to original sale): /cancel
ledger_bot: Deletes previous <bot_post>, updates AirTable, creates new <bot_post>

## DM Commands

list - List all open transactions, linking to each <bot_post>
list sales - List all open sales, linking to each <bot_post>
list purchases - List all open purchases, linking to each <bot_post>

## Bot Post Format:

```
**@<seller> sold <wine_name> to @<buyer>**
Price: <price>
<sale_link>

**Status:**
<approved_emoji> Approved:
<paid_emoji> Paid:
<delivered_emoji> Delivered:
```
