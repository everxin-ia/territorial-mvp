from rapidfuzz import fuzz

# Demo dictionary — reemplaza por tu catálogo territorial
TERRITORIES = {
    "Santiago": {"level": "comuna"},
    "Valparaíso": {"level": "región"},
    "Antofagasta": {"level": "región"},
    "Concepción": {"level": "comuna"},
    "La Serena": {"level": "comuna"},
}

def match_territories(text: str) -> list[dict]:
    t = (text or "")
    results = []
    for name, meta in TERRITORIES.items():
        if name.lower() in t.lower():
            results.append({"territory": name, "level": meta["level"], "confidence": 0.9})
        else:
            # fuzzy on tokens for demo
            score = fuzz.partial_ratio(name.lower(), t.lower()) / 100.0
            if score >= 0.92:
                results.append({"territory": name, "level": meta["level"], "confidence": float(score)})
    if not results:
        results.append({"territory": "No identificado", "level": "unknown", "confidence": 0.2})
    return results[:3]
