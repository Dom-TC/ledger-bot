"""Update event models.

Revision ID: 799a8048324f
Revises: 21bce503eccb
Create Date: 2025-10-28 23:20:58.326618

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "799a8048324f"
down_revision: Union[str, Sequence[str], None] = "21bce503eccb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "event_wines", sa.Column("event_member_id", sa.Integer(), nullable=False)
    )
    op.add_column(
        "event_wines",
        sa.Column(
            "size",
            sa.Enum("HALF", "FIFTYCL", "BOTTLE", "MAG", "DMAG", name="winesize"),
            nullable=False,
        ),
    )
    op.add_column("event_wines", sa.Column("quantity", sa.Integer(), nullable=False))

    with op.batch_alter_table("event_wines") as batch_op:
        batch_op.drop_constraint(
            op.f("fk_event_wines_member_id_members"), type_="foreignkey"
        )
        batch_op.create_foreign_key(
            op.f("fk_event_wines_event_member_id_event_members"),
            "event_members",
            ["event_member_id"],
            ["id"],
        )

    op.drop_column("event_wines", "member_id")

    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_constraint(op.f("fk_events_host_id_members"), type_="foreignkey")

    op.drop_column("events", "host_id")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("events", sa.Column("host_id", sa.INTEGER(), nullable=False))
    op.create_foreign_key(
        op.f("fk_events_host_id_members"), "events", "members", ["host_id"], ["id"]
    )
    op.add_column("event_wines", sa.Column("member_id", sa.INTEGER(), nullable=False))
    op.drop_constraint(
        op.f("fk_event_wines_event_member_id_event_members"),
        "event_wines",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_event_wines_member_id_members"),
        "event_wines",
        "members",
        ["member_id"],
        ["id"],
    )
    op.drop_column("event_wines", "quantity")
    op.drop_column("event_wines", "size")
    op.drop_column("event_wines", "event_member_id")
