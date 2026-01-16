from __future__ import annotations
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.session import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="rss")  # rss|scrape
    weight: Mapped[float] = mapped_column(Float, default=1.0)     # 0-2 recomendado
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant: Mapped["Tenant"] = relationship()

class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (UniqueConstraint("tenant_id", "hash", name="uq_signal_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)

    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000))
    content: Mapped[str] = mapped_column(Text, default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    lang: Mapped[str] = mapped_column(String(10), default="es")
    hash: Mapped[str] = mapped_column(String(64), index=True)

    source: Mapped["Source"] = relationship()

class SignalTopic(Base):
    __tablename__ = "signal_topics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signals.id"), index=True)
    topic: Mapped[str] = mapped_column(String(80), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    method: Mapped[str] = mapped_column(String(40), default="rules")

class SignalTerritory(Base):
    __tablename__ = "signal_territories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("signals.id"), index=True)
    territory: Mapped[str] = mapped_column(String(120), index=True)
    level: Mapped[str] = mapped_column(String(40), default="unknown")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

class RiskSnapshot(Base):
    __tablename__ = "risk_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    territory: Mapped[str] = mapped_column(String(120), index=True)

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_prob: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    drivers_json: Mapped[str] = mapped_column(Text, default="{}")

class AlertRule(Base):
    __tablename__ = "alert_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    territory_filter: Mapped[str] = mapped_column(String(200), default="")  # substring match
    topic_filter: Mapped[str] = mapped_column(String(200), default="")      # substring match
    min_prob: Mapped[float] = mapped_column(Float, default=0.6)
    min_confidence: Mapped[float] = mapped_column(Float, default=0.4)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

class AlertEvent(Base):
    __tablename__ = "alert_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("alert_rules.id"), index=True)

    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    territory: Mapped[str] = mapped_column(String(120), index=True)
    prob: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="new")  # new|acked|closed
