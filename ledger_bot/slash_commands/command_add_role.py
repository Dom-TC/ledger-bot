"""DM command - add_role."""

import logging
from typing import TYPE_CHECKING, Any, Dict

import discord

from ledger_bot.models import ReactionRole
from ledger_bot.reactions import add_reaction, is_valid_emoji
from ledger_bot.services import Service

if TYPE_CHECKING:
    from ledger_bot.clients import ReactionRolesClient

log = logging.getLogger(__name__)


async def command_add_role(
    client: "ReactionRolesClient",
    interaction: discord.Interaction[Any],
    role: discord.Role,
    emoji: str,
    message_id: int,
) -> None:
    """Add a role to the reactions database."""
    log.debug(
        f"Adding role: {role.name} with reaction {emoji} on message {message_id}."
    )
    await interaction.response.defer(ephemeral=True)

    # Confirm command is used from within a guild (and not a DM)
    if interaction.guild_id is None:
        log.info("Interaction had no guild id. Exiting")
        await interaction.followup.send(
            "This command must be used within a server.", ephemeral=True
        )
        return

    # Confirm emoji is in-fact an emoji
    if not is_valid_emoji(emoji):
        await interaction.followup.send(
            f'"{emoji}" is not a valid emoji.', ephemeral=True
        )
        return

    # Check if role already in storage
    stored_role = await client.service.reaction_role.get_reaction_role_by_role_id(
        server_id=interaction.guild_id, role_id=role.id
    )
    if stored_role is not None:
        await interaction.followup.send(
            f'"{role.name}" is already stored with reaction {stored_role.reaction_name}.',
            ephemeral=True,
        )
        return

    # Check if emoji in storage
    stored_reaction = await client.service.reaction_role.get_reaction_role_by_reaction(
        server_id=interaction.guild_id, message_id=message_id, reaction=emoji
    )
    if stored_reaction is not None:
        await interaction.followup.send(
            f'"{emoji}" is already stored with role "{stored_reaction.role_name}".',
            ephemeral=True,
        )
        return

    # Add role to storage
    reaction_role = ReactionRole(
        server_id=interaction.guild_id,
        message_id=message_id,
        reaction_name=emoji,
        reaction_bytecode=emoji.encode("unicode-escape").decode("ASCII"),
        role_id=role.id,
        role_name=role.name,
        bot_id=client.config["name"],
    )

    stored_record = await client.service.reaction_role.save_reaction_role(reaction_role)

    # Add reaction to target message
    await add_reaction(
        client=client,
        message_id=stored_record.message_id,
        reaction=stored_record.reaction_name,
    )

    await interaction.followup.send(f'Successfully added {emoji} for "{role.name}".')
