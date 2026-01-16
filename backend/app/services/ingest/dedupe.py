import hashlib

def canonical_hash(title: str, url: str) -> str:
    raw = (title or "").strip().lower() + "|" + (url or "").strip().lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
