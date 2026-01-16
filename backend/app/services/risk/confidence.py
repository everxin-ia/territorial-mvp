def confidence_score(num_signals: int, num_sources: int, num_distinct_sources: int) -> float:
    # MVP heuristic: más señales y más diversidad de fuentes => más confianza
    s = min(num_signals / 10.0, 1.0)                 # 0..1
    d = min(num_distinct_sources / max(num_sources,1), 1.0)  # 0..1
    return float(0.2 + 0.5*s + 0.3*d)  # 0.2..1.0
