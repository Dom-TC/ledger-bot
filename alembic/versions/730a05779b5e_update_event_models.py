"""Update event models.

Revision ID: 730a05779b5e
Revises: f7d90b16296d
Create Date: 2025-11-01 21:25:13.553226

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "730a05779b5e"
down_revision: Union[str, Sequence[str], None] = "f7d90b16296d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.add_column(sa.Column("region_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("is_ongoing", sa.Integer()))
        batch_op.add_column(sa.Column("is_private", sa.Integer()))
        batch_op.add_column(sa.Column("channel_jump_url", sa.String(), nullable=True))
        batch_op.create_unique_constraint(op.f("uq_events_channel_id"), ["channel_id"])

    op.execute("UPDATE events SET region_id = 1 WHERE region_id IS NULL")

    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.alter_column("region_id", nullable=False)
        batch_op.create_foreign_key(
            op.f("fk_events_region_id_event_regions"),
            "event_regions",
            ["region_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_constraint(
            op.f("fk_events_region_id_event_regions"), type_="foreignkey"
        )
        batch_op.drop_constraint(op.f("uq_events_channel_id"), type_="unique")
        batch_op.drop_column("channel_jump_url")
        batch_op.drop_column("is_ongoing")
        batch_op.drop_column("region_id")
