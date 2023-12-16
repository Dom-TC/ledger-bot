"""Additional functions for dealing with reactions."""

import logging
import re
from typing import TYPE_CHECKING, Optional

import discord
from emoji import is_emoji

if TYPE_CHECKING:
    from ledger_bot.mixins import ExtendedClient

log = logging.getLogger(__name__)


def is_valid_emoji(emoji: str) -> bool:
    """Check if the provided string is either a unicode emoji, or a valid discord custom emoji."""
    pattern = re.compile(r"^<:[a-zA-Z0-9_]+:\d+>$")
    return is_emoji(emoji) or bool(pattern.match(emoji))


async def _add_reaction_with_channel(
    client: "ExtendedClient",
    message_id: int,
    reaction: str,
    channel: discord.TextChannel,
) -> bool:
    try:
        log.info(f"Searching for {message_id} in {channel.name} - {channel.id}")
        message = await channel.fetch_message(message_id)

        try:
            log.info(f"Adding {reaction} to {message.id}")
            await message.add_reaction(reaction)

            return True
        except discord.NotFound as error:
            log.error(f"The reaction was not found: {error}")
        except discord.Forbidden as error:
            log.error(f"You don't have permission to add the reaction: {error}")
        except discord.HTTPException as error:
            log.error(f"An error occured adding the reaction: {error}")
        except TypeError as error:
            log.error(f"The emoji paramater {reaction} is invalid: {error}")
    except discord.NotFound:
        log.info("Message not found")

    return False


async def add_reaction(
    client: "ExtendedClient",
    message_id: int,
    reaction: str,
    channel_obj: Optional[discord.TextChannel] = None,
) -> None:
    """Adds the specified reaction to the given message."""
    log.info(f"Adding {reaction} to message {message_id}")

    if channel_obj is not None:
        await _add_reaction_with_channel(
            client=client, message_id=message_id, reaction=reaction, channel=channel_obj
        )
    else:
        for guild in client.guilds:
            for channel in guild.text_channels:
                success = await _add_reaction_with_channel(
                    client=client,
                    message_id=message_id,
                    reaction=reaction,
                    channel=channel,
                )

                if success:
                    break


async def _remove_reaction_with_channel(
    client: "ExtendedClient",
    message_id: int,
    reaction: str,
    channel: discord.TextChannel,
) -> bool:
    try:
        log.info(f"Searching for {message_id} in {channel.name} - {channel.id}")
        message = await channel.fetch_message(message_id)

        try:
            log.info(f"Removing {reaction} from {message.id}")
            await message.clear_reaction(reaction)

            return True
        except discord.NotFound as error:
            log.error(f"The reaction was not found: {error}")
        except discord.Forbidden as error:
            log.error(
                f"You don't have permission to remove the reaction: {error}"
                f"You're permissions are: "
            )
        except discord.HTTPException as error:
            log.error(f"An error occured remove the reaction: {error}")
        except TypeError as error:
            log.error(f"The emoji paramater {reaction} is invalid: {error}")

    except discord.NotFound:
        log.info("Message not found")
    except discord.Forbidden as error:
        log.error(f"You don't have permission to read from that channel: {error}")
    except discord.HTTPException as error:
        log.error(f"An error occured reading the message: {error}")

    return False


async def remove_reaction(
    client: "ExtendedClient",
    message_id: int,
    reaction: str,
    channel_obj: Optional[discord.TextChannel] = None,
) -> None:
    """Removes the specified reaction from the given message."""
    log.info(f"Removing {reaction} from message {message_id}")

    if channel_obj is not None:
        await _remove_reaction_with_channel(
            client=client, message_id=message_id, reaction=reaction, channel=channel_obj
        )
    else:
        log.info("No channel ID was specified, iterating through all known channels")

        for guild in client.guilds:
            for channel in guild.text_channels:
                success = await _remove_reaction_with_channel(
                    client=client,
                    message_id=message_id,
                    reaction=reaction,
                    channel=channel,
                )

                if success:
                    break
