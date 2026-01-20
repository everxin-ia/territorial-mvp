import pytest
from app.services.ingest.simhash_dedup import compute_simhash, hamming_distance, is_near_duplicate


def test_compute_simhash():
    """Test simhash computation"""
    text = "Este es un texto de prueba para simhash"
    hash_val = compute_simhash(text)

    assert isinstance(hash_val, str)
    assert len(hash_val) == 16  # 64 bits = 16 hex chars


def test_simhash_identical():
    """Test that identical texts produce identical hashes"""
    text = "Texto de prueba idéntico"
    hash1 = compute_simhash(text)
    hash2 = compute_simhash(text)

    assert hash1 == hash2
    assert hamming_distance(hash1, hash2) == 0


def test_simhash_similar():
    """Test that similar texts produce similar hashes"""
    text1 = "Este es un texto sobre protestas sociales"
    text2 = "Este es un texto acerca de protestas sociales"

    hash1 = compute_simhash(text1)
    hash2 = compute_simhash(text2)

    distance = hamming_distance(hash1, hash2)
    # Textos similares deberían tener distancia pequeña
    assert distance < 10  # Threshold arbitrario


def test_simhash_different():
    """Test that different texts produce different hashes"""
    text1 = "Texto completamente diferente sobre el clima"
    text2 = "Huelga nacional en el sector minero"

    hash1 = compute_simhash(text1)
    hash2 = compute_simhash(text2)

    distance = hamming_distance(hash1, hash2)
    # Textos diferentes deberían tener mayor distancia
    assert distance > 5


def test_is_near_duplicate():
    """Test near-duplicate detection"""
    text1 = "Protesta en Santiago por temas ambientales"
    text2 = "Protesta en Santiago sobre temas ambientales"
    text3 = "Concierto de rock en Valparaíso"

    hash1 = compute_simhash(text1)
    hash2 = compute_simhash(text2)
    hash3 = compute_simhash(text3)

    # text1 y text2 son similares
    assert is_near_duplicate(hash1, hash2, threshold=5)

    # text1 y text3 son diferentes
    assert not is_near_duplicate(hash1, hash3, threshold=3)


def test_simhash_empty():
    """Test empty text handling"""
    hash_val = compute_simhash("")
    assert hash_val == "0" * 16
