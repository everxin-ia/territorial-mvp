from __future__ import annotations

import asyncio
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Source, Signal, SignalTopic, SignalTerritory
from app.services.ingest.rss import fetch_rss
from app.services.ingest.simhash_dedup import compute_simhash, is_near_duplicate
from app.services.nlp.ai_geosparsing import AIGeoparser, geoparse_with_ai
from app.services.nlp.sentiment import analyze_sentiment
from app.services.nlp.topics import topic_scores
from app.services.nlp.territories import match_territories
from app.services.nlp.territories_advanced import match_territories_db


def ingest_sources(db: Session, tenant_id: int) -> int:
    sources = db.execute(
        select(Source).where(Source.tenant_id ==
                             tenant_id, Source.enabled == True)
    ).scalars().all()

    inserted = 0

    # Reutilizamos una sola instancia (para heurística + IA)
    geoparser = AIGeoparser()

    for src in sources:
        if src.type != "rss":
            continue

        items = fetch_rss(src.url)

        for it in items:
            title = it.get("title") or ""
            content = it.get("content") or ""
            url = it.get("url")  # <- IMPORTANTE para country gate

            text = f"{title} {content}"

            # Deduplicación rápida
            simhash_val = compute_simhash(text)

            recent_signals = db.execute(
                select(Signal)
                .where(Signal.tenant_id == tenant_id)
                .order_by(Signal.captured_at.desc())
                .limit(150)
            ).scalars().all()

            if any(s.simhash and is_near_duplicate(simhash_val, s.simhash, threshold=3) for s in recent_signals):
                continue

            # Sentiment
            sentiment = analyze_sentiment(text)

            # Insertar señal
            sig = Signal(
                tenant_id=tenant_id,
                source_id=src.id,
                title=title,
                url=url,
                content=content,
                published_at=it.get("published_at"),
                hash=it.get("hash"),
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

            # Topics
            for t in topic_scores(text):
                db.add(
                    SignalTopic(
                        signal_id=sig.id,
                        topic=t["topic"],
                        score=t["score"],
                        method=t.get("method", "heuristic"),
                    )
                )

            db.commit()

            # ------------------------------------------------------------------
            # TERRITORIES: Chile-only robusto
            # ------------------------------------------------------------------

            # 1) Country gate primero (MUY IMPORTANTE)
            #    Si NO parece Chile -> NO asignar territorios (ni IA ni fallback).
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    is_chile = loop.run_until_complete(
                        geoparser.is_chile_related(title, content, url=url)
                    )
                finally:
                    loop.close()
            except Exception:
                is_chile = False

            if not is_chile:
                # No agregamos SignalTerritory
                db.commit()
                continue

            # 2) Si es Chile: intentamos IA primero (pasando url)
            ai_enabled = bool(settings.openai_api_key)  # MVP: openai
            if ai_enabled:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        source_region = getattr(src, "region", None)

                        ai_matches = loop.run_until_complete(
                            geoparse_with_ai(
                                title,
                                content,
                                source_region=source_region,
                                url=url,  # <- IMPORTANTE
                            )
                        )
                    finally:
                        loop.close()

                    # Si IA devolvió territorios, los guardamos.
                    if ai_matches:
                        for match in ai_matches:
                            db.add(
                                SignalTerritory(
                                    signal_id=sig.id,
                                    territory=match["territory_name"],
                                    level=match["territory_level"],
                                    confidence=float(match["relevance_score"]),
                                    # trazabilidad (si tu modelo tiene estos campos)
                                    detected_toponym=match.get(
                                        "detected_toponym"),
                                    toponym_position=match.get(
                                        "toponym_position"),
                                    toponym_context=match.get(
                                        "toponym_context"),
                                    relevance_score=float(
                                        match.get("relevance_score", 0.0)),
                                    scoring_breakdown_json=json.dumps(
                                        match.get("scoring_breakdown", {})),
                                    mapping_method=match.get("mapping_method"),
                                    disambiguation_reason=match.get(
                                        "disambiguation_reason"),
                                    ai_provider=match.get("ai_provider"),
                                    latitude=match.get("latitude"),
                                    longitude=match.get("longitude"),
                                )
                            )

                        db.commit()
                        continue  # <- no usamos fallback si IA funcionó

                    # Si IA devuelve [], NO inventamos territorios.
                    db.commit()
                    continue

                except Exception as e:
                    print(
                        f"⚠️ IA geoparse falló, usando fallback (solo Chile): {e}")

            # 3) Fallback SOLO si es Chile y solo si IA falló (o no hay key)
            #    AUN ASÍ: recomiendo subir el umbral y NO default.
            try:
                territories = match_territories_db(text, db, tenant_id)
            except Exception:
                territories = match_territories(text)

            # Umbral mínimo (evita que el fallback meta cosas demasiado fáciles)
            territories = [tr for tr in territories if float(
                tr.get("confidence", 0)) >= 0.70]

            for tr in territories:
                db.add(
                    SignalTerritory(
                        signal_id=sig.id,
                        territory=tr["territory"],
                        level=tr.get("level", "unknown"),
                        confidence=float(tr.get("confidence", 0.0)),
                        latitude=tr.get("lat"),
                        longitude=tr.get("lon"),
                        mapping_method="fallback",
                        ai_provider="none",
                    )
                )

            db.commit()

    return inserted
