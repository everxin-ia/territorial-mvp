from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import AlertRule, AlertEvent

router = APIRouter()

@router.get("")
def list_alert_events(tenant_id: int = Query(1), limit: int = Query(200, le=500), db: Session = Depends(get_db)):
    events = db.execute(
        select(AlertEvent).where(AlertEvent.tenant_id==tenant_id).order_by(AlertEvent.triggered_at.desc()).limit(limit)
    ).scalars().all()
    return [{
        "id": e.id,
        "rule_id": e.rule_id,
        "territory": e.territory,
        "prob": e.prob,
        "confidence": e.confidence,
        "explanation": e.explanation,
        "triggered_at": e.triggered_at,
        "status": e.status,
    } for e in events]

@router.get("/rules")
def list_rules(tenant_id: int = Query(1), db: Session = Depends(get_db)):
    rules = db.execute(select(AlertRule).where(AlertRule.tenant_id==tenant_id)).scalars().all()
    return [{
        "id": r.id,
        "name": r.name,
        "territory_filter": r.territory_filter,
        "topic_filter": r.topic_filter,
        "min_prob": r.min_prob,
        "min_confidence": r.min_confidence,
        "enabled": r.enabled,
    } for r in rules]
