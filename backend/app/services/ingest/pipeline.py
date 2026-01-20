from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Source, Signal, SignalTopic, SignalTerritory
from app.services.ingest.rss import fetch_rss
from app.services.nlp.topics import topic_scores
from app.services.nlp.territories import match_territories
from app.services.nlp.territories_advanced import match_territories_db
from app.services.nlp.sentiment import analyze_sentiment
from app.services.ingest.simhash_dedup import compute_simhash, is_near_duplicate

def ingest_sources(db: Session, tenant_id: int) -> int:
    sources = db.execute(
        select(Source).where(Source.tenant_id==tenant_id, Source.enabled==True)
    ).scalars().all()

    inserted = 0
    for src in sources:
        if src.type != "rss":
            continue

        items = fetch_rss(src.url)
        for it in items:
            text = f"{it['title']} {it['content']}"

            # Calcular simhash para near-duplicate detection
            simhash_val = compute_simhash(text)

            # Verificar near-duplicates (últimos 100 signals)
            recent_signals = db.execute(
                select(Signal)
                .where(Signal.tenant_id==tenant_id)
                .order_by(Signal.captured_at.desc())
                .limit(100)
            ).scalars().all()

            is_duplicate = False
            for recent in recent_signals:
                if recent.simhash and is_near_duplicate(simhash_val, recent.simhash, threshold=3):
                    is_duplicate = True
                    break

            if is_duplicate:
                continue  # Skip near-duplicates

            # Sentiment analysis
            sentiment = analyze_sentiment(text)

            # upsert by unique hash constraint
            sig = Signal(
                tenant_id=tenant_id,
                source_id=src.id,
                title=it["title"],
                url=it["url"],
                content=it["content"],
                published_at=it["published_at"],
                hash=it["hash"],
                simhash=simhash_val,
                sentiment_score=sentiment["score"],
                sentiment_label=sentiment["label"],
            )
            try:
                db.add(sig)
                db.commit()
            except Exception:
                db.rollback()
                continue

            inserted += 1

            # NLP topics
            for t in topic_scores(text):
                db.add(SignalTopic(signal_id=sig.id, topic=t["topic"], score=t["score"], method=t["method"]))

            # Territories - intentar primero con DB, luego fallback a legacy
            try:
                territories = match_territories_db(text, db, tenant_id)
            except Exception:
                territories = match_territories(text)

            for tr in territories:
                db.add(SignalTerritory(
                    signal_id=sig.id,
                    territory=tr["territory"],
                    level=tr["level"],
                    confidence=tr["confidence"]
                ))

            db.commit()

    return inserted
