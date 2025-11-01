"""A mixin for dealing with events."""

import logging
import re

import arrow
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ledger_bot.core import Config
from ledger_bot.errors import EventChannelError
from ledger_bot.models import Event, EventRegion
from ledger_bot.services import Service
from ledger_bot.utils import get_ordinal_suffix

from .extended_client import ExtendedClient

log = logging.getLogger(__name__)


class EventClient(ExtendedClient):
    def __init__(
        self,
        config: Config,
        scheduler: AsyncIOScheduler,
        service: Service,
        session_factory: async_sessionmaker[AsyncSession],
        **kwargs,
    ) -> None:
        self.config = config
        self.scheduler = scheduler
        self.service = service
        self.session_factory = session_factory

        super().__init__(
            config=config,
            scheduler=scheduler,
            service=service,
            session_factory=session_factory,
            **kwargs,
        )

    async def handle_event_reaction(
        self, payload: discord.RawReactionActionEvent
    ) -> bool:
        log.debug("Running handle_event_reaction")

        return False

    async def register_regions(self) -> None:
        log.info("Registering all regions.")

        for raw_region in self.config.channels.event_regions:
            region = EventRegion(
                region_name=raw_region.region_name,
                new_event_category=raw_region.new_event_category,
                event_post_channel=raw_region.event_post_channel,
            )

            region = await self.service.event_region.add_region(region)

            if region.id:
                log.info(
                    f"Successfully added region: {region.region_name} ({region.id})"
                )

    def _parse_channel_name(self, channel_name: str) -> tuple[str, str | None, str]:
        """Parse a channel name to determine its type and date.

        Parameters
        ----------
        channel_name : str
            The channel name to parse

        Returns
        -------
        tuple[str, str | None, str]
            A tuple of (channel_type, date_str, full_name) where:
            - channel_type is one of: "non_event", "dated", "ongoing", "tbd"
            - date_str is the date string for sorting (e.g., "2025-11-01") or None
            - full_name is the original channel name for alphabetical sorting
        """
        # Check if it matches our event channel pattern
        # Patterns: "1st-nov-...", "23rd-jan-...", "ongoing-...", "tbd-..."

        # Pattern for dated channels: {day}{ordinal}-{month}-...
        dated_pattern = r"^(\d{1,2})(st|nd|rd|th)-([a-z]{3})-(.+)$"
        match = re.match(dated_pattern, channel_name)
        if match:
            day = int(match.group(1))
            month_abbr = match.group(3)

            # Convert month abbreviation to month number
            month_map = {
                "jan": 1,
                "feb": 2,
                "mar": 3,
                "apr": 4,
                "may": 5,
                "jun": 6,
                "jul": 7,
                "aug": 8,
                "sep": 9,
                "oct": 10,
                "nov": 11,
                "dec": 12,
            }
            month = month_map.get(month_abbr)

            if month:
                # Create a sortable date string (assuming current/next year context)
                # Format: YYYY-MM-DD for easy sorting
                from datetime import datetime

                current_year = datetime.now().year
                date_str = f"{current_year:04d}-{month:02d}-{day:02d}"
                return ("dated", date_str, channel_name)

        # Check for ongoing pattern
        if channel_name.startswith("ongoing-"):
            return ("ongoing", None, channel_name)

        # Check for tbd pattern
        if channel_name.startswith("tbd-"):
            return ("tbd", None, channel_name)

        # Doesn't match our event pattern
        return ("non_event", None, channel_name)

    async def position_event_channel(
        self, channel: discord.TextChannel, category: discord.CategoryChannel
    ) -> None:
        """Position a specific channel within a category according to event priority.

        Positioning priority:
        1. Non-event channels (maintain their existing positions)
        2. Dated event channels (sorted by date, then alphabetically)
        3. Ongoing event channels (sorted alphabetically)
        4. TBD event channels (sorted alphabetically)

        Parameters
        ----------
        channel : discord.TextChannel
            The channel to position
        category : discord.CategoryChannel
            The category containing the channel

        Raises
        ------
        discord.Forbidden
            If bot lacks permissions to edit channel positions
        discord.HTTPException
            If Discord API request fails
        """
        log.info(
            f"Positioning channel '{channel.name}' in category '{category.name}' ({category.id})"
        )

        # Get all text channels in the category
        all_channels = [
            ch for ch in category.channels if isinstance(ch, discord.TextChannel)
        ]

        if not all_channels:
            log.debug(f"No channels in category '{category.name}'")
            return

        # Parse the target channel
        target_type, target_date, target_name = self._parse_channel_name(channel.name)

        # Parse and categorize all channels
        channel_data = []
        for ch in all_channels:
            if ch.id == channel.id:
                # Skip the target channel itself - we'll insert it later
                continue

            ch_type, ch_date, ch_name = self._parse_channel_name(ch.name)
            channel_data.append(
                {
                    "channel": ch,
                    "type": ch_type,
                    "date": ch_date,
                    "name": ch_name,
                    "position": ch.position,
                }
            )

        # Create sort key function
        def get_sort_key(ch_type: str, ch_date: str | None, ch_name: str) -> tuple:
            """Generate a sort key for comparison."""
            # Priority: non_event (-1), dated (0), ongoing (1), tbd (2)
            priority_map = {"non_event": -1, "dated": 0, "ongoing": 1, "tbd": 2}
            priority = priority_map.get(ch_type, 3)

            # Within each priority, sort by date (if applicable), then name
            date_sort = ch_date if ch_date else ""
            name_sort = ch_name

            return (priority, date_sort, name_sort)

        # Find the correct position for the target channel
        target_sort_key = get_sort_key(target_type, target_date, target_name)

        # Count how many channels should come before the target
        position = 0
        for ch_data in channel_data:
            ch_sort_key = get_sort_key(
                ch_data["type"], ch_data["date"], ch_data["name"]
            )
            if ch_sort_key < target_sort_key:
                position += 1

        # Only update if position has changed
        if channel.position != position:
            try:
                log.debug(
                    f"Moving channel '{channel.name}' from position "
                    f"{channel.position} to {position}"
                )
                await channel.edit(position=position)
                log.info(
                    f"Successfully positioned channel '{channel.name}' at position {position}"
                )

            except discord.Forbidden:
                log.exception(
                    f"Permission denied when positioning channel '{channel.name}'"
                )
                raise

            except discord.HTTPException:
                log.exception(
                    f"Discord API error when positioning channel '{channel.name}'"
                )
                raise

        else:
            log.debug(
                f"Channel '{channel.name}' is already at correct position {position}"
            )

    def generate_channel_name(self, event: Event) -> str:
        """Generate a Discord-compatible channel name from an event.

        Parameters
        ----------
        event : Event
            The event object to generate a channel name for

        Returns
        -------
        str
            A sanitized channel name following Discord requirements:
            - Lowercase
            - Spaces replaced with hyphens
            - Special characters removed
            - Max 80 characters
            - Prefixed with:
              - "ongoing-" if event.is_ongoing is True
              - "DD{suffix} MMM-" if event.event_date is set (e.g., "1st-nov-", "23rd-jan-")
              - "tbd-" otherwise
        """
        # Determine the prefix based on event properties
        if event.is_ongoing:
            prefix = "ongoing"
            log.debug(f"Event {event.id} is ongoing, using 'ongoing' prefix")
        elif event.event_date:
            day = event.event_date.day
            month = event.event_date.strftime("%b").lower()
            ordinal = get_ordinal_suffix(day)
            prefix = f"{day}{ordinal}-{month}"
            log.debug(
                f"Event {event.id} has date {event.event_date}, using '{prefix}' prefix"
            )
        else:
            prefix = "tbd"
            log.debug(
                f"Event {event.id} has no date/ongoing status, using 'tbd' prefix"
            )

        channel_name = event.event_name
        channel_name = channel_name.replace(" ", "-")
        channel_name = re.sub(r"[^a-z0-9\-_]", "", channel_name)
        channel_name = re.sub(r"-+", "-", channel_name)
        channel_name = channel_name.strip("-")
        channel_name = f"{prefix}-{channel_name}".lower()

        # Limit to 80 characters
        if len(channel_name) > 80:
            channel_name = channel_name[:80]
            # Remove trailing hyphen if truncation caused one
            channel_name = channel_name.rstrip("-")

        log.debug(
            f"Generated channel name: {channel_name} from event {event.id} ({event.event_name})"
        )

        return channel_name

    async def create_event_channel(
        self, event: Event, session: AsyncSession | None = None
    ) -> discord.TextChannel | None:
        """Create a Discord channel for an event.

        Creates a text channel in the EventRegion's new_event_category with a
        sanitized name based on the event name. If successful, updates the
        event's channel_id in the database.

        Parameters
        ----------
        event : Event
            The event to create a channel for
        session : AsyncSession | None, optional
            An optional session, by default None

        Returns
        -------
        discord.TextChannel | None
            The created Discord TextChannel object if successful, None otherwise

        Raises
        ------
        EventChannelError
            If event.region is None
            If event.region.new_event_category is None
            If the Discord category cannot be found
            If channel creation fails due to permissions or other Discord errors
        """
        log.info(
            f"Attempting to create channel for event {event.id} ({event.event_name})"
        )

        # Check if channel already exists
        if event.channel_id is not None:
            log.debug(
                f"Event {event.id} already has channel_id {event.channel_id}, skipping creation"
            )
            return None

        # Validate event has region
        if event.region is None:
            log.error(f"Event {event.id} has no associated region")
            raise EventChannelError(event, "Event has no associated region")

        # Validate region has new_event_category
        if event.region.new_event_category is None:
            log.error(
                f"Event region {event.region.region_name} has no new_event_category configured"
            )
            raise EventChannelError(
                event,
                f"Region {event.region.region_name} has no new_event_category configured",
            )

        # Get the category from Discord
        category = self.get_channel(event.region.new_event_category)
        if category is None:
            log.error(
                f"Could not find Discord category with id {event.region.new_event_category}"
            )
            raise EventChannelError(
                event,
                f"Discord category {event.region.new_event_category} not found",
            )

        if not isinstance(category, discord.CategoryChannel):
            log.error(
                f"Channel {event.region.new_event_category} is not a CategoryChannel"
            )
            raise EventChannelError(
                event,
                f"Channel {event.region.new_event_category} is not a category",
            )

        # Generate channel name
        channel_name = self.generate_channel_name(event)

        # Create the channel
        try:
            log.info(
                f"Creating channel '{channel_name}' in category '{category.name}' "
                f"for event {event.id}"
            )
            channel = await category.create_text_channel(name=channel_name)
            await self.position_event_channel(channel=channel, category=category)
            log.info(
                f"Successfully created channel {channel.id} ({channel.name}) "
                f"for event {event.id}"
            )

        except discord.Forbidden as e:
            log.exception(
                f"Permission denied when creating channel for event {event.id}"
            )
            raise EventChannelError(
                event, f"Permission denied to create channel: {e}"
            ) from e

        except discord.HTTPException as e:
            log.exception(
                f"Discord API error when creating channel for event {event.id}"
            )
            raise EventChannelError(
                event, f"Discord API error when creating channel: {e}"
            ) from e

        # Update event with channel_id
        event.channel_id = channel.id

        try:
            await self.service.event.update_event(
                event=event, fields=["channel_id"], session=session
            )
            log.info(f"Updated event {event.id} with channel_id {channel.id}")

        except SQLAlchemyError as e:
            log.exception(
                f"Database error when updating event {event.id} with channel_id {channel.id}"
            )
            # Channel was created but database update failed - delete the channel
            try:
                log.warning(
                    f"Attempting to delete channel {channel.id} due to database failure"
                )
                await channel.delete(
                    reason="Database update failed after channel creation"
                )
                log.info(f"Successfully deleted channel {channel.id}")
            except discord.HTTPException as delete_error:
                log.exception(
                    f"Failed to delete channel {channel.id} after database error: {delete_error}"
                )
                # Include both errors in the exception message
                raise EventChannelError(
                    event,
                    f"Failed to update event with channel_id: {e}. "
                    f"Also failed to delete channel: {delete_error}",
                ) from e
            raise EventChannelError(
                event, f"Failed to update event with channel_id: {e}"
            ) from e
        return channel
