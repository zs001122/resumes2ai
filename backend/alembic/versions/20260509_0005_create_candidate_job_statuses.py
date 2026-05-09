"""create candidate job statuses

Revision ID: 20260509_0005
Revises: 20260509_0004
Create Date: 2026-05-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260509_0005"
down_revision: str | None = "20260509_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_job_statuses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_candidate_job_statuses_job_candidate",
        "candidate_job_statuses",
        ["job_id", "candidate_id"],
        unique=True,
    )
    op.create_index("ix_candidate_job_statuses_status", "candidate_job_statuses", ["status"])


def downgrade() -> None:
    op.drop_index("ix_candidate_job_statuses_status", table_name="candidate_job_statuses")
    op.drop_index("ix_candidate_job_statuses_job_candidate", table_name="candidate_job_statuses")
    op.drop_table("candidate_job_statuses")
