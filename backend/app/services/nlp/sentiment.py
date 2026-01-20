from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Inicializar VADER para español (funciona razonablemente bien)
analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text: str) -> dict:
    """
    Analiza el sentimiento del texto usando VADER.

    Returns:
        dict con 'score' (-1 a +1) y 'label' (positive|negative|neutral)
    """
    if not text or len(text.strip()) < 10:
        return {"score": 0.0, "label": "neutral"}

    scores = analyzer.polarity_scores(text)
    compound = scores['compound']

    # Clasificación
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {
        "score": float(compound),
        "label": label,
        "breakdown": {
            "pos": scores['pos'],
            "neg": scores['neg'],
            "neu": scores['neu']
        }
    }
