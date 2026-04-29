"""Phase 1 initial schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("code", name=op.f("uq_roles_code")),
    )
    op.create_table(
        "subcities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subcities")),
        sa.UniqueConstraint("code", name=op.f("uq_subcities_code")),
    )
    op.create_table(
        "violation_rules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("penalty_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_violation_rules")),
        sa.UniqueConstraint("code", name=op.f("uq_violation_rules_code")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("default_subcity_id", sa.String(length=36), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["default_subcity_id"], ["subcities.id"], name=op.f("fk_users_default_subcity_id_subcities")),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("fk_users_role_id_roles")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], name=op.f("fk_audit_logs_actor_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_table(
        "officer_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("subcity_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=64), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["subcity_id"], ["subcities.id"], name=op.f("fk_officer_assignments_subcity_id_subcities")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_officer_assignments_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_officer_assignments")),
    )
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outbox_events")),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_sessions_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_sessions_token_hash")),
    )
    op.create_table(
        "violations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("reference_code", sa.String(length=64), nullable=False),
        sa.Column("rule_id", sa.String(length=36), nullable=False),
        sa.Column("reporting_officer_id", sa.String(length=36), nullable=False),
        sa.Column("subcity_id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_plate", sa.String(length=32), nullable=False),
        sa.Column("driver_phone_number", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("draft_penalty_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("location_text", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.String(length=64), nullable=True),
        sa.Column("longitude", sa.String(length=64), nullable=True),
        sa.Column("escape_path_geojson", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["reporting_officer_id"], ["users.id"], name=op.f("fk_violations_reporting_officer_id_users")),
        sa.ForeignKeyConstraint(["rule_id"], ["violation_rules.id"], name=op.f("fk_violations_rule_id_violation_rules")),
        sa.ForeignKeyConstraint(["subcity_id"], ["subcities.id"], name=op.f("fk_violations_subcity_id_subcities")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_violations")),
        sa.UniqueConstraint("reference_code", name=op.f("uq_violations_reference_code")),
    )
    op.create_table(
        "complaints",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("violation_id", sa.String(length=36), nullable=False),
        sa.Column("opened_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["opened_by_user_id"], ["users.id"], name=op.f("fk_complaints_opened_by_user_id_users")),
        sa.ForeignKeyConstraint(["violation_id"], ["violations.id"], name=op.f("fk_complaints_violation_id_violations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_complaints")),
    )
    op.create_table(
        "payment_requests",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("violation_id", sa.String(length=36), nullable=False),
        sa.Column("reference_code", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_payment_requests_created_by_user_id_users")),
        sa.ForeignKeyConstraint(["violation_id"], ["violations.id"], name=op.f("fk_payment_requests_violation_id_violations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_requests")),
        sa.UniqueConstraint("reference_code", name=op.f("uq_payment_requests_reference_code")),
    )
    op.create_table(
        "violation_alerts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("violation_id", sa.String(length=36), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_violation_alerts_created_by_user_id_users")),
        sa.ForeignKeyConstraint(["violation_id"], ["violations.id"], name=op.f("fk_violation_alerts_violation_id_violations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_violation_alerts")),
    )
    op.create_table(
        "violation_evidence",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("violation_id", sa.String(length=36), nullable=False),
        sa.Column("bucket_name", sa.String(length=128), nullable=False),
        sa.Column("storage_key", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256_hex", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["violation_id"], ["violations.id"], name=op.f("fk_violation_evidence_violation_id_violations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_violation_evidence")),
    )
    op.create_table(
        "alert_recipients",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("alert_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["violation_alerts.id"], name=op.f("fk_alert_recipients_alert_id_violation_alerts")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_alert_recipients_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alert_recipients")),
    )
    op.create_table(
        "complaint_decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("complaint_id", sa.String(length=36), nullable=False),
        sa.Column("decided_by_user_id", sa.String(length=36), nullable=False),
        sa.Column("decision", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], name=op.f("fk_complaint_decisions_complaint_id_complaints")),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"], name=op.f("fk_complaint_decisions_decided_by_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_complaint_decisions")),
    )
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("payment_request_id", sa.String(length=36), nullable=False),
        sa.Column("provider_reference", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["payment_request_id"], ["payment_requests.id"], name=op.f("fk_payment_transactions_payment_request_id_payment_requests")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_transactions")),
    )


def downgrade() -> None:
    op.drop_table("payment_transactions")
    op.drop_table("complaint_decisions")
    op.drop_table("alert_recipients")
    op.drop_table("violation_evidence")
    op.drop_table("violation_alerts")
    op.drop_table("payment_requests")
    op.drop_table("complaints")
    op.drop_table("violations")
    op.drop_table("sessions")
    op.drop_table("outbox_events")
    op.drop_table("officer_assignments")
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.drop_table("violation_rules")
    op.drop_table("subcities")
    op.drop_table("roles")

