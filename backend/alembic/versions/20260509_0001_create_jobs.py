"""create jobs table

Revision ID: 20260509_0001
Revises:
Create Date: 2026-05-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260509_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("salary_range", sa.String(length=120), nullable=True),
        sa.Column("experience_required", sa.String(length=120), nullable=True),
        sa.Column("education_required", sa.String(length=120), nullable=True),
        sa.Column("jd", sa.Text(), nullable=False),
        sa.Column("responsibilities", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("must_have", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("nice_to_have", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("deal_breakers", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("scoring_dimensions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_jobs_created_at", table_name="jobs")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_table("jobs")
