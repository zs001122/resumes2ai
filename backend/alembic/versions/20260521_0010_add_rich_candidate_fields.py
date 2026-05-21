"""add rich candidate parse fields

Revision ID: 20260521_0010
Revises: 20260512_0009
Create Date: 2026-05-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260521_0010"
down_revision: str | None = "20260512_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("certifications", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("candidates", sa.Column("languages", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("candidates", sa.Column("awards", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("candidates", sa.Column("self_evaluation", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidates", "self_evaluation")
    op.drop_column("candidates", "awards")
    op.drop_column("candidates", "languages")
    op.drop_column("candidates", "certifications")
