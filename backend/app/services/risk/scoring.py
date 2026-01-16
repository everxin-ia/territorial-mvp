INTENSITY_KEYWORDS = {
    "high": ["bloqueo", "paro", "huelga", "enfrentamiento", "violencia", "sanción", "querella", "incendio"],
    "medium": ["denuncia", "rechazo", "conflicto", "tensión", "audiencia pública", "fiscalización", "acusación"],
}

def language_intensity(text: str) -> float:
    t = (text or "").lower()
    score = 0.0
    for kw in INTENSITY_KEYWORDS["high"]:
        if kw in t:
            score += 1.0
    for kw in INTENSITY_KEYWORDS["medium"]:
        if kw in t:
            score += 0.4
    return min(score, 2.0)

def compute_signal_score(source_weight: float, top_topic_score: float, text: str,
                         recurrence: int = 0, official: bool = False) -> dict:
    lang = language_intensity(text)
    recurrence_boost = min(recurrence * 0.3, 2.0)
    official_boost = 0.6 if official else 0.0

    score = min(source_weight + (2.0 * top_topic_score) + lang + recurrence_boost + official_boost, 8.0)

    drivers = {
        "source_weight": source_weight,
        "topic_score": top_topic_score,
        "language_intensity": lang,
        "recurrence": recurrence,
        "official": official,
    }
    return {"score": float(score), "drivers": drivers}
