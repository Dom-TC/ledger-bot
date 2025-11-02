"""Add events  currency.

Revision ID: bd1e0d3ab430
Revises: 730a05779b5e
Create Date: 2025-11-02 00:31:50.883543

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bd1e0d3ab430"
down_revision: Union[str, Sequence[str], None] = "730a05779b5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite requires batch operations for ALTER COLUMN operations
    with op.batch_alter_table("events", schema=None) as batch_op:
        # Add currency_code column as nullable first
        batch_op.add_column(sa.Column("currency_code", sa.String(), nullable=True))

        # Make is_ongoing and is_private non-nullable
        batch_op.alter_column("is_ongoing", existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column("is_private", existing_type=sa.INTEGER(), nullable=False)

    # Set default value for existing rows
    op.execute("UPDATE events SET currency_code = 'GBP' WHERE currency_code IS NULL")

    # Now make currency_code non-nullable and add foreign key
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.alter_column(
            "currency_code", existing_type=sa.String(), nullable=False
        )
        batch_op.create_foreign_key(
            op.f("fk_events_currency_code_currencies"),
            "currencies",
            ["currency_code"],
            ["code"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    # SQLite requires batch operations for ALTER COLUMN operations
    with op.batch_alter_table("events", schema=None) as batch_op:
        # Drop foreign key constraint
        batch_op.drop_constraint(
            op.f("fk_events_currency_code_currencies"), type_="foreignkey"
        )

        # Make is_ongoing and is_private nullable again
        batch_op.alter_column(
            "is_private",
            existing_type=sa.INTEGER(),
            nullable=True,
        )
        batch_op.alter_column(
            "is_ongoing",
            existing_type=sa.INTEGER(),
            nullable=True,
        )

        # Drop currency_code column
        batch_op.drop_column("currency_code")
