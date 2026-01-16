from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Source, Signal, SignalTopic, SignalTerritory
from app.services.ingest.rss import fetch_rss
from app.services.nlp.topics import topic_scores
from app.services.nlp.territories import match_territories

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
            # upsert by unique hash constraint
            sig = Signal(
                tenant_id=tenant_id,
                source_id=src.id,
                title=it["title"],
                url=it["url"],
                content=it["content"],
                published_at=it["published_at"],
                hash=it["hash"],
            )
            try:
                db.add(sig)
                db.commit()
            except Exception:
                db.rollback()
                continue

            inserted += 1

            # NLP topics
            text = f"{sig.title} {sig.content}"
            for t in topic_scores(text):
                db.add(SignalTopic(signal_id=sig.id, topic=t["topic"], score=t["score"], method=t["method"]))
            # Territories
            for tr in match_territories(text):
                db.add(SignalTerritory(signal_id=sig.id, territory=tr["territory"], level=tr["level"], confidence=tr["confidence"]))
            db.commit()

    return inserted
