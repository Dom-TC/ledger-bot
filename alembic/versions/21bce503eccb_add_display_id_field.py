"""Add display_id field.

Revision ID: 21bce503eccb
Revises: 5c4e1b58f588
Create Date: 2025-10-28 19:43:57.478694

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "21bce503eccb"
down_revision: Union[str, Sequence[str], None] = "5c4e1b58f588"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("transactions", sa.Column("display_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("transactions", "display_id")
