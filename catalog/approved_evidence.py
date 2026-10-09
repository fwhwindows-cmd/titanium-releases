"""Opt-in licensed evidence feed. No website scraping or network requests by default.
Only per-category, source-backed descriptions from explicitly authorised feeds.
"""
import os
from urllib.parse import urlsplit
import requests
from keyword_guide import CATEGORIES, UNKNOWN

def validate(payload, movie_id, title, year):
    if not isinstance(payload, dict) or payload.get("rights") != "licensed-for-titanium":
        return None
    try:
        if int(payload.get("tmdb_id", 0)) != int(movie_id):
            return None
    except (TypeError, ValueError):
        return None
    if str(payload.get("title","")).strip().casefold() != title.strip().casefold():
        return None
    if str(payload.get("year","")).strip() != str(year).strip():
        return None
    categories = payload.get("categories", {})
    if not isinstance(categories, dict):
        return None
    descriptions, evidence = {}, {}
    for category in CATEGORIES:
        item = categories.get(category)
        if not isinstance(item, dict) or item.get("reviewed") is not True:
            continue
        summary, source_url = item.get("summary"), item.get("source_url")
        if not isinstance(summary, str) or not isinstance(source_url, str):
            continue
        summary = summary.strip()
        parsed = urlsplit(source_url)
        if (len(summary) < 24 or len(summary) > 300
                or UNKNOWN.casefold() in summary.casefold()
                or parsed.scheme != "https" or not parsed.netloc):
            continue
        descriptions[category] = category + " — " + summary
        evidence[category] = {"basis":"source_review", "sources":[source_url]}
    if not descriptions:
        return None
    return descriptions, evidence

def fetch_approved(movie_id, title, year, session=None):
    url = os.getenv("TITANIUM_EVIDENCE_FEED_URL", "").strip()
    token = os.getenv("TITANIUM_EVIDENCE_FEED_TOKEN", "").strip()
    parts = urlsplit(url)
    if not token or parts.scheme != "https" or not parts.netloc:
        return None
    session = session or requests.Session()
    try:
        result = session.get(
            url,
            params={"tmdb_id": movie_id, "title": title, "year": year},
            headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
            timeout=(5, 12), allow_redirects=False)
        if result.status_code != 200 or len(result.content) > 500_000:
            return None
        return validate(result.json(), movie_id, title, year)
    except (requests.RequestException, ValueError, TypeError):
        return None

def merge(descriptions, evidence, reviewed):
    if reviewed is None:
        return descriptions, evidence
    supported, provenance = reviewed
    descriptions = list(descriptions)
    evidence = dict(evidence)
    for index, category in enumerate(CATEGORIES):
        if category in supported and evidence.get(category, {}).get("basis") != "source_review":
            descriptions[index] = supported[category]
            evidence[category] = provenance[category]
    return descriptions, evidence
