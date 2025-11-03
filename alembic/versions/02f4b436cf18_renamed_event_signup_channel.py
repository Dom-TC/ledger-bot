"""Renamed event_signup_channel.

Revision ID: 02f4b436cf18
Revises: 2754e43120ca
Create Date: 2025-11-03 00:58:22.221979

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "02f4b436cf18"
down_revision: Union[str, Sequence[str], None] = "2754e43120ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "event_regions", sa.Column("event_signup_channel", sa.Integer(), nullable=False)
    )
    op.drop_column("event_regions", "event_post_channel")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "event_regions", sa.Column("event_post_channel", sa.INTEGER(), nullable=False)
    )
    op.drop_column("event_regions", "event_signup_channel")
