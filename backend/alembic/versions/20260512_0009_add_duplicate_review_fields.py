"""add duplicate review fields"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260512_0009"
down_revision: str | None = "20260512_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("candidate_duplicate_checks", sa.Column("review_note", sa.Text(), nullable=True))
    op.add_column("candidate_duplicate_checks", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("candidate_duplicate_checks", "reviewed_at")
    op.drop_column("candidate_duplicate_checks", "review_note")
