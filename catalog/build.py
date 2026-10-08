#!/usr/bin/env python3
"""Compile persistent Titanium Content Guide records into GitHub-hosted JSON.

Reads TMDB's public daily ID export and the existing Titanium Render
metadata/advisory APIs. No secrets or user streaming data are required.
The generated records carry source provenance and distinguish unknown
warnings from known absence. This is a background data builder, not an API.
"""
import argparse
import os
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime, timedelta, timezone
import gzip
import heapq
import json
from pathlib import Path
import sys
import time
import requests
from keyword_guide import compile_descriptors
from featured_guides import FEATURED, compile_featured
from ai_describer import generate_from_evidence
from quality import REVISION, should_refresh, summarize

METADATA = "https://titanium-metadata-provider.onrender.com"
ADVISORY = "https://titanium-advisory-provider.onrender.com"
SCHEMA = "titanium.content-guide.v3"
CATEGORIES = [
    "Violence", "Gore / Injury", "Sex / Nudity",
    "Language", "Alcohol / Drugs", "Frightening",
]
UNKNOWN = "Information not available"


def source_export_candidates(max_rank=100000, export_date=None, session=None):
    """Stream the daily gzip; retain only the most popular IDs in memory."""
    session = session or requests.Session()
    base_day = export_date or datetime.now(timezone.utc).date() - timedelta(days=1)
    dates = [base_day - timedelta(days=n) for n in range(3)]
    last_error = None
    for day in dates:
        url = f"https://files.tmdb.org/p/exports/movie_ids_{day:%m_%d_%Y}.json.gz"
        try:
            response = session.get(url, stream=True, timeout=(15, 90))
            response.raise_for_status()
            response.raw.decode_content = False
            top = []
            with response, gzip.GzipFile(fileobj=response.raw) as archive:
                for raw in archive:
                    try:
                        row = json.loads(raw)
                        if row.get("adult") or row.get("video"):
                            continue
                        movie_id = int(row.get("id", 0))
                        popularity = float(row.get("popularity", 0) or 0)
                        if movie_id <= 0 or popularity < 0:
                            continue
                        pair = (popularity, movie_id)
                        if len(top) < max_rank:
                            heapq.heappush(top, pair)
                        elif pair > top[0]:
                            heapq.heapreplace(top, pair)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        continue
            return [movie_id for _, movie_id in sorted(top, reverse=True)]
        except requests.RequestException as exc:
            last_error = exc
    raise RuntimeError(f"TMDB daily export unavailable: {last_error}")


def record_path(root, movie_id):
    return root / f"{movie_id // 1000:06d}" / f"{movie_id}.json"


def should_fetch(path, now):
    if not path.exists():
        return True
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
        return should_refresh(saved, now)
    except (OSError, ValueError, TypeError):
        return True


def six_point_guide(tags):
    normalized = {str(t).strip().upper() for t in tags}
    def pick(options, phrase):
        return phrase if normalized.intersection(options) else UNKNOWN
    lines = [
        pick({"GRAPHIC VIOLENCE", "VIOLENCE"}, "Violence reported"),
        pick({"GORE", "BLOODY INJURY", "GRAPHIC INJURY", "INJURY"}, "Bloody injury / gore reported"),
        pick({"SEXUAL CONTENT", "NUDITY", "SEX", "SEX / NUDITY"}, "Sexual content / nudity reported"),
        pick({"STRONG LANGUAGE", "LANGUAGE", "PROFANITY"}, "Strong language reported" if "STRONG LANGUAGE" in normalized else "Language reported"),
        pick({"DRUG USE", "ALCOHOL", "SMOKING"}, "Alcohol, drugs or smoking reported"),
        pick({"FRIGHTENING SCENES", "HORROR", "THREAT", "SELF-HARM", "ANIMAL HARM"}, "Frightening / distressing content reported"),
    ]
    return [f"{category} — {description}" for category, description in zip(CATEGORIES, lines)]


def get_json_with_retry(session, url, *, params=None, attempts=3, read_timeout=100):
    """Allow free Render services time to wake; retry transient failures."""
    for attempt in range(attempts):
        try:
            response = session.get(
                url, params=params, timeout=(15, read_timeout)
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            if attempt == attempts - 1:
                raise
            time.sleep(min(3 * (attempt + 1), 10))


_THREAD_CONTEXT = threading.local()


def _worker_session():
    # requests.Session is not shared across worker threads.
    session = getattr(_THREAD_CONTEXT, "session", None)
    if session is None:
        session = requests.Session()
        _THREAD_CONTEXT.session = session
    return session


def compile_movie(movie_id, session=None):
    session = session or requests.Session()
    wrapper = get_json_with_retry(
        session, f"{METADATA}/details/movie/{movie_id}", read_timeout=120
    )
    if not wrapper.get("ok") or not isinstance(wrapper.get("item"), dict):
        raise ValueError("Metadata missing or invalid")
    movie = wrapper["item"]
    title = str(movie.get("title") or "").strip()
    year = str(movie.get("year") or "").strip()
    if not title:
        raise ValueError("No matching movie title")
    advisory = get_json_with_retry(
        session,
        f"{ADVISORY}/advisory",
        params={"title": title, "year": year, "type": "movie"},
        read_timeout=75,
    )
    if not advisory.get("ok"):
        raise ValueError("Advisory service unavailable")
    tags = advisory.get("tags") if isinstance(advisory.get("tags"), list) else []
    matched = bool(advisory.get("match"))
    keywords = movie.get("keywords", [])
    if not isinstance(keywords, list):
        keywords = []
    descriptors, category_evidence = compile_descriptors(
        tags if matched else [], keywords,
        advisory.get("consumer_advice", "") if matched else ""
    )
    # Prefer individually source-checked six-sentence entries over thematic
    # keyword estimates, while preserving the source links per category.
    reviewed = compile_featured(movie_id, title, year)
    if reviewed is not None:
        descriptors, category_evidence = reviewed
    elif matched:
        generated = generate_from_evidence(
            title, year,
            str(advisory.get("consumer_advice") or ""),
            str(advisory.get("source") or ""),
        )
        if generated is not None:
            descriptors, category_evidence = generated
    quality = summarize(descriptors, category_evidence)
    # A 'no match' is not evidence that any warning is absent.
    return {
        "schema": SCHEMA,
        "tmdb_id": movie_id,
        "imdb_id": str(movie.get("imdb_id") or ""),
        "title": title,
        "year": year,
        "certification": str(movie.get("certification") or ""),
        "certification_source": str(movie.get("certification_source") or ""),
        "vote_average": movie.get("vote_average", 0),
        "matched_advisory": matched,
        "source": str(advisory.get("source") or "none") if matched else "none",
        "consumer_advice": str(advisory.get("consumer_advice") or "") if matched else "",
        "advisory_tags": tags if matched else [],
        "keywords": keywords,
        "content_descriptors": descriptors,
        "category_evidence": category_evidence,
        "guide_revision": REVISION,
        "guide_quality": quality,
        "matched_url": str(advisory.get("matched_url") or "") if matched else "",
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="catalog/data")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--top", type=int, default=100000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--sleep", type=float, default=0.0,
                        help="Delay between queued requests, if rate limited")
    parser.add_argument("--ids", default="",
                        help="Optional comma-separated IDs for smoke tests")
    args = parser.parse_args()
    if args.batch_size < 1 or args.top < 1:
        parser.error("batch-size and top must be positive")
    if args.workers < 1 or args.workers > 4:
        parser.error("workers must be between 1 and 4 to protect Render")
    if args.sleep < 0:
        parser.error("sleep must not be negative")

    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    ids = (
        [int(x.strip()) for x in args.ids.split(",") if x.strip()]
        if args.ids else list(FEATURED) + source_export_candidates(args.top)
    )

    # Select one small bounded set. Existing published records stay intact.
    pending = []
    seen = set()
    for movie_id in ids:
        if movie_id in seen or movie_id <= 0:
            continue
        seen.add(movie_id)
        if should_fetch(record_path(root, movie_id), now):
            pending.append(movie_id)
        if len(pending) >= args.batch_size:
            break

    print(
        f"START queued={len(pending)} workers={args.workers} "
        f"batch_limit={args.batch_size}",
        flush=True,
    )

    def compile_one(movie_id):
        try:
            return movie_id, compile_movie(movie_id, _worker_session()), None
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            return movie_id, None, str(exc)

    wrote, failed = 0, 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        # map preserves the input order. Disk writes and final Git commit
        # remain single-threaded, avoiding partially written JSON.
        for movie_id, record, error in pool.map(compile_one, pending):
            if error is not None:
                failed += 1
                print(f"SKIP {movie_id}: {error}", file=sys.stderr, flush=True)
                continue
            path = record_path(root, movie_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            wrote += 1
            print(
                f"STORED {movie_id} {record['title']} "
                f"matched={record['matched_advisory']}",
                flush=True,
            )
            if args.sleep:
                time.sleep(args.sleep)

    print(
        f"COMPLETE attempted={len(pending)} stored={wrote} failed={failed}",
        flush=True,
    )
    if pending and not wrote:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
