"""create candidate matches

Revision ID: 20260509_0004
Revises: 20260509_0003
Create Date: 2026-05-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260509_0004"
down_revision: str | None = "20260509_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_matches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("level", sa.String(length=40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("matched_points", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("weak_points", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("risks", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("interview_questions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidate_matches_job_candidate", "candidate_matches", ["job_id", "candidate_id"])
    op.create_index("ix_candidate_matches_score", "candidate_matches", ["score"])


def downgrade() -> None:
    op.drop_index("ix_candidate_matches_score", table_name="candidate_matches")
    op.drop_index("ix_candidate_matches_job_candidate", table_name="candidate_matches")
    op.drop_table("candidate_matches")
