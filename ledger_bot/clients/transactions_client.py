"""A mixin for dealing with transactions."""

import logging
from typing import Any, Dict

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.commands_scheduled import cleanup
from ledger_bot.message_generators import (
    generate_transaction_status_message,
    send_message,
)
from ledger_bot.reactions import add_reaction, remove_reaction
from ledger_bot.reminder_manager import ReminderManager
from ledger_bot.services import Service
from ledger_bot.views import CreateReminderButton

from .extended_client import ExtendedClient

log = logging.getLogger(__name__)


class TransactionsClient(ExtendedClient):
    def __init__(
        self,
        config: Dict[str, Any],
        scheduler: AsyncIOScheduler,
        service: Service,
        reminders: ReminderManager,
        session_factory: async_sessionmaker[AsyncSession],
        **kwargs,
    ) -> None:
        self.config = config
        self.scheduler = scheduler
        self.service = service
        self.reminders = reminders
        self.session_factory = session_factory

        scheduler.add_job(
            func=cleanup,
            name="Cleanup",
            kwargs={"client": self, "service": self.service},
            trigger="cron",
            hour=config["run_cleanup_time"]["hour"],
            minute=config["run_cleanup_time"]["minute"],
            second=config["run_cleanup_time"]["second"],
            timezone="UTC",
        )
        super().__init__(
            config=config,
            scheduler=scheduler,
            service=service,
            session_factory=session_factory,
            **kwargs,
        )

    async def handle_transaction_reaction(
        self, payload: discord.RawReactionActionEvent
    ) -> bool:
        channel = await self.get_or_fetch_channel(payload.channel_id)
        reactor = payload.member

        # Repeating checks to deal with mypy warnings
        if reactor is None:
            log.debug("Payload contained no reactor. Ignoring payload.")
            return False

        if not isinstance(channel, discord.TextChannel):
            log.debug("Couldn't get channel information. Ignoring reaction.")
            return False

        # Check if valid reaction emoji
        if payload.emoji.name not in [
            self.config["emojis"]["approval"],
            self.config["emojis"]["cancel"],
            self.config["emojis"]["paid"],
            self.config["emojis"]["delivered"],
            self.config["emojis"]["reminder"],
        ]:
            return False

        # Check if in valid channel
        if (
            self.config["channels"].get("include")
            and channel.name not in self.config["channels"]["include"]
        ):
            log.debug(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Channel not included"
            )
            return False
        else:
            if channel.name in self.config["channels"].get("exclude", []):
                log.debug(
                    f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Channel excluded"
                )
                return False

        # Check if valid message
        target_transaction = (
            await self.service.transaction.get_transaction_by_bot_message_id(
                bot_message_id=int(payload.message_id),
                bot_message_service=self.service.bot_message,
            )
        )
        if target_transaction is None:
            log.debug(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Invalid target message"
            )
            return False

        # After this point all are checks are slow, so we add the reaction now.
        # The valid message check above is also pretty slow, but we'd then add the reaction to every message that received a valid reaction
        # So we add this after those checks
        await add_reaction(
            client=self,
            message_id=payload.message_id,
            reaction=self.config["emojis"]["thinking"],
            channel_obj=channel,
        )

        # Get buyer & seller discord.Member objects
        buyer = await self.service.member.get_member_from_record_id(
            target_transaction.buyer_id
        )
        if buyer is None:
            await remove_reaction(
                client=self,
                message_id=payload.message_id,
                reaction=self.config["emojis"]["thinking"],
                channel_obj=channel,
            )
            log.debug("No buyer found")
            return False
        buyer = await self.get_or_fetch_user(buyer.discord_id)

        seller = await self.service.member.get_member_from_record_id(
            target_transaction.seller_id
        )
        if seller is None:
            await remove_reaction(
                client=self,
                message_id=payload.message_id,
                reaction=self.config["emojis"]["thinking"],
                channel_obj=channel,
            )
            log.debug("No seller found")
            return False
        seller = await self.get_or_fetch_user(seller.discord_id)

        # Check if buyer or seller
        if reactor.id != buyer.id and reactor.id != seller.id:
            log.debug(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Reactor is neither buyer nor seller"
            )
            await remove_reaction(
                client=self,
                message_id=payload.message_id,
                reaction=self.config["emojis"]["thinking"],
            )
            return False

        # Process reaction
        log.info(
            f"Processing {payload.emoji.name} from {reactor.name} on message {payload.message_id}"
        )

        if payload.emoji.name == self.config["emojis"]["approval"]:
            # Approval
            log.info(
                f"Processing approval reaction from {reactor.name} on message {payload.message_id}"
            )

            processed_transaction = await self.service.transaction.approve_transaction(
                transaction=target_transaction, reactor=reactor
            )

            response_contents = await generate_transaction_status_message(
                transaction=processed_transaction,
                client=self,
                config=self.config,
                is_update=True,
            )

            await send_message(
                response_contents=response_contents,
                channel=channel,
                target_transaction=processed_transaction,
                previous_message_id=payload.message_id,
                service=self.service,
                config=self.config,
            )

        elif payload.emoji.name == self.config["emojis"]["paid"]:
            # Paid
            log.info(
                f"Processing payment reaction from {reactor.name} on message {payload.message_id}"
            )

            processed_transaction = (
                await self.service.transaction.mark_transaction_paid(
                    transaction=target_transaction, reactor=reactor
                )
            )

            response_contents = await generate_transaction_status_message(
                transaction=processed_transaction,
                client=self,
                config=self.config,
                is_update=True,
            )

            await send_message(
                response_contents=response_contents,
                channel=channel,
                target_transaction=processed_transaction,
                previous_message_id=payload.message_id,
                service=self.service,
                config=self.config,
            )

        elif payload.emoji.name == self.config["emojis"]["delivered"]:
            # Delivered
            log.info(
                f"Processing delivered reaction from {reactor.name} on message {payload.message_id}"
            )

            processed_transaction = (
                await self.service.transaction.mark_transaction_delivered(
                    transaction=target_transaction, reactor=reactor
                )
            )

            response_contents = await generate_transaction_status_message(
                transaction=processed_transaction,
                client=self,
                config=self.config,
                is_update=True,
            )

            await send_message(
                response_contents=response_contents,
                channel=channel,
                target_transaction=processed_transaction,
                previous_message_id=payload.message_id,
                service=self.service,
                config=self.config,
            )

        elif payload.emoji.name == self.config["emojis"]["cancel"]:
            # Cancelled
            log.info(
                f"Processing cancel reaction from {reactor.name} on message {payload.message_id}"
            )

            processed_transaction = await self.service.transaction.cancel_transaction(
                transaction=target_transaction, reactor=reactor
            )

            response_contents = await generate_transaction_status_message(
                transaction=processed_transaction,
                client=self,
                config=self.config,
                is_update=True,
            )

            await send_message(
                response_contents=response_contents,
                channel=channel,
                target_transaction=processed_transaction,
                previous_message_id=payload.message_id,
                service=self.service,
                config=self.config,
            )

        elif payload.emoji.name == self.config["emojis"]["reminder"]:
            # Watch
            log.info(
                f"Processing reminder reaction from {reactor.name} on message {payload.message_id}"
            )
            await reactor.send(
                content=f'Click here to add a reminder for "*{target_transaction.wine}*" from {buyer.mention} to {seller.mention} for £{target_transaction.price}',
                view=CreateReminderButton(
                    service=self.service,
                    transaction=target_transaction,
                    user=reactor,
                    reminders=self.reminders,
                ),
            )

        # Remove our thinking reaction
        await remove_reaction(
            client=self,
            message_id=payload.message_id,
            reaction=self.config["emojis"]["thinking"],
            channel_obj=channel,
        )

        log.info(f"Finished processing reaction {payload.emoji} from {reactor}")
        return True

    async def refresh_transaction(
        self, record_id: int, channel_id: int | None
    ) -> str | None:
        """Removes all existing messages for a given transaction, and creates a new message with the current status."""
        log.info(f"Refreshing transaction: {record_id}")

        # Get transaction record
        transaction = await self.service.transaction.get_transaction(
            record_id=record_id
        )

        if transaction is None:
            log.info(f"No transaction found with row_id {record_id}")
            return "No transaction found."

        log.debug(f"Transaction: {transaction}")

        # Get all existing bot_messages
        bot_messages = transaction.bot_messages

        # We overwrite this with the channel from the bot_message, if it's provided
        channel = (
            await self.get_or_fetch_channel(channel_id)
            if channel_id is not None
            else None
        )

        # Delete all previous bot messages, if they exist
        if bot_messages is not None:
            for bot_message in bot_messages:
                log.debug(f"Message: {bot_message}")

                try:
                    channel = await self.get_or_fetch_channel(bot_message.channel_id)

                    if isinstance(channel, discord.TextChannel):
                        message = await channel.fetch_message(bot_message.message_id)

                        log.info(f"Deleting message: {bot_message.message_id}")
                        await message.delete()

                        log.info(f"Deleting message record: {bot_message.id}")
                        await self.service.bot_message.delete_bot_message(bot_message)
                    else:
                        log.info(
                            f"Channel {channel} is not a TextChannel, so has no messages"
                        )
                except discord.errors.Forbidden as error:
                    log.error(
                        f"You don't have permission to delete the message: {error}"
                    )
                except discord.errors.NotFound as error:
                    log.error(f"The message has already been deleted: {error}")

                    log.info(f"Deleting message record: {bot_message.id}")
                    await self.service.bot_message.delete_bot_message(bot_message)
                except discord.errors.HTTPException as error:
                    log.error(f"An error occured deleting the message: {error}")

        if channel is None:
            return "I couldn't calculate which channel to post in. Please repeat the command specifying a channel id."

        log.info(
            f"Seller Discord ID: {transaction.seller.discord_id} / {type(transaction.seller.discord_id)}"
        )
        log.info(
            f"Buyer Discord ID: {transaction.buyer.discord_id} / {type(transaction.buyer.discord_id)}"
        )

        if transaction.seller.discord_id is None:
            log.warning("No Seller Discord ID specified. Skipping")
            return None

        if transaction.buyer.discord_id is None:
            log.warning("No Buyer Discord ID specified. Skipping")
            return None

        seller = await self.get_or_fetch_user(transaction.seller.discord_id)
        buyer = await self.get_or_fetch_user(transaction.buyer.discord_id)

        log.info(f"Seller: {seller} / {type(seller)}")
        log.info(f"Buyer: {buyer} / {type(buyer)}")

        # Post new message
        message_contents = await generate_transaction_status_message(
            transaction=transaction,
            client=self,
            config=self.config,
            is_update=True,
        )

        await send_message(
            response_contents=message_contents,
            channel=channel,
            target_transaction=transaction,
            previous_message_id=None,
            service=self.service,
            config=self.config,
        )

        return "Successfully refreshed message."
