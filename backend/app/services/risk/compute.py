from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import json
from collections import Counter, defaultdict
import numpy as np

from app.db.models import Source, Signal, SignalTopic, SignalTerritory, RiskSnapshot
from app.services.risk.scoring import compute_signal_score
from app.services.risk.probability import logistic_probability
from app.services.risk.confidence import confidence_score

def compute_risk_snapshots(db: Session, tenant_id: int, window_days: int = 7) -> int:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=window_days)

    signals = db.execute(
        select(Signal).where(Signal.tenant_id==tenant_id, Signal.captured_at>=start)
    ).scalars().all()

    if not signals:
        return 0

    # load topics/territories
    topics_by_signal = defaultdict(list)
    for st in db.execute(select(SignalTopic)).scalars().all():
        topics_by_signal[st.signal_id].append(st)

    terrs_by_signal = defaultdict(list)
    for tt in db.execute(select(SignalTerritory)).scalars().all():
        terrs_by_signal[tt.signal_id].append(tt)

    sources = {s.id: s for s in db.execute(select(Source).where(Source.tenant_id==tenant_id)).scalars().all()}
    num_sources = max(len(sources), 1)

    by_territory = defaultdict(list)
    by_territory_sources = defaultdict(set)
    topic_counter = defaultdict(Counter)

    for sig in signals:
        src = sources.get(sig.source_id)
        source_weight = float(src.weight if src else 1.0)
        source_credibility = float(src.credibility_score if src else 0.7)

        top_topic_score = 0.2
        if topics_by_signal.get(sig.id):
            top_topic_score = max(t.score for t in topics_by_signal[sig.id])

        # recurrence (MVP): count same source+title hash repeats (very rough)
        recurrence = 0

        score_pack = compute_signal_score(
            source_weight,
            top_topic_score,
            (sig.title + " " + (sig.content or "")),
            recurrence=recurrence,
            official=False,
            sentiment_score=sig.sentiment_score,
            source_credibility=source_credibility
        )
        sig_score = score_pack["score"]

        terrs = terrs_by_signal.get(sig.id) or []
        if not terrs:
            continue
        # assign to first territory (demo); could distribute by confidence
        terr = terrs[0].territory
        by_territory[terr].append((sig_score, score_pack["drivers"], sig.id))
        by_territory_sources[terr].add(sig.source_id)

        if topics_by_signal.get(sig.id):
            for t in topics_by_signal[sig.id]:
                topic_counter[terr][t.topic] += 1

    created = 0
    for terr, items in by_territory.items():
        risk_score = sum(s for s,_,_ in items)
        prob = logistic_probability(risk_score)

        distinct_sources = len(by_territory_sources[terr])
        conf = confidence_score(num_signals=len(items), num_sources=num_sources, num_distinct_sources=distinct_sources)

        # Time series analysis: comparar con periodo anterior
        prev_start = start - timedelta(days=window_days)
        prev_snaps = db.execute(
            select(RiskSnapshot).where(
                RiskSnapshot.tenant_id == tenant_id,
                RiskSnapshot.territory == terr,
                RiskSnapshot.period_start >= prev_start,
                RiskSnapshot.period_start < start
            )
        ).scalars().all()

        trend = "stable"
        trend_pct = 0.0
        is_anomaly = False

        if prev_snaps:
            # Comparar con promedio del periodo anterior
            prev_avg_score = np.mean([s.risk_score for s in prev_snaps])
            if prev_avg_score > 0:
                trend_pct = ((risk_score - prev_avg_score) / prev_avg_score) * 100

                if trend_pct > 20:
                    trend = "rising"
                elif trend_pct < -20:
                    trend = "falling"

                # Anomaly detection: si el score actual es > 2 std dev del histórico
                historical_scores = [s.risk_score for s in prev_snaps]
                if len(historical_scores) >= 3:
                    mean_hist = np.mean(historical_scores)
                    std_hist = np.std(historical_scores)
                    if std_hist > 0 and abs(risk_score - mean_hist) > 2 * std_hist:
                        is_anomaly = True

        drivers = {
            "window_days": window_days,
            "num_signals": len(items),
            "distinct_sources": distinct_sources,
            "top_topics": topic_counter[terr].most_common(5),
            "avg_sentiment": np.mean([signals[sig_id].sentiment_score for _, _, sig_id in items if sig_id < len(signals)]) if items else 0.0
        }

        snap = RiskSnapshot(
            tenant_id=tenant_id,
            territory=terr,
            period_start=start,
            period_end=end,
            risk_score=float(risk_score),
            risk_prob=float(prob),
            confidence=float(conf),
            drivers_json=json.dumps(drivers, ensure_ascii=False),
            trend=trend,
            trend_pct=float(trend_pct),
            is_anomaly=is_anomaly,
        )
        db.add(snap)
        db.commit()
        created += 1

    return created
