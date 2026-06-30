"""create resume parse vnext tables

Revision ID: 20260630_0011
Revises: 20260521_0010
Create Date: 2026-06-30
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260630_0011"
down_revision: str | None = "20260521_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resume_parse_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("resume_file_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=True),
        sa.Column("parser_version", sa.String(length=80), nullable=False),
        sa.Column("ai_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="success"),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"]),
        sa.ForeignKeyConstraint(["resume_file_id"], ["resume_files.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_parse_runs_resume_file_id", "resume_parse_runs", ["resume_file_id"])

    op.create_table(
        "resume_parse_blocks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("parse_run_id", sa.String(length=36), nullable=False),
        sa.Column("block_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_offset", sa.Integer(), nullable=True),
        sa.Column("end_offset", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("inferred", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parse_run_id"], ["resume_parse_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_parse_blocks_parse_run_id", "resume_parse_blocks", ["parse_run_id"])

    op.create_table(
        "resume_field_candidates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("parse_run_id", sa.String(length=36), nullable=False),
        sa.Column("field_name", sa.String(length=120), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("extractor", sa.String(length=120), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("selected", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["parse_run_id"], ["resume_parse_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resume_field_candidates_parse_run_id", "resume_field_candidates", ["parse_run_id"])
    op.create_index("ix_resume_field_candidates_field_name", "resume_field_candidates", ["field_name"])


def downgrade() -> None:
    op.drop_index("ix_resume_field_candidates_field_name", table_name="resume_field_candidates")
    op.drop_index("ix_resume_field_candidates_parse_run_id", table_name="resume_field_candidates")
    op.drop_table("resume_field_candidates")
    op.drop_index("ix_resume_parse_blocks_parse_run_id", table_name="resume_parse_blocks")
    op.drop_table("resume_parse_blocks")
    op.drop_index("ix_resume_parse_runs_resume_file_id", table_name="resume_parse_runs")
    op.drop_table("resume_parse_runs")
