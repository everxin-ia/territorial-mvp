from __future__ import annotations
import feedparser
from datetime import datetime, timezone
from app.services.ingest.normalize import clean_html
from app.services.ingest.dedupe import canonical_hash

def fetch_rss(url: str) -> list[dict]:
    feed = feedparser.parse(url)
    items = []
    for e in feed.entries[:50]:
        title = getattr(e, "title", "") or ""
        link = getattr(e, "link", "") or ""
        summary = getattr(e, "summary", "") or ""
        published_at = None
        if getattr(e, "published_parsed", None):
            published_at = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
        items.append({
            "title": title[:500],
            "url": link[:1000],
            "content": clean_html(summary),
            "published_at": published_at,
            "hash": canonical_hash(title, link),
        })
    return items
