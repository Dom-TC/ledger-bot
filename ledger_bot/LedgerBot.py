"""The LedgerBot class is the actual implimentation of the Discord bot.  Extends discord.Client."""

import logging

import discord
from discord import app_commands

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

    async def on_disconnect(self):
        log.warning("Bot disconnected")
