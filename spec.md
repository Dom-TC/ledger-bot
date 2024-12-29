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

`!list` - List all open transactions, linking to each <bot_post>
`!list sales` - List all open sales, linking to each <bot_post>
`!list purchases` - List all open purchases, linking to each <bot_post>
`!help` - Returns the help documentation
`!version` - Returns the version / bot_id of the running bot

## Bot Post Format

```
**@<seller> sold <wine_name> to @<buyer>**
Price: <price>
<sale_link>

**Status:**
<approved_emoji> Approved:
<paid_emoji> Paid:
<delivered_emoji> Delivered:
```

## New Reminder Flow

1. User reacts to post
2. Show modal asking for days / hours / statys
3. Store reminder

## Reminders ToDo

1. Create New Reminder
2. Add jobs for each reminder
3. Process reminder at correct time
4. DM command to list reminders
5. DM command to remove reminders

## Reaction Roles

- Get watched message IDs
  - Daily
  - DM command
  - Whenever a new role is added
- Assign Role
  - If message ID and reaction are valid, assign the user the appropriate role
- Add Role
  - Admin only command

## Events Spec

Commands:

- Create Event
  - Name: string
  - Date: datetime
  - Max Guests: int, optional
  - Location: str, optional
    1. Create Event object
    2. Create private channel with host.
        - Named: `<name>-<date>-<location>`
    3. Create buttons in channel:
        - Set Max Guests
        - Set Menu Option
        - Set Deposit
    4. Create Discord Event?

- Join Event
- Leave Event
- Add Wine
- Remove Wine
- Get Event Details
- List Events
- Cancel Event
- Mark Deposit Paid
- Manage Event
  - Change Event Date
  - Set Deposit Amount
  - Add Menu Choice
  - Select Menu Choice
  - Change Max Guests
  - Chase Deposits
- Archive Event

Event Table Schema:

- Row ID: int, auto-increment
- Name: string
- Host: Member Record, single record
- Max Guests: int
- Guests: Member Record, multiple records
- Event Date: datetime
- Channel ID: str
- Bot ID: string

Event Wines Table Schema:

- Row ID: int, auto-increment
- Event ID: Event Record, single record
- Member:  Member Record, single record
- Wine: str
- Bot ID: string

Event Deposits Table Scema

- Row ID: int, auto-increment
- Event ID: Event Record, single record
- Member:  Member Record, single record
- Paid: bool
- Confirmed Paid: bool
- Bot ID: string
