"""One-shot live check: Render should return public, persisted movie guides."""
import sys
import requests

BASE = "https://titanium-advisory-provider.onrender.com"

for movie_id, title in [(238, "The Godfather"), (10830, "Matilda")]:
    try:
        response = requests.get(
            f"{BASE}/catalog/movie/{movie_id}",
            timeout=(10, 75),
        )
        print(
            f"LIVE_CHECK {movie_id} {title}: HTTP {response.status_code}",
            flush=True,
        )
        response.raise_for_status()
        payload = response.json()
        lines = payload.get("content_descriptors") or []
        print(f"catalog={payload.get('catalog')} match={payload.get('match')} "
              f"cert={payload.get('certification')} rows={len(lines)}", flush=True)
        if len(lines) != 6:
            raise AssertionError("Six descriptions missing")
        if movie_id == 238 and "close-range shootings" not in lines[0]:
            raise AssertionError("Godfather is still showing generic guidance")
        if movie_id == 10830 and "Cartoonish bullying" not in lines[0]:
            raise AssertionError("Matilda is still showing generic guidance")
    except (requests.RequestException, ValueError, AssertionError) as exc:
        print(f"LIVE_ERROR {movie_id} {exc}", flush=True)
        sys.exit(1)
print("BOTH_LIVE_CATALOG_RECORDS_PASS",flush=True)
