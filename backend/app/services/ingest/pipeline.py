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
from app.services.nlp.ai_geosparsing import geoparse_with_ai
import asyncio
import json
import os

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

            # Territories - usar IA si está configurada, sino fallback
            ai_enabled = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))

            if ai_enabled:
                try:
                    # Usar geosparsing con IA (trazabilidad completa)
                    # Ejecutar de forma síncrona
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        source_region = getattr(src, 'region', None)  # Si la fuente tiene región asociada
                        ai_matches = loop.run_until_complete(
                            geoparse_with_ai(it["title"], it["content"], source_region=source_region)
                        )

                        # Guardar con trazabilidad completa
                        for match in ai_matches:
                            db.add(SignalTerritory(
                                signal_id=sig.id,
                                territory=match["territory_name"],
                                level=match["territory_level"],
                                confidence=match["relevance_score"],
                                # Trazabilidad
                                detected_toponym=match["detected_toponym"],
                                toponym_position=match["toponym_position"],
                                toponym_context=match["toponym_context"],
                                relevance_score=match["relevance_score"],
                                scoring_breakdown_json=json.dumps(match["scoring_breakdown"]),
                                mapping_method=match["mapping_method"],
                                disambiguation_reason=match["disambiguation_reason"],
                                ai_provider=match["ai_provider"],
                                latitude=match["latitude"],
                                longitude=match["longitude"]
                            ))
                    finally:
                        loop.close()
                except Exception as e:
                    print(f"⚠️  Error en geosparsing con IA: {e}")
                    # Fallback a método DB
                    try:
                        territories = match_territories_db(text, db, tenant_id)
                    except Exception:
                        territories = match_territories(text)

                    for tr in territories:
                        db.add(SignalTerritory(
                            signal_id=sig.id,
                            territory=tr["territory"],
                            level=tr["level"],
                            confidence=tr["confidence"],
                            latitude=tr.get("lat"),
                            longitude=tr.get("lon"),
                            mapping_method="db_fallback",
                            ai_provider="none"
                        ))
            else:
                # Sin IA: usar método tradicional
                try:
                    territories = match_territories_db(text, db, tenant_id)
                except Exception:
                    territories = match_territories(text)

                for tr in territories:
                    db.add(SignalTerritory(
                        signal_id=sig.id,
                        territory=tr["territory"],
                        level=tr["level"],
                        confidence=tr["confidence"],
                        latitude=tr.get("lat"),
                        longitude=tr.get("lon"),
                        mapping_method="legacy",
                        ai_provider="none"
                    ))

            db.commit()

    return inserted
