"""Manager for handling event post/message operations."""

import logging
from typing import TYPE_CHECKING, List

import discord

from ledger_bot.errors import EventChannelError
from ledger_bot.message_generators import (
    generate_event_detail_message,
    generate_event_signup_message,
)
from ledger_bot.models import BotMessage, BotMessageType, Event
from ledger_bot.services import Service
from ledger_bot.views import CreateSignupView

if TYPE_CHECKING:
    from ledger_bot.clients.event_client import EventClient

log = logging.getLogger(__name__)


class EventPostManager:
    """Manages Discord message/post operations for events."""

    def __init__(self, client: "EventClient", service: Service):
        """Initialize the EventPostManager.

        Parameters
        ----------
        client : EventClient
            The Discord client instance
        service : Service
            The service layer for data access
        """
        self.client = client
        self.service = service

    async def update_event_posts(self, event: Event) -> List[discord.Message] | None:
        """Update the posts for a given event.

        Parameters
        ----------
        event : Event
            The event whose posts should be updated

        Returns
        -------
        List[discord.Message] | None
            The updated Discord Message objects if successful, None otherwise

        Raises
        ------
        EventChannelError
            If event.id is None
            If the Discord message cannot be found
            If the edit fails due to permissions or other Discord errors
            If the event id and the bot_message event id don't match
            If message_type is not EVENT_DETAIL or EVENT_SIGNUP
        """
        log.info(
            f"Attempting to update event posts for event {event.event_name} ({event.id})"
        )

        if event.id is None:
            log.error(f"Event {event.id} has no id, cannot update event posts")
            raise EventChannelError(event, "Event has no id")

        bot_messages = await self.service.bot_message.get_bot_messages_by_event_id(
            event_id=event.id
        )

        if not bot_messages:
            log.info(f"Event {event.id} has no bot messages")
            return None

        edited_messages: List[discord.Message] = []

        for bot_message in bot_messages:
            if bot_message.event_id is not event.id:
                log.exception(
                    f"event.id ({event.id}) does not match bot_message.id ({bot_message.message_id})"
                )
                raise EventChannelError(
                    event, "Event.id and BotMessage.message_id don't match"
                )

            try:
                channel = await self.client.get_or_fetch_channel(bot_message.channel_id)

                if not isinstance(channel, discord.TextChannel):
                    log.error(
                        f"Channel {bot_message.channel_id} is not a text channel: {type(channel)}"
                    )
                    raise EventChannelError(event, "Channel is not a text channel")

                message = await channel.fetch_message(bot_message.message_id)

                if bot_message.message_type is BotMessageType.EVENT_DETAIL:
                    contents = await generate_event_detail_message(
                        event=event, client=self.client
                    )
                    message = await message.edit(content=contents)
                elif bot_message.message_type is BotMessageType.EVENT_SIGNUP:
                    contents = await generate_event_signup_message(
                        event=event, client=self.client
                    )
                    message = await message.edit(
                        content=contents,
                        view=CreateSignupView(client=self.client, event=event),
                    )
                else:
                    log.error(
                        f"BotMessage.message_type {bot_message.message_type} is not BotMessageType.EVENT_DETAIL or BotMessageType.EVENT_SIGNUP"
                    )
                    raise EventChannelError(
                        event,
                        "BotMessage.message_type is not BotMessageType.EVENT_DETAIL or BotMessageType.EVENT_SIGNUP",
                    )

                edited_messages.append(message)

            except discord.NotFound:
                log.info(f"Message {bot_message.message_id} does not exist, skipping.")
                break

            except discord.Forbidden as e:
                log.exception(
                    f"Permission denied to edit message {bot_message.message_id} for event {event.id}"
                )
                raise EventChannelError(
                    event, f"Permission denied to edit message: {e}"
                ) from e

            except discord.HTTPException as e:
                log.exception(
                    f"Discord API error when editing message {bot_message.message_id} for event {event.id}"
                )
                raise EventChannelError(
                    event, f"Discord API error when editing message: {e}"
                ) from e

        return edited_messages

    async def create_event_post(
        self,
        event: Event,
        channel: discord.TextChannel | int,
        message_type: BotMessageType,
        should_pin: bool = False,
    ) -> BotMessage | None:
        """Create a post for a given event.

        Parameters
        ----------
        event : Event
            The event whose posts should be created
        channel: discord.TextChannel | int
            The channel the message should be posted in
        message_type: BotMessageType
            The message type. EVENT_DETAIL or EVENT_SIGNUP
        should_pin: bool, optional
            Whether to pin the message, by default False

        Returns
        -------
        BotMessage | None
            The BotMessage object of the created message

        Raises
        ------
        EventChannelError
            If event.id is None
            If the message creation fails due to permissions or other Discord errors
            If message_type is not EVENT_DETAIL or EVENT_SIGNUP
        """
        log.info(
            f"Attempting to create event {message_type} post for event {event.event_name} ({event.id})"
        )

        if event.id is None:
            log.error(f"Event {event.id} has no id, cannot create event post")
            raise EventChannelError(event, "Event has no id")

        if message_type is BotMessageType.EVENT_DETAIL:
            contents = await generate_event_detail_message(
                event=event, client=self.client
            )
        elif message_type is BotMessageType.EVENT_SIGNUP:
            contents = await generate_event_signup_message(
                event=event, client=self.client
            )

            if event.is_private:
                log.info("Event is private. Skipping signup post")
                return None
        else:
            log.error(
                f"message_type {message_type} is not BotMessageType.EVENT_DETAIL or BotMessageType.EVENT_SIGNUP"
            )
            raise EventChannelError(
                event,
                "message_type is not BotMessageType.EVENT_DETAIL or BotMessageType.EVENT_SIGNUP",
            )

        try:
            if isinstance(channel, int):
                discord_channel = await self.client.get_or_fetch_channel(channel)

                if not isinstance(discord_channel, discord.TextChannel):
                    log.error(
                        f"Channel {channel} is not a text channel: {type(discord_channel)}"
                    )
                    raise EventChannelError(event, "Channel is not a text channel")
                else:
                    channel = discord_channel

            message = await channel.send(
                content=contents, view=CreateSignupView(client=self.client, event=event)
            )

            if should_pin:
                await message.pin()

            if message_type is BotMessageType.EVENT_DETAIL:
                bm = await self.service.bot_message.save_event_detail_bot_message(
                    message=message, event=event
                )
            elif message_type is BotMessageType.EVENT_SIGNUP:
                bm = await self.service.bot_message.save_event_signup_bot_message(
                    message=message, event=event
                )

            return bm

        except discord.NotFound as e:
            log.exception(
                f"Not found error when creating message in {channel} for event {event.id}"
            )
            raise EventChannelError(
                event, f"Permission denied to create message: {e}"
            ) from e

        except discord.Forbidden as e:
            log.exception(
                f"Permission denied to create message in {channel} for event {event.id}"
            )
            raise EventChannelError(
                event, f"Permission denied to create message: {e}"
            ) from e

        except discord.HTTPException as e:
            log.exception(
                f"Discord API error when creating message in {channel} for event {event.id}"
            )
            raise EventChannelError(
                event, f"Discord API error when creating message: {e}"
            ) from e

        except (ValueError, TypeError) as e:
            log.exception(
                f"Error when creating message in {channel} for event {event.id}"
            )
            raise EventChannelError(event, f"Error when creating message: {e}") from e
