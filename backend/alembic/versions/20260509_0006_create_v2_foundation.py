"""create v2 foundation tables

Revision ID: 20260509_0006
Revises: 20260509_0005
Create Date: 2026-05-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260509_0006"
down_revision: str | None = "20260509_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "upload_processing_tasks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id"), nullable=False),
        sa.Column("resume_file_id", sa.String(length=36), sa.ForeignKey("resume_files.id"), nullable=True),
        sa.Column("original_filename", sa.String(length=260), nullable=False),
        sa.Column("upload_status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("parse_status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("match_status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_upload_processing_tasks_job", "upload_processing_tasks", ["job_id"])
    op.create_index("ix_upload_processing_tasks_resume_file", "upload_processing_tasks", ["resume_file_id"])
    op.create_index(
        "ix_upload_processing_tasks_statuses",
        "upload_processing_tasks",
        ["upload_status", "parse_status", "match_status"],
    )

    op.create_table(
        "candidate_match_explanations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("match_id", sa.String(length=36), sa.ForeignKey("candidate_matches.id"), nullable=False),
        sa.Column("dimension", sa.String(length=120), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("conclusion", sa.Text(), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidate_match_explanations_match", "candidate_match_explanations", ["match_id"])
    op.create_index("ix_candidate_match_explanations_dimension", "candidate_match_explanations", ["dimension"])

    op.create_table(
        "candidate_notes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("candidate_id", sa.String(length=36), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidate_notes_candidate", "candidate_notes", ["candidate_id"])
    op.create_index("ix_candidate_notes_job_candidate", "candidate_notes", ["job_id", "candidate_id"])

    op.create_table(
        "candidate_timeline_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("candidate_id", sa.String(length=36), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("action_summary", sa.Text(), nullable=False),
        sa.Column("before_value", sa.Text(), nullable=True),
        sa.Column("after_value", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidate_timeline_events_candidate", "candidate_timeline_events", ["candidate_id"])
    op.create_index(
        "ix_candidate_timeline_events_job_candidate",
        "candidate_timeline_events",
        ["job_id", "candidate_id"],
    )
    op.create_index("ix_candidate_timeline_events_action_type", "candidate_timeline_events", ["action_type"])

    op.create_table(
        "candidate_tags",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidate_tags_name", "candidate_tags", ["name"], unique=True)

    op.create_table(
        "candidate_tag_links",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("candidate_id", sa.String(length=36), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("tag_id", sa.String(length=36), sa.ForeignKey("candidate_tags.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidate_tag_links_candidate", "candidate_tag_links", ["candidate_id"])
    op.create_index("ix_candidate_tag_links_tag", "candidate_tag_links", ["tag_id"])
    op.create_index(
        "ix_candidate_tag_links_candidate_tag",
        "candidate_tag_links",
        ["candidate_id", "tag_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_tag_links_candidate_tag", table_name="candidate_tag_links")
    op.drop_index("ix_candidate_tag_links_tag", table_name="candidate_tag_links")
    op.drop_index("ix_candidate_tag_links_candidate", table_name="candidate_tag_links")
    op.drop_table("candidate_tag_links")

    op.drop_index("ix_candidate_tags_name", table_name="candidate_tags")
    op.drop_table("candidate_tags")

    op.drop_index("ix_candidate_timeline_events_action_type", table_name="candidate_timeline_events")
    op.drop_index("ix_candidate_timeline_events_job_candidate", table_name="candidate_timeline_events")
    op.drop_index("ix_candidate_timeline_events_candidate", table_name="candidate_timeline_events")
    op.drop_table("candidate_timeline_events")

    op.drop_index("ix_candidate_notes_job_candidate", table_name="candidate_notes")
    op.drop_index("ix_candidate_notes_candidate", table_name="candidate_notes")
    op.drop_table("candidate_notes")

    op.drop_index("ix_candidate_match_explanations_dimension", table_name="candidate_match_explanations")
    op.drop_index("ix_candidate_match_explanations_match", table_name="candidate_match_explanations")
    op.drop_table("candidate_match_explanations")

    op.drop_index("ix_upload_processing_tasks_statuses", table_name="upload_processing_tasks")
    op.drop_index("ix_upload_processing_tasks_resume_file", table_name="upload_processing_tasks")
    op.drop_index("ix_upload_processing_tasks_job", table_name="upload_processing_tasks")
    op.drop_table("upload_processing_tasks")
