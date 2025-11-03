"""Member management forms: add member, add host."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.errors import EventChannelError
from ledger_bot.message_generators import generate_event_detail_message
from ledger_bot.models import (
    BotMessageType,
    Event,
    EventMember,
    EventMemberStatus,
    Member,
)

if TYPE_CHECKING:
    from ledger_bot.LedgerBot import LedgerBot

log = logging.getLogger(__name__)


class PostSignupButton(discord.ui.Button):
    """Button to post a signup message for the event."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__(
            label="Create Signup Post" if not event.has_signup else "Bump Signup Post",
            style=(
                discord.ButtonStyle.success
                if not event.has_signup
                else discord.ButtonStyle.primary
            ),
            custom_id="PostSignupButton",
        )

    async def callback(self, interaction: discord.Interaction):
        # Import here to avoid circular dependency
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        bot_message = await self.client.create_event_post(
            event=self.event,
            channel=self.event.region.event_signup_channel,
            message_type=BotMessageType.EVENT_SIGNUP,
        )

        if not bot_message:
            feedback = "Failed to post message."
        else:
            channel = await self.client.get_or_fetch_channel(bot_message.channel_id)
            if not isinstance(channel, discord.TextChannel):
                log.error(
                    f"Channel {bot_message.channel_id} is not a text channel: {type(channel)}"
                )
                raise EventChannelError(self.event, "Channel is not a text channel")

            message = await channel.fetch_message(bot_message.message_id)

            feedback = f"Successfully created signup post at {message.jump_url}"
        await interaction.response.edit_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
                description=await generate_event_detail_message(
                    self.event, self.client
                ),
            ),
        )


class AddMemberButton(discord.ui.Button):
    """Button to add a member to the event."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__(
            label="Add Member",
            style=discord.ButtonStyle.primary,
            custom_id="AddMemberButton",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            view=AddMemberView(
                client=self.client, requestor=self.requestor, event=self.event
            ),
            ephemeral=True,
        )


class AddMemberView(discord.ui.View):
    """View with user select to add a member to the event."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__()

        # Add user select
        user_select: discord.ui.UserSelect = discord.ui.UserSelect(
            placeholder="Select a user to add as a member",
            min_values=1,
            max_values=1,
        )
        user_select.callback = self.user_selected  # type: ignore[method-assign]
        self.add_item(user_select)

    async def user_selected(self, interaction: discord.Interaction):
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        # Get the selected user from the select component
        select_data: list[str] = interaction.data.get("values", []) if interaction.data else []  # type: ignore[assignment]

        if not select_data:
            await interaction.response.send_message(
                "**Failed to add member.**\nNo user selected.",
                ephemeral=True,
            )
            return

        user_id = int(select_data[0])

        # Get the user from the guild
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101
        user = self.client.guild.get_member(user_id)

        if user is None:
            await interaction.response.send_message(
                "**Failed to add member.**\nUser not found in the server.",
                ephemeral=True,
            )
            return

        # Get or create the member record
        async with self.client.session_factory() as session:
            member = await self.client.service.member.get_or_add_member(
                user, session=session
            )

            # Check if the user is already a member of this event
            existing_members = (
                await self.client.service.event_member.list_event_members_by_event(
                    event_id=self.event.id, session=session
                )
            )

            # Check if member is already in the event
            is_already_member = any(
                em.member_id == member.id for em in existing_members
            )

            if is_already_member:
                feedback = f"**{user.display_name} is already a member of this event.**"
            else:
                # Add the member to the event
                event_member = EventMember(
                    event_id=self.event.id,
                    member_id=member.id,
                    status=EventMemberStatus.CONFIRMED,
                    bot_id=self.client.guild.id,
                )
                await self.client.service.event_member.add_event_member(
                    event_member=event_member, session=session
                )

                log.info(
                    f"Added {user.display_name} (member_id: {member.id}) to event {self.event.event_name} ({self.event.id}) as CONFIRMED"
                )

                feedback = f"**Successfully added {user.display_name} as a member.**"

        await interaction.response.edit_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
                description=await generate_event_detail_message(
                    self.event, self.client
                ),
            ),
        )


class AddHostButton(discord.ui.Button):
    """Button to add a host to the event."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__(
            label="Add Host",
            style=discord.ButtonStyle.primary,
            custom_id="AddHostButton",
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            view=AddHostView(
                client=self.client, requestor=self.requestor, event=self.event
            ),
            ephemeral=True,
        )


class AddHostView(discord.ui.View):
    """View with user select to add a host to the event."""

    def __init__(
        self,
        client: "LedgerBot",
        requestor: Member,
        event: Event,
    ) -> None:
        self.client = client
        self.requestor = requestor
        self.event = event

        super().__init__()

        # Add user select
        user_select: discord.ui.UserSelect = discord.ui.UserSelect(
            placeholder="Select a user to add as a host",
            min_values=1,
            max_values=1,
        )
        user_select.callback = self.user_selected  # type: ignore[method-assign]
        self.add_item(user_select)

    async def user_selected(self, interaction: discord.Interaction):
        from ledger_bot.views.event_forms.management_view import (
            CreateEventManagementButtons,
        )

        # Get the selected user from the select component
        select_data: list[str] = interaction.data.get("values", []) if interaction.data else []  # type: ignore[assignment]

        if not select_data:
            await interaction.response.send_message(
                "**Failed to add host.**\nNo user selected.",
                ephemeral=True,
            )
            return

        user_id = int(select_data[0])

        # Get the user from the guild
        assert isinstance(self.client.guild, discord.Guild)  # nosec B101
        user = self.client.guild.get_member(user_id)

        if user is None:
            await interaction.response.send_message(
                "**Failed to add host.**\nUser not found in the server.",
                ephemeral=True,
            )
            return

        # Get or create the member record
        async with self.client.session_factory() as session:
            member = await self.client.service.member.get_or_add_member(
                user, session=session
            )

            # Check if the user is already a member of this event
            existing_members = (
                await self.client.service.event_member.list_event_members_by_event(
                    event_id=self.event.id, session=session
                )
            )

            # Check if member is already in the event
            existing_event_member = next(
                (em for em in existing_members if em.member_id == member.id), None
            )

            if existing_event_member:
                # Update their status to HOST
                existing_event_member.status = EventMemberStatus.HOST
                await self.client.service.event_member.update_event_member(
                    event_member=existing_event_member,
                    fields=["status"],
                    session=session,
                )

                log.info(
                    f"Updated {user.display_name} (member_id: {member.id}) to HOST for event {self.event.event_name} ({self.event.id})"
                )

                feedback = f"**Successfully updated {user.display_name} to host.**"
            else:
                # Add the member to the event as a host
                event_member = EventMember(
                    event_id=self.event.id,
                    member_id=member.id,
                    status=EventMemberStatus.HOST,
                    bot_id=self.client.guild.id,
                )
                await self.client.service.event_member.add_event_member(
                    event_member=event_member, session=session
                )

                log.info(
                    f"Added {user.display_name} (member_id: {member.id}) to event {self.event.event_name} ({self.event.id}) as HOST"
                )

                feedback = f"**Successfully added {user.display_name} as a host.**"

        await interaction.response.edit_message(
            view=CreateEventManagementButtons(
                client=self.client,
                requestor=self.requestor,
                feedback=feedback,
                event=self.event,
                description=await generate_event_detail_message(
                    self.event, self.client
                ),
            ),
        )
