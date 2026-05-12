"""create job standard versions"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260512_0008"
down_revision: str | None = "20260511_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_standard_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("criteria_json", sa.JSON(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_standard_versions_job_id_version", "job_standard_versions", ["job_id", "version"])
    op.add_column(
        "candidate_matches",
        sa.Column("job_standard_version_id", sa.String(length=36), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("candidate_matches", "job_standard_version_id")
    op.drop_index("ix_job_standard_versions_job_id_version", table_name="job_standard_versions")
    op.drop_table("job_standard_versions")
