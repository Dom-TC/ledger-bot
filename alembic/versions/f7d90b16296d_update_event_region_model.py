"""Update event region model.

Revision ID: f7d90b16296d
Revises: b1b48fc8932e
Create Date: 2025-10-29 21:43:40.872098

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7d90b16296d"
down_revision: Union[str, Sequence[str], None] = "b1b48fc8932e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "event_regions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("region_name", sa.String(), nullable=False),
        sa.Column("new_event_category", sa.Integer(), nullable=False),
        sa.Column("event_post_channel", sa.Integer(), nullable=False),
        sa.Column("bot_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_regions")),
        sa.UniqueConstraint("region_name", name=op.f("uq_event_regions_region_name")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("event_regions")
