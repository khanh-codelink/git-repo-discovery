"""create summaries and comparisons tables

Revision ID: 2186bf92c014
Revises:
Create Date: 2026-10-22 14:12:38.832763

Column names mirror SummaryResponse and ComparisonResponse in src/schemas/report_schema.py,
so a row is `{**response.model_dump(mode="json"), "user_id": user_id}`.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2186bf92c014"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("summaries", "comparisons")


def _shared_columns() -> list[sa.Column]:
    """Columns both tables have (built fresh per table: a Column belongs to one table)."""
    return [
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("auth.users.id", ondelete="CASCADE"),
            nullable=False,
            server_default=sa.text("auth.uid()"),
        ),
        sa.Column(
            "missing_readme",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("report", postgresql.JSONB(), nullable=False),
        sa.Column("report_type", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    ]


def _enable_owner_rls(table: str) -> None:
    """Enable RLS so signed-in users can only read and write their own rows."""
    owner = "(select auth.uid()) = user_id"
    op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON public.{table} TO authenticated")
    op.execute(
        f'CREATE POLICY "{table}_select_own" ON public.{table} '
        f"FOR SELECT TO authenticated USING ({owner})"
    )
    op.execute(
        f'CREATE POLICY "{table}_insert_own" ON public.{table} '
        f"FOR INSERT TO authenticated WITH CHECK ({owner})"
    )
    op.execute(
        f'CREATE POLICY "{table}_update_own" ON public.{table} '
        f"FOR UPDATE TO authenticated USING ({owner}) WITH CHECK ({owner})"
    )
    op.execute(
        f'CREATE POLICY "{table}_delete_own" ON public.{table} '
        f"FOR DELETE TO authenticated USING ({owner})"
    )


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "summaries",
        sa.Column(
            "summary_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("selected_repo", postgresql.JSONB(), nullable=True),
        *_shared_columns(),
        sa.CheckConstraint(
            "report_type IN ('summary', 'compare')", name="summaries_report_type_check"
        ),
        schema="public",
    )
    op.create_table(
        "comparisons",
        sa.Column(
            "comparison_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("comparison", sa.Text(), nullable=False),
        sa.Column("selected_repos", postgresql.JSONB(), nullable=False),
        *_shared_columns(),
        sa.CheckConstraint(
            "report_type IN ('summary', 'compare')", name="comparisons_report_type_check"
        ),
        schema="public",
    )

    for table in TABLES:
        # The RLS policies filter on user_id, and listing a user's reports does too.
        op.create_index(f"ix_{table}_user_id", table, ["user_id"], schema="public")
        _enable_owner_rls(table)


def downgrade() -> None:
    """Downgrade schema."""
    # Dropping a table also drops its policies and indexes.
    for table in reversed(TABLES):
        op.drop_table(table, schema="public")
