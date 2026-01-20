from simhash import Simhash

def compute_simhash(text: str) -> str:
    """
    Calcula simhash de un texto para detección de near-duplicates.

    Returns:
        Hash hexadecimal de 64 bits
    """
    if not text or len(text.strip()) < 10:
        return "0" * 16

    # Simhash con 64 bits
    hash_obj = Simhash(text, f=64)
    return format(hash_obj.value, '016x')


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Calcula la distancia de Hamming entre dos hashes hexadecimales.

    Returns:
        Número de bits diferentes
    """
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        xor = val1 ^ val2
        return bin(xor).count('1')
    except (ValueError, TypeError):
        return 999  # Distancia muy alta para hashes inválidos


def is_near_duplicate(hash1: str, hash2: str, threshold: int = 3) -> bool:
    """
    Determina si dos textos son near-duplicates basado en simhash.

    Args:
        hash1, hash2: Hashes hexadecimales
        threshold: Número máximo de bits diferentes (default 3, ~5% diferencia)

    Returns:
        True si son near-duplicates
    """
    return hamming_distance(hash1, hash2) <= threshold
