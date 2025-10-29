"""Add MessageType to BotMessage.

Revision ID: b1b48fc8932e
Revises: 799a8048324f
Create Date: 2025-10-29 07:48:01.075583

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1b48fc8932e"
down_revision: Union[str, Sequence[str], None] = "799a8048324f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite requires batch operations for ALTER COLUMN operations
    with op.batch_alter_table("bot_messages", schema=None) as batch_op:
        # Add message_type column as nullable first
        batch_op.add_column(sa.Column("message_type", sa.String(), nullable=True))

        # Add event_id column
        batch_op.add_column(sa.Column("event_id", sa.Integer(), nullable=True))

        # Make transaction_id nullable
        batch_op.alter_column(
            "transaction_id", existing_type=sa.INTEGER(), nullable=True
        )

        # Add foreign key for event_id
        batch_op.create_foreign_key(
            op.f("fk_bot_messages_event_id_events"), "events", ["event_id"], ["id"]
        )

        # Add check constraint to ensure exactly one of transaction_id or event_id is set
        batch_op.create_check_constraint(
            "ck_bot_messages_exactly_one_type_id",
            "(transaction_id IS NOT NULL AND event_id IS NULL) OR "
            "(transaction_id IS NULL AND event_id IS NOT NULL)",
        )

    # Set all existing rows to 'transaction' (lowercase to match MessageType enum)
    op.execute(
        "UPDATE bot_messages SET message_type = 'TRANSACTION' WHERE message_type IS NULL"
    )

    # Now make the column non-nullable using batch operations
    with op.batch_alter_table("bot_messages", schema=None) as batch_op:
        batch_op.alter_column("message_type", existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # SQLite requires batch operations for ALTER COLUMN operations
    with op.batch_alter_table("bot_messages", schema=None) as batch_op:
        # Drop check constraint first
        batch_op.drop_constraint("ck_bot_messages_exactly_one_type_id", type_="check")

        # Drop foreign key
        batch_op.drop_constraint(
            op.f("fk_bot_messages_event_id_events"), type_="foreignkey"
        )

        # Make transaction_id non-nullable again
        batch_op.alter_column(
            "transaction_id", existing_type=sa.INTEGER(), nullable=False
        )

        # Drop columns
        batch_op.drop_column("event_id")
        batch_op.drop_column("message_type")
