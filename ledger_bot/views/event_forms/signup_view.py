"""Main event management views and buttons."""

import logging
from typing import TYPE_CHECKING

import discord

from ledger_bot.models import Event, EventMember, EventMemberStatus
from ledger_bot.views.base import BaseView

if TYPE_CHECKING:
    from ledger_bot.clients import EventClient

log = logging.getLogger(__name__)


class SignupButton(discord.ui.Button):
    """Button to sign a user up to an event."""

    event: Event

    async def callback(self, interaction: discord.Interaction):
        async with self.client.session_factory() as session:
            member = await self.client.service.member.get_or_add_member(
                interaction.user, session=session
            )

            # Check if the user is already a member of this event
            existing_members = (
                await self.client.service.event_member.list_event_members_by_event(
                    event_id=self.event.id, session=session
                )
            )

            is_already_member = any(
                em.member_id == member.id for em in existing_members
            )

            if is_already_member:
                feedback = "You are already a member of this event."
                log.info(
                    f"failed to add {member.display_name} (member_id: {member.id}) to event {self.event.event_name} ({self.event.id}). Member already in event."
                )
            else:
                event_member = EventMember(
                    event_id=self.event.id,
                    member_id=member.id,
                    status=self.status,
                    bot_id=self.client.config.bot_id,
                )
                await self.client.service.event_member.add_event_member(
                    event_member=event_member, session=session
                )

                log.info(
                    f"Added {member.display_name} (member_id: {member.id}) to event {self.event.event_name} ({self.event.id}) as {self.status}"
                )

                if self.status is EventMemberStatus.CONFIRMED:
                    feedback = f"You have been successfully added to {self.event.event_name}.\nYou can find out more about the event here: {self.event.channel_jump_url}"
                elif self.status is EventMemberStatus.WAITLIST:
                    feedback = f"You have been successfully added to the waitlist for {self.event.event_name}.\nYou can find out more about the event here: {self.event.channel_jump_url}"
                else:
                    feedback = f"You have been added to to {self.event.event_name} with an unknown status.\nYou can find out more about the event here: {self.event.channel_jump_url}"

        await interaction.response.edit_message(
            view=CreateSignupView(
                client=self.client,
                event=self.event,
            ),
        )
        await interaction.followup.send(feedback, ephemeral=True)

    def _label(self) -> str:
        if self.status is EventMemberStatus.CONFIRMED:
            return "Join Event"
        elif self.status is EventMemberStatus.WAITLIST:
            return "Join Waitlist"
        else:
            return "Unknown Status"

    def __init__(
        self,
        client: "EventClient",
        event: Event,
        status: EventMemberStatus = EventMemberStatus.CONFIRMED,
    ) -> None:
        self.client = client
        self.event = event
        self.status = status

        super().__init__(
            label=self._label(),
            style=discord.ButtonStyle.primary,
            custom_id="SignupButton",
        )


class CreateSignupView(BaseView):
    """View for signing up to an event."""

    def __init__(
        self,
        client: "EventClient",
        event: Event,
    ) -> None:
        self.client = client
        self.event = event

        super().__init__()

        signup_button = SignupButton(
            client=client, event=event, status=EventMemberStatus.CONFIRMED
        )
        waitlist_button = SignupButton(
            client=client, event=event, status=EventMemberStatus.WAITLIST
        )

        # Add button directly to view
        if not event.is_full:
            log.debug("Event has space, adding signup button")
            self.add_item(signup_button)
        else:
            log.debug("Event is full, adding waitlist button")
            self.add_item(waitlist_button)
