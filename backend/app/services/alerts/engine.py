from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import json

from app.db.models import AlertRule, AlertEvent, RiskSnapshot
from app.services.alerts.notify import send_webhook

def run_alerts(db: Session, tenant_id: int) -> int:
    # Latest snapshot per territory in last 24h
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    snaps = db.execute(
        select(RiskSnapshot).where(RiskSnapshot.tenant_id==tenant_id, RiskSnapshot.period_end>=since)
    ).scalars().all()

    rules = db.execute(
        select(AlertRule).where(AlertRule.tenant_id==tenant_id, AlertRule.enabled==True)
    ).scalars().all()

    created = 0
    for r in rules:
        for s in snaps:
            if r.territory_filter and r.territory_filter.lower() not in s.territory.lower():
                continue
            if s.risk_prob < r.min_prob or s.confidence < r.min_confidence:
                continue

            explanation = f"Alerta '{r.name}': prob={s.risk_prob:.2f}, conf={s.confidence:.2f} en {s.territory}. Drivers: {s.drivers_json}"
            ev = AlertEvent(
                tenant_id=tenant_id,
                rule_id=r.id,
                territory=s.territory,
                prob=s.risk_prob,
                confidence=s.confidence,
                explanation=explanation,
            )
            db.add(ev)
            db.commit()
            created += 1

            send_webhook({
                "tenant_id": tenant_id,
                "rule": r.name,
                "territory": s.territory,
                "probability": s.risk_prob,
                "confidence": s.confidence,
                "drivers": json.loads(s.drivers_json or "{}"),
                "triggered_at": ev.triggered_at.isoformat(),
            })
    return created
