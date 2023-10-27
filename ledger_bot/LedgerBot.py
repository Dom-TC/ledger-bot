"""The LedgerBot class is the actual implimentation of the Discord bot.  Extends discord.Client."""

import logging

import discord

log = logging.getLogger(__name__)


class LedgerBot(discord.Client):
    def __init__(self, config: dict, storage):
        self.config = config
        self.storage = storage

        log.debug("Watching channels: %s", self.config["channels"])

        intents = discord.Intents(
            messages=True, guilds=True, reactions=True, message_content=True
        )
        super().__init__(intents=intents)

    async def on_ready(self):
        log.info(f"We have logged in as {self.user}")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=self.config["watching_status"],
            )
        )

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

        log.debug(f"Message from {message.author}: {message.content}")

        if message.content == "add_member":
            log.debug(f"Adding member: {message.author}")
            await self.storage.get_or_add_member(message.author)

    async def on_disconnect(self):
        log.warning("Bot disconnected")
