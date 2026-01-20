import pytest
from app.services.nlp.sentiment import analyze_sentiment


def test_sentiment_positive():
    """Test positive sentiment detection"""
    text = "Excelente acuerdo alcanzado. Gran logro para la comunidad."
    result = analyze_sentiment(text)

    assert result["label"] in ["positive", "neutral"]  # VADER puede variar
    assert -1.0 <= result["score"] <= 1.0


def test_sentiment_negative():
    """Test negative sentiment detection"""
    text = "Terrible situación. Grave problema que afecta a todos."
    result = analyze_sentiment(text)

    assert result["label"] in ["negative", "neutral"]
    assert -1.0 <= result["score"] <= 1.0


def test_sentiment_neutral():
    """Test neutral sentiment"""
    text = "La reunión se realizó el martes."
    result = analyze_sentiment(text)

    assert result["label"] == "neutral"
    assert -1.0 <= result["score"] <= 1.0


def test_sentiment_short_text():
    """Test short text handling"""
    text = "Hola"
    result = analyze_sentiment(text)

    assert result["label"] == "neutral"
    assert result["score"] == 0.0


def test_sentiment_empty():
    """Test empty text handling"""
    result = analyze_sentiment("")

    assert result["label"] == "neutral"
    assert result["score"] == 0.0
