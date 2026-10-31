"""Persist alert thresholds, add alert acknowledgement and query indexes."""

from alembic import op
import sqlalchemy as sa


revision = "0002_alert_configs_and_indexes"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alert_configs",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("threshold_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("alert_email", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("scope", name="uq_alert_configs_scope"),
    )
    with op.batch_alter_table("alerts") as batch:
        batch.add_column(
            sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.false())
        )
    op.create_index("ix_alerts_triggered_at", "alerts", ["triggered_at"], unique=False)
    op.create_index(
        "ix_price_snapshots_asin_scraped", "price_snapshots", ["asin_id", "scraped_at"], unique=False
    )
    op.create_index("ix_price_snapshots_seller_id", "price_snapshots", ["seller_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_price_snapshots_seller_id", table_name="price_snapshots")
    op.drop_index("ix_price_snapshots_asin_scraped", table_name="price_snapshots")
    op.drop_index("ix_alerts_triggered_at", table_name="alerts")
    with op.batch_alter_table("alerts") as batch:
        batch.drop_column("acknowledged")
    op.drop_table("alert_configs")
