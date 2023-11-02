"""The LedgerBot class is the actual implimentation of the Discord bot.  Extends discord.Client."""

import datetime
import logging

import discord
from discord import app_commands
from message_generator import generate_transaction_status_message
from models import AirTableError
from process_dm import is_dm, process_dm

log = logging.getLogger(__name__)


class LedgerBot(discord.Client):
    """
    The main bot class.

    Paramaters
    ----------
    config : dict
        The bots config options

    storage : storage.AirtableStorage
        The AirTable storage

    guild : discord.Object
        The Discord Server the bot is running in

    """

    def __init__(self, config: dict, storage):
        self.config = config
        self.storage = storage
        self.guild = discord.Object(id=self.config["guild"])

        log.info(f"Set guild: {self.config['guild']}")
        log.info(f"Watching channels: {self.config['channels']}")

        intents = discord.Intents(
            messages=True, guilds=True, reactions=True, message_content=True
        )

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        log.info(f"We have logged in as {self.user}")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=self.config["watching_status"],
            )
        )

        log.info("Building slash commands")
        await self.tree.sync(guild=self.guild)

    async def on_message(self, message):
        # Process DMs
        if is_dm(message):
            await process_dm(self, message)
            return

        channel_name = message.channel.name

        if (
            self.config["channels"].get("include")
            and channel_name not in self.config["channels"]["include"]
        ):
            return
        else:
            if channel_name in self.config["channels"].get("exclude", []):
                return

        if message.content == "add_member":
            log.debug(f"Adding member: {message.author}")
            await self.storage.get_or_add_member(message.author)

    async def on_raw_reaction_add(self, payload):
        # Check if valid reaction emoji
        if payload.emoji.name not in [
            self.config["emojis"]["approval"],
            self.config["emojis"]["paid"],
            self.config["emojis"]["delivered"],
        ]:
            return

        channel = self.get_channel(payload.channel_id)
        reactor = payload.member

        # Check if in valid channel
        if (
            self.config["channels"].get("include")
            and channel.name not in self.config["channels"]["include"]
        ):
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Channel not included"
            )
            return
        else:
            if channel.name in self.config["channels"].get("exclude", []):
                log.info(
                    f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Channel excluded"
                )
                return

        # Check if valid message
        target_transaction = await self.storage.find_transaction_by_bot_message_id(
            payload.message_id
        )
        if target_transaction is None:
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Invalid target message"
            )
            return

        # Get buyer & seller discord.Member objects
        buyer_id = await self.storage.get_member_from_record_id(
            target_transaction.buyer_id
        )
        buyer = await self.fetch_user(buyer_id.discord_id)
        seller_id = await self.storage.get_member_from_record_id(
            target_transaction.seller_id
        )
        seller = await self.fetch_user(seller_id.discord_id)

        # Check if buyer or seller
        if reactor.id != buyer.id and reactor.id != seller.id:
            log.info(
                f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Reactor is neither buyer nor seller"
            )
            return

        # Process reaction
        log.info(
            f"Processing {payload.emoji.name} from {reactor.name} on message {payload.message_id}"
        )

        if payload.emoji.name == self.config["emojis"]["approval"]:
            # Approval
            if reactor.id != buyer.id:
                log.info(
                    f"Ignoring {payload.emoji.name} from {reactor.name} on message {payload.message_id} in {channel.name} - Reactor is not the buyer"
                )
                return

            if target_transaction.sale_approved:
                log.info(
                    f"Ignoring approval on transaction {target_transaction.row_id}. Transaction already approved"
                )
                return

            log.info(f"Approving transaction {target_transaction.row_id}")

            target_transaction.sale_approved = True
            target_transaction.approved_date = datetime.datetime.utcnow().isoformat()
            transaction_fields = ["sale_approved", "approved_date"]
            await self.storage.save_transaction(
                transaction=target_transaction, fields=transaction_fields
            )

            response_contents = generate_transaction_status_message(
                seller=seller,
                buyer=buyer,
                wine_name=target_transaction.wine,
                wine_price=target_transaction.price,
                config=self.config,
                is_update=True,
                is_approved=True,
            )

            try:
                sent_message = await channel.send(response_contents)
                await self.storage.record_bot_message(
                    message=sent_message, transaction=target_transaction
                )

            except discord.HTTPException as error:
                log.error(f"An error occured sending the message: {error}")
            except discord.Forbidden as error:
                log.error(f"You don't have permission to send to that channel: {error}")
            except AirTableError as error:
                log.error(f"An error occured storing the content in AirTable: {error}")

            if self.config["delete_previous_bot_messages"]:
                log.info("delete_previous_bot_messages is true")
                log.info(f"Removing bot_message {payload.message_id}")
                old_message = await channel.fetch_message(payload.message_id)

                try:
                    await old_message.delete()
                    await self.storage.delete_bot_message(
                        await self.storage(payload.message_id)
                    )
                except discord.Forbidden as error:
                    log.error(
                        f"You don't have permission to send to that channel: {error}"
                    )
                except discord.NotFound as error:
                    log.error(f"The message has already been deleted: {error}")
                except discord.HTTPException as error:
                    log.error(f"An error occured deleting the message: {error}")

    async def on_disconnect(self):
        log.warning("Bot disconnected")
