"""create resume upload and parse tables

Revision ID: 20260509_0002
Revises: 20260509_0001
Create Date: 2026-05-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260509_0002"
down_revision: str | None = "20260509_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("phone", sa.String(length=60), nullable=True),
        sa.Column("email", sa.String(length=160), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("current_company", sa.String(length=200), nullable=True),
        sa.Column("current_title", sa.String(length=200), nullable=True),
        sa.Column("years_of_experience", sa.Float(), nullable=True),
        sa.Column("highest_education", sa.String(length=120), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("education", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("work_experiences", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("project_experiences", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("low_confidence_fields", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidates_phone", "candidates", ["phone"])
    op.create_index("ix_candidates_email", "candidates", ["email"])

    op.create_table(
        "resume_files",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), sa.ForeignKey("candidates.id"), nullable=True),
        sa.Column("file_name", sa.String(length=260), nullable=False),
        sa.Column("file_type", sa.String(length=20), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("preview_path", sa.String(length=500), nullable=True),
        sa.Column("parsed_text", sa.Text(), nullable=True),
        sa.Column("upload_status", sa.String(length=24), nullable=False, server_default="uploaded"),
        sa.Column("parse_status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_resume_files_job_id", "resume_files", ["job_id"])
    op.create_index("ix_resume_files_candidate_id", "resume_files", ["candidate_id"])
    op.create_index("ix_resume_files_parse_status", "resume_files", ["parse_status"])

    op.create_table(
        "resume_field_extractions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("resume_file_id", sa.String(length=36), sa.ForeignKey("resume_files.id"), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), sa.ForeignKey("candidates.id"), nullable=True),
        sa.Column("field_name", sa.String(length=120), nullable=False),
        sa.Column("extracted_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("text_start_offset", sa.Integer(), nullable=True),
        sa.Column("text_end_offset", sa.Integer(), nullable=True),
        sa.Column("bounding_box", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_resume_field_extractions_resume_file_id", "resume_field_extractions", ["resume_file_id"])
    op.create_index("ix_resume_field_extractions_candidate_id", "resume_field_extractions", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_resume_field_extractions_candidate_id", table_name="resume_field_extractions")
    op.drop_index("ix_resume_field_extractions_resume_file_id", table_name="resume_field_extractions")
    op.drop_table("resume_field_extractions")
    op.drop_index("ix_resume_files_parse_status", table_name="resume_files")
    op.drop_index("ix_resume_files_candidate_id", table_name="resume_files")
    op.drop_index("ix_resume_files_job_id", table_name="resume_files")
    op.drop_table("resume_files")
    op.drop_index("ix_candidates_email", table_name="candidates")
    op.drop_index("ix_candidates_phone", table_name="candidates")
    op.drop_table("candidates")
