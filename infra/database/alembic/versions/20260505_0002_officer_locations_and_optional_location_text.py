"""Add officer locations and make location text optional."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260505_0002"
down_revision: Union[str, None] = "20260429_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "officer_locations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("latitude", sa.String(length=64), nullable=False),
        sa.Column("longitude", sa.String(length=64), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_officer_locations_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_officer_locations")),
    )
    op.alter_column("violations", "location_text", existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    op.alter_column("violations", "location_text", existing_type=sa.String(length=255), nullable=False)
    op.drop_table("officer_locations")
