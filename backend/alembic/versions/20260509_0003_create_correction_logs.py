"""create field correction logs

Revision ID: 20260509_0003
Revises: 20260509_0002
Create Date: 2026-05-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260509_0003"
down_revision: str | None = "20260509_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "field_correction_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("candidate_id", sa.String(length=36), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("resume_file_id", sa.String(length=36), sa.ForeignKey("resume_files.id"), nullable=True),
        sa.Column("field_name", sa.String(length=120), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("editor_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_field_correction_logs_candidate_id", "field_correction_logs", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_field_correction_logs_candidate_id", table_name="field_correction_logs")
    op.drop_table("field_correction_logs")
