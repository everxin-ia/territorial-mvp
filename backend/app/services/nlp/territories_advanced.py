from __future__ import annotations
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from sqlalchemy import select
import json
from typing import Optional

def match_territories_db(text: str, db: Session, tenant_id: int) -> list[dict]:
    """
    Detecta territorios usando la base de datos de territories.
    Usa matching exacto y fuzzy con aliases.
    """
    from app.db.models import Territory

    territories = db.execute(
        select(Territory).where(Territory.tenant_id == tenant_id, Territory.enabled == True)
    ).scalars().all()

    if not territories:
        # Fallback al método legacy
        from app.services.nlp.territories import match_territories
        return match_territories(text)

    t = (text or "").lower()
    results = []

    for terr in territories:
        # Matching exacto por nombre
        if terr.name.lower() in t:
            results.append({
                "territory": terr.name,
                "level": terr.level,
                "confidence": 0.95,
                "lat": terr.latitude,
                "lon": terr.longitude
            })
            continue

        # Matching por aliases
        aliases = json.loads(terr.aliases_json or "[]")
        for alias in aliases:
            if alias.lower() in t:
                results.append({
                    "territory": terr.name,
                    "level": terr.level,
                    "confidence": 0.9,
                    "lat": terr.latitude,
                    "lon": terr.longitude
                })
                break
        else:
            # Fuzzy matching
            score = max(
                fuzz.partial_ratio(terr.name.lower(), t) / 100.0,
                max((fuzz.partial_ratio(alias.lower(), t) / 100.0 for alias in aliases), default=0.0)
            )
            if score >= 0.92:
                results.append({
                    "territory": terr.name,
                    "level": terr.level,
                    "confidence": float(score),
                    "lat": terr.latitude,
                    "lon": terr.longitude
                })

    # Si no se encontró nada
    if not results:
        results.append({
            "territory": "No identificado",
            "level": "unknown",
            "confidence": 0.2,
            "lat": None,
            "lon": None
        })

    # Ordenar por confianza descendente y limitar a 3
    return sorted(results, key=lambda x: x["confidence"], reverse=True)[:3]


def match_territories_spacy(text: str, nlp_model) -> list[dict]:
    """
    Usa spaCy NER para detectar entidades de tipo LOC (Location) y GPE (Geopolitical Entity).
    Requiere modelo spaCy previamente cargado.
    """
    if not nlp_model:
        return []

    doc = nlp_model(text[:10000])  # Limitar para performance
    locations = []

    for ent in doc.ents:
        if ent.label_ in ["LOC", "GPE", "ORG"]:  # ORG a veces captura nombres de lugares
            locations.append({
                "territory": ent.text,
                "level": "detected",
                "confidence": 0.8,
                "lat": None,
                "lon": None
            })

    return locations[:3]
