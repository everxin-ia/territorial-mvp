from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime, timedelta, timezone
import json

from app.db.models import AlertRule, AlertEvent, RiskSnapshot, Signal, SignalTerritory, SignalTopic
from app.services.alerts.notify import send_webhook


def _get_evidence_signals(db: Session, tenant_id: int, territory: str, period_start: datetime, limit: int = 5) -> list[dict]:
    """
    Obtiene las señales más relevantes que sirven como evidencia de la alerta

    Args:
        db: Sesión de base de datos
        tenant_id: ID del tenant
        territory: Territorio a filtrar
        period_start: Fecha desde la cual buscar señales
        limit: Número máximo de señales a retornar

    Returns:
        Lista de diccionarios con información de las señales
    """
    # Obtener IDs de signals que matchean el territorio
    territory_matches = db.execute(
        select(SignalTerritory.signal_id, SignalTerritory.confidence)
        .where(
            and_(
                SignalTerritory.territory.ilike(f"%{territory}%"),
                SignalTerritory.confidence > 0.5
            )
        )
        .order_by(SignalTerritory.confidence.desc())
        .limit(limit * 2)  # Obtener más para filtrar después
    ).all()

    if not territory_matches:
        return []

    signal_ids = [t.signal_id for t in territory_matches]

    # Obtener las señales completas
    signals = db.execute(
        select(Signal)
        .where(
            and_(
                Signal.id.in_(signal_ids),
                Signal.tenant_id == tenant_id,
                Signal.captured_at >= period_start
            )
        )
        .order_by(Signal.captured_at.desc())
        .limit(limit)
    ).scalars().all()

    evidence = []
    for sig in signals:
        # Obtener tópicos de la señal
        topics = db.execute(
            select(SignalTopic.topic, SignalTopic.score)
            .where(SignalTopic.signal_id == sig.id)
            .order_by(SignalTopic.score.desc())
            .limit(3)
        ).all()

        evidence.append({
            "id": sig.id,
            "title": sig.title,
            "url": sig.url,
            "published_at": sig.published_at.isoformat() if sig.published_at else None,
            "sentiment_score": sig.sentiment_score,
            "sentiment_label": sig.sentiment_label,
            "topics": [{"topic": t.topic, "score": t.score} for t in topics]
        })

    return evidence


def _generate_detailed_explanation(
    rule_name: str,
    territory: str,
    risk_prob: float,
    confidence: float,
    trend: str,
    trend_pct: float,
    is_anomaly: bool,
    drivers: dict,
    evidence_signals: list[dict]
) -> str:
    """
    Genera una explicación detallada y legible de por qué se generó la alerta

    Returns:
        Texto explicativo estructurado
    """
    explanation_parts = []

    # 1. Resumen ejecutivo
    explanation_parts.append(f"🚨 ALERTA: {rule_name}")
    explanation_parts.append(f"📍 Territorio: {territory}")
    explanation_parts.append(f"📊 Probabilidad de riesgo: {risk_prob:.1%} | Confianza: {confidence:.1%}")

    # 2. Razones de la alerta
    reasons = []

    if risk_prob >= 0.8:
        reasons.append("Probabilidad de riesgo MUY ALTA (≥80%)")
    elif risk_prob >= 0.6:
        reasons.append("Probabilidad de riesgo ALTA (≥60%)")

    if trend != "stable":
        trend_text = "incrementando" if trend == "rising" else "disminuyendo"
        reasons.append(f"Tendencia {trend_text} ({trend_pct:+.1f}% vs periodo anterior)")

    if is_anomaly:
        reasons.append("⚠️ ANOMALÍA DETECTADA: Comportamiento atípico identificado")

    # Analizar drivers
    num_signals = drivers.get("num_signals", 0)
    if num_signals > 50:
        reasons.append(f"Volumen alto de señales ({num_signals} en los últimos 7 días)")
    elif num_signals > 20:
        reasons.append(f"Volumen moderado de señales ({num_signals} en los últimos 7 días)")

    avg_sentiment = drivers.get("avg_sentiment", 0)
    if avg_sentiment < -0.3:
        reasons.append(f"Sentimiento negativo predominante (promedio: {avg_sentiment:.2f})")
    elif avg_sentiment < -0.1:
        reasons.append(f"Sentimiento ligeramente negativo (promedio: {avg_sentiment:.2f})")

    # Tópicos principales
    top_topics = drivers.get("top_topics", [])
    if top_topics:
        topics_str = ", ".join([f"{t[0]} ({t[1]})" for t in top_topics[:3]])
        reasons.append(f"Tópicos principales: {topics_str}")

    if reasons:
        explanation_parts.append("\n🔍 Razones de la alerta:")
        for i, reason in enumerate(reasons, 1):
            explanation_parts.append(f"  {i}. {reason}")

    # 3. Evidencia (noticias principales)
    if evidence_signals:
        explanation_parts.append("\n📰 Evidencia (noticias recientes):")
        for i, sig in enumerate(evidence_signals, 1):
            topics_text = ", ".join([t["topic"] for t in sig["topics"][:2]])
            sentiment_emoji = "😠" if sig["sentiment_score"] < -0.3 else "😐" if sig["sentiment_score"] < 0.3 else "😊"

            explanation_parts.append(
                f"  {i}. {sig['title'][:80]}... {sentiment_emoji}"
            )
            if topics_text:
                explanation_parts.append(f"     Tópicos: {topics_text}")
            if sig["url"]:
                explanation_parts.append(f"     URL: {sig['url']}")
    else:
        explanation_parts.append("\n📰 Sin noticias recientes disponibles como evidencia")

    # 4. Recomendaciones
    explanation_parts.append("\n💡 Recomendaciones:")
    if risk_prob >= 0.8 or is_anomaly:
        explanation_parts.append("  • Monitoreo URGENTE requerido")
        explanation_parts.append("  • Revisar y analizar las noticias de evidencia")
        explanation_parts.append("  • Considerar activar protocolos de respuesta")
    else:
        explanation_parts.append("  • Mantener vigilancia sobre el territorio")
        explanation_parts.append("  • Monitorear evolución en las próximas horas")

    return "\n".join(explanation_parts)


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
    now = datetime.now(timezone.utc)

    for r in rules:
        for s in snaps:
            if r.territory_filter and r.territory_filter.lower() not in s.territory.lower():
                continue
            if s.risk_prob < r.min_prob or s.confidence < r.min_confidence:
                continue

            # Deduplication window key: por hora (YYYY-MM-DD-HH)
            dedup_key = now.strftime("%Y-%m-%d-%H")

            # Obtener evidencia (señales recientes del territorio)
            evidence_signals = _get_evidence_signals(
                db=db,
                tenant_id=tenant_id,
                territory=s.territory,
                period_start=s.period_start,
                limit=5
            )

            # Parsear drivers
            drivers = json.loads(s.drivers_json or "{}")

            # Generar explicación detallada
            explanation = _generate_detailed_explanation(
                rule_name=r.name,
                territory=s.territory,
                risk_prob=s.risk_prob,
                confidence=s.confidence,
                trend=s.trend,
                trend_pct=s.trend_pct,
                is_anomaly=s.is_anomaly,
                drivers=drivers,
                evidence_signals=evidence_signals
            )

            ev = AlertEvent(
                tenant_id=tenant_id,
                rule_id=r.id,
                territory=s.territory,
                prob=s.risk_prob,
                confidence=s.confidence,
                explanation=explanation,
                dedup_window_key=dedup_key,
            )
            try:
                db.add(ev)
                db.commit()
                created += 1

                # Webhook con evidencia incluida
                send_webhook({
                    "tenant_id": tenant_id,
                    "rule": r.name,
                    "territory": s.territory,
                    "probability": s.risk_prob,
                    "confidence": s.confidence,
                    "trend": s.trend,
                    "trend_pct": s.trend_pct,
                    "is_anomaly": s.is_anomaly,
                    "drivers": drivers,
                    "evidence_signals": evidence_signals,
                    "triggered_at": ev.triggered_at.isoformat(),
                })
            except Exception:
                # Duplicate alert en esta hora para misma regla+territory
                db.rollback()
                continue

    return created
