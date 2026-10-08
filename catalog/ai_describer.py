"""Optional source-grounded AI descriptions for Titanium catalogue builds.

Runs only in GitHub Actions / backend. Never export an OpenAI API key to
Godot/Android. Not enabled unless TITANIUM_AI_ENABLED=1, OPENAI_API_KEY is
present, and substantive human-written consumer advice was retrieved.
"""
import os
import requests
from keyword_guide import CATEGORIES, UNKNOWN

KEYS = (
    "violence", "sex_and_nudity", "profanity",
    "alcohol_drugs", "frightening", "mature_themes",
)
FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "titanium_movie_content_guide",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {key: {"type": "string"} for key in KEYS},
            "required": list(KEYS),
            "additionalProperties": False,
        },
    },
}


def generate_from_evidence(title, year, advice, source):
    """Returns (six labelled sentences, provenance) or None.

    Does not use a film title alone as a prompt. A title/genre/score cannot
    prove violent or sexual scenes. Missing information stays unknown.
    """
    if os.getenv("TITANIUM_AI_ENABLED") != "1":
        return None
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or len(advice.strip()) < 60:
        return None
    max_words = 1500
    advice = advice.strip()[:max_words * 7]
    payload = {
        "model": os.getenv("TITANIUM_AI_MODEL", "gpt-4o-mini"),
        "temperature": 0,
        "response_format": FORMAT,
        "messages": [
            {"role": "system", "content": (
                "You create evidence-grounded, parent-friendly content guides. "
                "For each of the six fields, write ONE concise descriptive "
                "sentence citing ONLY explicit details in the provided "
                "independent consumer advice. Do not rely on your memory of "
                "the movie, title, genre, keyword labels or age rating. "
                "If a field is not supported by that advice, respond exactly "
                "'Information not available'. A missing mention is NOT proof "
                "that a scene is absent. Avoid copying source sentences verbatim."
            )},
            {"role": "user", "content": (
                f"Film: {title} ({year})\nVerified source identifier: {source}\n"
                f"Consumer advice evidence:\n{advice}"
            )},
        ],
    }
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            timeout=(10, 60),
        )
        response.raise_for_status()
        value = response.json()["choices"][0]["message"]["content"]
        import json
        parsed = json.loads(value)
        if not isinstance(parsed, dict) or set(parsed) != set(KEYS):
            return None
        descriptors = []
        for category, field in zip(CATEGORIES, KEYS):
            sentence = parsed[field]
            if not isinstance(sentence, str) or not sentence.strip():
                return None
            # Bound display length. The script must not invent words when
            # truncating; reject excessively long descriptions entirely.
            if len(sentence) > 340:
                return None
            descriptors.append(category + " — " + sentence.strip())
        evidence = {
            category: {"basis": "ai_summary_source_advisory", "source": source}
            for category in CATEGORIES
        }
        return descriptors, evidence
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError):
        return None
