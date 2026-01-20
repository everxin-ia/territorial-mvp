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

def compute_signal_score(
    source_weight: float,
    top_topic_score: float,
    text: str,
    recurrence: int = 0,
    official: bool = False,
    sentiment_score: float = 0.0,
    source_credibility: float = 0.7
) -> dict:
    """
    Calcula el score de riesgo de una señal.

    Formula mejorada:
    score = source_weight * credibility + 2*topic + language + recurrence + official - sentiment_penalty
    """
    lang = language_intensity(text)
    recurrence_boost = min(recurrence * 0.3, 2.0)
    official_boost = 0.6 if official else 0.0

    # Ajuste por credibilidad de fuente (multiplica source_weight)
    adjusted_source = source_weight * source_credibility

    # Sentiment penalty: noticias negativas incrementan riesgo
    # sentiment_score es -1 (muy negativo) a +1 (muy positivo)
    # Convertimos a penalty: negativo = + riesgo, positivo = - riesgo
    sentiment_penalty = -sentiment_score * 0.5  # Rango: -0.5 a +0.5

    score = min(
        adjusted_source + (2.0 * top_topic_score) + lang + recurrence_boost + official_boost + sentiment_penalty,
        10.0  # Nuevo máximo aumentado
    )

    drivers = {
        "source_weight": source_weight,
        "source_credibility": source_credibility,
        "topic_score": top_topic_score,
        "language_intensity": lang,
        "recurrence": recurrence,
        "official": official,
        "sentiment_score": sentiment_score,
        "sentiment_penalty": sentiment_penalty,
    }
    return {"score": float(score), "drivers": drivers}
