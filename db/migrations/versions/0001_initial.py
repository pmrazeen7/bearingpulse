"""Initial schema."""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "asins",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("asin", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("search_query", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_asins_asin", "asins", ["asin"], unique=True)

    op.create_table(
        "sellers",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("seller_name", sa.String(length=255), nullable=False),
        sa.Column("seller_id_amazon", sa.String(length=255), nullable=True),
        sa.Column("is_fba", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("location_state", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_sellers_seller_name", "sellers", ["seller_name"], unique=False)

    op.create_table(
        "price_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("asin_id", sa.Uuid(), sa.ForeignKey("asins.id"), nullable=False),
        sa.Column("seller_id", sa.Uuid(), sa.ForeignKey("sellers.id"), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("mrp", sa.Numeric(10, 2), nullable=True),
        sa.Column("discount_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("is_buy_box_winner", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("stock_status", sa.String(length=64), nullable=True),
        sa.Column("simulated_pincode", sa.String(length=16), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_price_snapshots_scraped_at", "price_snapshots", ["scraped_at"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("asin_id", sa.Uuid(), sa.ForeignKey("asins.id"), nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_index("ix_price_snapshots_scraped_at", table_name="price_snapshots")
    op.drop_table("price_snapshots")
    op.drop_index("ix_sellers_seller_name", table_name="sellers")
    op.drop_table("sellers")
    op.drop_index("ix_asins_asin", table_name="asins")
    op.drop_table("asins")
