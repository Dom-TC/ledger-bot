import asyncio
import logging

import discord

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class LedgerBot(discord.Client):
    def __init__(self, config: dict):
        self.config = config

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
        print(f"Message from {message.author}: {message.content}")

        if message.content == "hello":
            await message.channel.send("howdy")
