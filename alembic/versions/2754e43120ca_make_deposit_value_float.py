"""Make deposit_value float.

Revision ID: 2754e43120ca
Revises: bd1e0d3ab430
Create Date: 2025-11-02 22:33:24.317114

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2754e43120ca"
down_revision: Union[str, Sequence[str], None] = "bd1e0d3ab430"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.alter_column(
            "deposit_value",
            existing_type=sa.INTEGER(),
            type_=sa.Float(),
            existing_nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.alter_column(
            "deposit_value",
            existing_type=sa.Float(),
            type_=sa.INTEGER(),
            existing_nullable=True,
        )
