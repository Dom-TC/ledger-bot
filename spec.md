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

## New Reminder Flow

1. User reacts to post
2. Show modal asking for days / hours / statys
3. Store reminder

## Reminders ToDo.

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

## Schema

MEMBERS:

- id iNT AUTOINCREMENT
- discord_id INT UNIQUE
- username TEXT
- nickname TEXT

EVENTS

- id INT AUTOINCREMENT
- event_name TEXT
- event_description TEXT
- event_date TEXT (ISO 8601)
- event_location TEXT
- event_host FK members.id
- max_guests INT
- deposit_value INT
- creation_date TEXT (ISO 8601)
- channel_id INT
- bot_id TEXT

EVENT_MEMBERS

- id INT AUTOINCREMENT
- event_id FK events.id
- member_id FK members.id
- guests INT
- has_paid INT (bool)
- status TEXT (enum - host, confirmed, waitlist, cancelled)
- joined_date TEXT (ISO 8601)
- paid_date TEXT (ISO 8601)
- bot_ID TEXT

EVENT_WINES

- id INT AUTOINCREMENT
- event_id FK events.id
- member_id FK members.id
- wine TEXT
- category TEXT (enum - sparkling, white, red, sweet, other)
- date_added TEXT (ISO 8601)
- bot_ID TEXT

## Services

MEMBER

- get_or_add_member - Either get an existing member record or add the member to the database and return the record
- find_member_by_discord_id - Find a member by their discord id
- list_all_members - List all members
- delete_member - Delete the specified member
- set_dietry_requirement - Set the diatry requirement data

TRANSACTION

- get_transaction - Get a transaction by it's record id
- get_users_transaction - Get all transactions for a specific user
- get_completed_transaction
- save_transaction - If id is none, add new transaction, else update existing one
- list_all_transactions - List all transactions
- delete_transaction - Delete the specified transaction
- approve_transaction
- cancel_transaction
- mark_transaction_delivered
- mark_transaction_paid
- refresh_transaction

BOT_MESSAGE

- add_bot_message
- find_bot_message_by_message_id
- delete_bot_message
- refresh_bot_message - Remove old bot messages and store new one

REMINDERS

- get_reminder
- save_reminder - If id is none, add new reminder, else update existing one
- list_all_reminders
- delete_reminder

REACTION_ROLE

- get_reaction_role_by_role_id
- get_reaction_role_by_reaction
- add_reaction_role
- delete_reaction_role
- list_watched_message_ids

## Storage

MEMBER

- get_membe
- add_membe
- list_members
- delete_member
- update_member

TRANSACTION

- get_transaction
- add_transaction
- list_transactions
- delete_transaction
- update_transaction

BOT_MESSAGE

- get_bot_message
- add_bot_message
- list_bot_messages
- delete_bot_message

REMINDERS

- get_reminder
- add_reminder
- list_reminders
- delete_reminder
- update_reminder

REACTIONROLE

- get_reaction_role
- add_reaction_role
- list_reeaction_roles
- delete_reaction_role
- update_reaction_role
- list_watched_message_ids

## TODO

2. Create services

- transactions
- bot_messages
- reminders
- reaction_roles

3. Move `process_transaction/send_message.py` to client
4. Remove other `process_transaction` functions (all should be in service)
5. Update all instances to use new client/service/storage classes.
6. Implement events system
