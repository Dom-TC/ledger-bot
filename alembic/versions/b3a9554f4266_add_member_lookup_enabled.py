"""Add member.lookup_enabled.

Revision ID: b3a9554f4266
Revises: 9561e0128062
Create Date: 2025-10-09 20:45:45.606100

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3a9554f4266"
down_revision: Union[str, Sequence[str], None] = "9561e0128062"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "members",
        sa.Column("lookup_enabled", sa.Integer(), server_default="1", nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("members", "lookup_enabled")
