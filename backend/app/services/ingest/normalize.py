from __future__ import annotations
from bs4 import BeautifulSoup
from datetime import datetime
import re

def clean_html(text: str) -> str:
    if not text:
        return ""
    soup = BeautifulSoup(text, "lxml")
    cleaned = soup.get_text(" ", strip=True)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:8000]  # cap demo

def parse_datetime(dt_str) -> datetime | None:
    # MVP: feedparser often provides parsed struct_time; we keep None if not parseable here
    return None
