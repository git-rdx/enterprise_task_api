"""add refresh token family id

Revision ID: e704728ab149
Revises: b5b81461ce72
Create Date: 2026-08-15 01:13:06.708692
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "e704728ab149"

down_revision: Union[
    str,
    Sequence[str],
    None
] = "b5b81461ce72"

branch_labels: Union[
    str,
    Sequence[str],
    None
] = None

depends_on: Union[
    str,
    Sequence[str],
    None
] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add temporarily as nullable
    op.add_column(
        "refresh_tokens",
        sa.Column(
            "family_id",
            sa.Uuid(),
            nullable=True
        )
    )

    # Assign a family to existing tokens
    op.execute(
        """
        UPDATE refresh_tokens
        SET family_id = gen_random_uuid()
        WHERE family_id IS NULL
        """
    )

    # Make it mandatory
    op.alter_column(
        "refresh_tokens",
        "family_id",
        existing_type=sa.Uuid(),
        nullable=False
    )

    # Add index
    op.create_index(
        op.f("ix_refresh_tokens_family_id"),
        "refresh_tokens",
        ["family_id"],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_refresh_tokens_family_id"),
        table_name="refresh_tokens"
    )

    op.drop_column(
        "refresh_tokens",
        "family_id"
    )