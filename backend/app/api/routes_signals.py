from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime, timezone, timedelta
from app.db.session import get_db
from app.db.models import Signal, SignalTopic, SignalTerritory

router = APIRouter()

@router.get("")
def list_signals(
    tenant_id: int = Query(1),
    limit: int = Query(100, le=500),
    territory: str | None = Query(None),
    topic: str | None = Query(None),
    days: int | None = Query(None, le=90),
    db: Session = Depends(get_db),
):
    """
    Lista señales con filtros opcionales por territorio, topic y días
    """
    query = select(Signal).where(Signal.tenant_id == tenant_id)

    # Filtro por días
    if days:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.where(Signal.captured_at >= since)

    query = query.order_by(Signal.captured_at.desc()).limit(limit)
    signals = db.execute(query).scalars().all()

    # lightweight enrichment
    out = []
    for s in signals:
        topics = db.execute(select(SignalTopic).where(SignalTopic.signal_id == s.id)).scalars().all()
        terrs = db.execute(select(SignalTerritory).where(SignalTerritory.signal_id == s.id)).scalars().all()

        # Aplicar filtros
        if territory and not any(territory.lower() in t.territory.lower() for t in terrs):
            continue
        if topic and not any(topic.lower() in t.topic.lower() for t in topics):
            continue

        out.append({
            "id": s.id,
            "title": s.title,
            "url": s.url,
            "captured_at": s.captured_at,
            "published_at": s.published_at,
            "sentiment_score": s.sentiment_score,
            "sentiment_label": s.sentiment_label,
            "topics": [{"topic": t.topic, "score": t.score} for t in topics],
            "territories": [{"territory": t.territory, "confidence": t.confidence} for t in terrs],
        })

    return out

@router.get("/{signal_id}")
def get_signal(signal_id: int, db: Session = Depends(get_db)):
    s = db.get(Signal, signal_id)
    if not s:
        return {"error": "not found"}
    topics = db.execute(select(SignalTopic).where(SignalTopic.signal_id == s.id)).scalars().all()
    terrs = db.execute(select(SignalTerritory).where(SignalTerritory.signal_id == s.id)).scalars().all()
    return {
        "id": s.id,
        "title": s.title,
        "url": s.url,
        "content": s.content,
        "captured_at": s.captured_at,
        "published_at": s.published_at,
        "sentiment_score": s.sentiment_score,
        "sentiment_label": s.sentiment_label,
        "topics": [{"topic": t.topic, "score": t.score} for t in topics],
        "territories": [{"territory": t.territory, "level": t.level, "confidence": t.confidence} for t in terrs],
    }
