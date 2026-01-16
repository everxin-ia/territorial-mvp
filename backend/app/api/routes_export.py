from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
import pandas as pd
from app.db.session import get_db
from app.db.models import Signal, RiskSnapshot

router = APIRouter()

@router.get("/signals.csv", response_class=PlainTextResponse)
def export_signals_csv(tenant_id: int = Query(1), limit: int = Query(1000, le=5000), db: Session = Depends(get_db)):
    signals = db.execute(
        select(Signal).where(Signal.tenant_id==tenant_id).order_by(Signal.captured_at.desc()).limit(limit)
    ).scalars().all()
    df = pd.DataFrame([{
        "id": s.id,
        "title": s.title,
        "url": s.url,
        "published_at": s.published_at,
        "captured_at": s.captured_at,
    } for s in signals])
    return df.to_csv(index=False)

@router.get("/risk.csv", response_class=PlainTextResponse)
def export_risk_csv(tenant_id: int = Query(1), limit: int = Query(1000, le=5000), db: Session = Depends(get_db)):
    snaps = db.execute(
        select(RiskSnapshot).where(RiskSnapshot.tenant_id==tenant_id).order_by(RiskSnapshot.period_end.desc()).limit(limit)
    ).scalars().all()
    df = pd.DataFrame([{
        "id": s.id,
        "territory": s.territory,
        "period_start": s.period_start,
        "period_end": s.period_end,
        "risk_score": s.risk_score,
        "risk_prob": s.risk_prob,
        "confidence": s.confidence,
        "drivers": s.drivers_json,
    } for s in snaps])
    return df.to_csv(index=False)
