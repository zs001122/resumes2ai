"""create candidate duplicate checks"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260511_0007"
down_revision: str | None = "20260509_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "upload_processing_tasks",
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "upload_processing_tasks",
        sa.Column("has_duplicate_risk", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "candidate_duplicate_checks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("resume_file_id", sa.String(length=36), nullable=False),
        sa.Column("matched_candidate_id", sa.String(length=36), nullable=False),
        sa.Column("match_reason", sa.String(length=120), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending_review"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["matched_candidate_id"], ["candidates.id"]),
        sa.ForeignKeyConstraint(["resume_file_id"], ["resume_files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("candidate_duplicate_checks")
    op.drop_column("upload_processing_tasks", "has_duplicate_risk")
    op.drop_column("upload_processing_tasks", "duplicate_count")
