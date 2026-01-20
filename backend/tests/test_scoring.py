import pytest
from app.services.risk.scoring import compute_signal_score, language_intensity


def test_language_intensity():
    """Test language intensity detection"""
    # High intensity keywords
    text_high = "Se produjo un bloqueo y huelga en la zona"
    assert language_intensity(text_high) >= 2.0

    # Medium intensity keywords
    text_medium = "Hubo una denuncia y rechazo de la comunidad"
    assert 0.4 <= language_intensity(text_medium) < 2.0

    # No intensity
    text_low = "El clima estuvo agradable hoy"
    assert language_intensity(text_low) == 0.0


def test_compute_signal_score_basic():
    """Test basic signal score computation"""
    result = compute_signal_score(
        source_weight=1.0,
        top_topic_score=0.5,
        text="protesta pacífica",
        recurrence=0,
        official=False,
        sentiment_score=0.0,
        source_credibility=0.7
    )

    assert "score" in result
    assert "drivers" in result
    assert 0 <= result["score"] <= 10.0


def test_compute_signal_score_with_sentiment():
    """Test that negative sentiment increases risk"""
    # Negative sentiment should increase score
    result_negative = compute_signal_score(
        source_weight=1.0,
        top_topic_score=0.5,
        text="protesta",
        sentiment_score=-0.8,  # Very negative
        source_credibility=0.7
    )

    # Positive sentiment should decrease score
    result_positive = compute_signal_score(
        source_weight=1.0,
        top_topic_score=0.5,
        text="protesta",
        sentiment_score=0.8,  # Very positive
        source_credibility=0.7
    )

    assert result_negative["score"] > result_positive["score"]


def test_compute_signal_score_with_credibility():
    """Test that source credibility affects score"""
    # High credibility source
    result_high_cred = compute_signal_score(
        source_weight=2.0,
        top_topic_score=0.5,
        text="protesta",
        source_credibility=0.9
    )

    # Low credibility source
    result_low_cred = compute_signal_score(
        source_weight=2.0,
        top_topic_score=0.5,
        text="protesta",
        source_credibility=0.3
    )

    assert result_high_cred["score"] > result_low_cred["score"]
