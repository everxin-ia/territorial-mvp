from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime, timezone, timedelta
from app.db.session import get_db
from app.db.models import Signal, SignalTopic, SignalTerritory
import json

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
        topics = db.execute(select(SignalTopic).where(
            SignalTopic.signal_id == s.id)).scalars().all()
        terrs = db.execute(select(SignalTerritory).where(
            SignalTerritory.signal_id == s.id)).scalars().all()

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
    topics = db.execute(select(SignalTopic).where(
        SignalTopic.signal_id == s.id)).scalars().all()
    terrs = db.execute(select(SignalTerritory).where(
        SignalTerritory.signal_id == s.id)).scalars().all()
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


@router.get("/{signal_id}/geosparsing-trace")
def get_geosparsing_trace(signal_id: int, db: Session = Depends(get_db)):
    """
    Obtiene la trazabilidad completa del geosparsing con IA para una señal

    Retorna información detallada sobre:
    - Qué topónimos se detectaron
    - Dónde estaban en el texto
    - Por qué se mapearon a cada territorio
    - Scoring detallado
    - Método de detección usado
    """
    s = db.get(Signal, signal_id)
    if not s:
        return {"error": "Signal not found"}

    terrs = db.execute(select(SignalTerritory).where(
        SignalTerritory.signal_id == s.id)).scalars().all()

    trace_data = {
        "signal_id": s.id,
        "signal_title": s.title,
        "signal_url": s.url,
        "captured_at": s.captured_at,
        "territories_detected": [],
        "ai_enabled": False,
        "metadata": {
            "total_territories": len(terrs),
            "ai_detected_count": 0,
            "legacy_detected_count": 0
        }
    }

    for t in terrs:
        territory_info = {
            "territory_name": t.territory,
            "territory_level": t.level,
            "confidence": t.confidence,
            "coordinates": {
                "latitude": t.latitude,
                "longitude": t.longitude
            } if t.latitude and t.longitude else None,

            # Trazabilidad
            "detection": {
                "detected_toponym": t.detected_toponym,
                "position_in_text": t.toponym_position,
                "context": t.toponym_context,
            } if t.detected_toponym else None,

            # Scoring
            "relevance_score": t.relevance_score,
            "scoring_breakdown": json.loads(t.scoring_breakdown_json) if t.scoring_breakdown_json else None,

            # Explicabilidad
            "mapping_method": t.mapping_method,
            "disambiguation_reason": t.disambiguation_reason,
            "ai_provider": t.ai_provider,
        }

        trace_data["territories_detected"].append(territory_info)

        # Contar métodos
        if t.ai_provider and t.ai_provider not in ["none", "legacy"]:
            trace_data["ai_enabled"] = True
            trace_data["metadata"]["ai_detected_count"] += 1
        else:
            trace_data["metadata"]["legacy_detected_count"] += 1

    return trace_data
