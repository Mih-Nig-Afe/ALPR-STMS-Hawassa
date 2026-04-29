from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import utcnow
from app.db.base import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="role")


class Subcity(Base):
    __tablename__ = "subcities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="default_subcity")
    assignments: Mapped[list[OfficerAssignment]] = relationship(back_populates="subcity")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone_number: Mapped[str | None] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), nullable=False)
    default_subcity_id: Mapped[str | None] = mapped_column(ForeignKey("subcities.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    role: Mapped[Role] = relationship(back_populates="users")
    default_subcity: Mapped[Subcity | None] = relationship(back_populates="users")
    assignments: Mapped[list[OfficerAssignment]] = relationship(back_populates="user")


class OfficerAssignment(Base):
    __tablename__ = "officer_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    subcity_id: Mapped[str] = mapped_column(ForeignKey("subcities.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates="assignments")
    subcity: Mapped[Subcity] = relationship(back_populates="assignments")


class ViolationRule(Base):
    __tablename__ = "violation_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    penalty_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    reference_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    rule_id: Mapped[str] = mapped_column(ForeignKey("violation_rules.id"), nullable=False)
    reporting_officer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    subcity_id: Mapped[str] = mapped_column(ForeignKey("subcities.id"), nullable=False)
    vehicle_plate: Mapped[str] = mapped_column(String(32), nullable=False)
    driver_phone_number: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    draft_penalty_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    location_text: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[str | None] = mapped_column(String(64))
    longitude: Mapped[str | None] = mapped_column(String(64))
    escape_path_geojson: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    rule: Mapped[ViolationRule] = relationship()
    reporting_officer: Mapped[User] = relationship()
    subcity: Mapped[Subcity] = relationship()
    evidence_items: Mapped[list[ViolationEvidence]] = relationship(back_populates="violation")
    alerts: Mapped[list[ViolationAlert]] = relationship(back_populates="violation")
    complaints: Mapped[list[Complaint]] = relationship(back_populates="violation")
    payment_requests: Mapped[list[PaymentRequest]] = relationship(back_populates="violation")


class ViolationEvidence(Base):
    __tablename__ = "violation_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    violation_id: Mapped[str] = mapped_column(ForeignKey("violations.id"), nullable=False)
    bucket_name: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hex: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    violation: Mapped[Violation] = relationship(back_populates="evidence_items")


class ViolationAlert(Base):
    __tablename__ = "violation_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    violation_id: Mapped[str] = mapped_column(ForeignKey("violations.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    violation: Mapped[Violation] = relationship(back_populates="alerts")
    recipients: Mapped[list[AlertRecipient]] = relationship(back_populates="alert")


class AlertRecipient(Base):
    __tablename__ = "alert_recipients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    alert_id: Mapped[str] = mapped_column(ForeignKey("violation_alerts.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    alert: Mapped[ViolationAlert] = relationship(back_populates="recipients")
    user: Mapped[User] = relationship()


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    violation_id: Mapped[str] = mapped_column(ForeignKey("violations.id"), nullable=False)
    opened_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    violation: Mapped[Violation] = relationship(back_populates="complaints")
    decisions: Mapped[list[ComplaintDecision]] = relationship(back_populates="complaint")


class ComplaintDecision(Base):
    __tablename__ = "complaint_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id"), nullable=False)
    decided_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    complaint: Mapped[Complaint] = relationship(back_populates="decisions")


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    violation_id: Mapped[str] = mapped_column(ForeignKey("violations.id"), nullable=False)
    reference_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)

    violation: Mapped[Violation] = relationship(back_populates="payment_requests")
    transactions: Mapped[list[PaymentTransaction]] = relationship(back_populates="payment_request")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    payment_request_id: Mapped[str] = mapped_column(ForeignKey("payment_requests.id"), nullable=False)
    provider_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    payment_request: Mapped[PaymentRequest] = relationship(back_populates="transactions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped[User] = relationship()
