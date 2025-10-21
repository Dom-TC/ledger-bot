"""Add currencies.

Revision ID: 5c4e1b58f588
Revises: b3a9554f4266
Create Date: 2025-10-20 19:00:52.626350

"""

from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c4e1b58f588"
down_revision: Union[str, Sequence[str], None] = "b3a9554f4266"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "currencies",
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("rate", sa.Float(), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False),
        sa.Column("bot_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_currencies")),
    )

    currencies = sa.table(
        "currencies",
        sa.column("code", sa.String),
        sa.column("symbol", sa.String),
        sa.column("rate", sa.Float),
        sa.column("last_updated", sa.DateTime),
        sa.column("bot_id", sa.String),
    )

    op.bulk_insert(
        currencies,
        [
            {
                "code": "GBP",
                "symbol": "£",
                "rate": 1.0,
                "last_updated": datetime.now(timezone.utc),
                "bot_id": "Alembic",
            }
        ],
    )

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "currency_code", sa.String(), nullable=False, server_default="GBP"
            )
        )
        batch_op.create_foreign_key(
            "fk_transactions_currency_code_currencies",
            "currencies",
            ["currency_code"],
            ["code"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_constraint(op.f("fk_transactions_currency_code_currencies"))
        batch_op.drop_column("currency_code")
    op.drop_table("currencies")
