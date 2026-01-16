import math

def logistic_probability(score: float, k: float = 0.7, threshold: float = 6.0) -> float:
    x = k * (score - threshold)
    return 1.0 / (1.0 + math.exp(-x))
