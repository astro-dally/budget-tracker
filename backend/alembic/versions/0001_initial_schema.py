"""Initial schema: accounts plus owner-scoped budget data.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("category_id", sa.String(length=32), nullable=False),
        sa.Column("category_name", sa.String(length=50), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("rule_key", sa.String(length=40), nullable=False),
        sa.Column("level", sa.String(length=10), nullable=False),
        sa.Column("threshold", sa.String(length=12), nullable=False),
        sa.Column("message", sa.String(length=300), nullable=False),
        sa.Column("spent_minor", sa.BigInteger(), nullable=False),
        sa.Column("limit_minor", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name=op.f("fk_alerts_owner_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
        sa.UniqueConstraint("category_id", "period", "rule_key", name="uq_alerts_once_per_period"),
    )
    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_alerts_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_alerts_is_read"), ["is_read"], unique=False)
        batch_op.create_index(batch_op.f("ix_alerts_owner_id"), ["owner_id"], unique=False)

    op.create_table(
        "categories",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("name_key", sa.String(length=50), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column("icon", sa.String(length=40), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_categories_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("owner_id", "name_key", name=op.f("uq_categories_owner_id_name_key")),
    )
    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_categories_owner_id"), ["owner_id"], unique=False)

    op.create_table(
        "budgets",
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("category_id", sa.String(length=32), nullable=False),
        sa.Column("limit_minor", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_budgets_category_id_categories"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name=op.f("fk_budgets_owner_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("category_id", name=op.f("pk_budgets")),
    )
    with op.batch_alter_table("budgets", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_budgets_owner_id"), ["owner_id"], unique=False)

    op.create_table(
        "category_rules",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("keyword", sa.String(length=50), nullable=False),
        sa.Column("category_id", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_category_rules_category_id_categories"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_category_rules_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_category_rules")),
        sa.UniqueConstraint("owner_id", "keyword", name=op.f("uq_category_rules_owner_id_keyword")),
    )
    with op.batch_alter_table("category_rules", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_category_rules_category_id"), ["category_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_category_rules_owner_id"), ["owner_id"], unique=False)

    op.create_table(
        "recurring_payments",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("category_id", sa.String(length=32), nullable=True),
        sa.Column("frequency", sa.String(length=10), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_generated_on", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_recurring_payments_category_id_categories"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_recurring_payments_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recurring_payments")),
    )
    with op.batch_alter_table("recurring_payments", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_recurring_payments_owner_id"), ["owner_id"], unique=False
        )

    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("description_key", sa.String(length=200), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("category_id", sa.String(length=32), nullable=True),
        sa.Column("category_source", sa.String(length=10), nullable=False),
        sa.Column("recurring_id", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name=op.f("fk_transactions_category_id_categories")
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_transactions_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recurring_id"],
            ["recurring_payments.id"],
            name=op.f("fk_transactions_recurring_id_recurring_payments"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
        sa.UniqueConstraint("recurring_id", "occurred_on", name="uq_transactions_recurrence"),
    )
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_transactions_category_id"), ["category_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_transactions_description_key"), ["description_key"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_transactions_occurred_on"), ["occurred_on"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_transactions_owner_id"), ["owner_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_transactions_type"), ["type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_transactions_type"))
        batch_op.drop_index(batch_op.f("ix_transactions_owner_id"))
        batch_op.drop_index(batch_op.f("ix_transactions_occurred_on"))
        batch_op.drop_index(batch_op.f("ix_transactions_description_key"))
        batch_op.drop_index(batch_op.f("ix_transactions_category_id"))

    op.drop_table("transactions")
    with op.batch_alter_table("recurring_payments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_recurring_payments_owner_id"))

    op.drop_table("recurring_payments")
    with op.batch_alter_table("category_rules", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_category_rules_owner_id"))
        batch_op.drop_index(batch_op.f("ix_category_rules_category_id"))

    op.drop_table("category_rules")
    with op.batch_alter_table("budgets", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_budgets_owner_id"))

    op.drop_table("budgets")
    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_categories_owner_id"))

    op.drop_table("categories")
    with op.batch_alter_table("alerts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_alerts_owner_id"))
        batch_op.drop_index(batch_op.f("ix_alerts_is_read"))
        batch_op.drop_index(batch_op.f("ix_alerts_created_at"))

    op.drop_table("alerts")
    op.drop_table("users")
