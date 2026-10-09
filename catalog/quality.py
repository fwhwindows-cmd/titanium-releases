"""Evidence quality measurements for Titanium's evolving content guides.

Film-count is not detailed-guide-count. Never mistake a one-word
classification descriptor or a TMDB theme for a scene-verified review.
"""
from datetime import datetime, timezone

CATEGORIES = (
    "Violence", "Sex & Nudity", "Profanity", "Alcohol, Drugs & Smoking",
    "Frightening & Intense Scenes", "Mature Content & Themes",
)
REVISION = 1
UNKNOWN = "Information not available"


def summarize(descriptions, evidence):
    detailed = 0
    source_tagged = 0
    themes = 0
    unknown = 0
    for category, description in zip(CATEGORIES, descriptions):
        value = description.partition(" — ")[2].strip()
        item = evidence.get(category, {}) if isinstance(evidence, dict) else {}
        basis = item.get("basis", "unknown") if isinstance(item, dict) else "unknown"
        if value == UNKNOWN or basis == "unknown":
            unknown += 1
        elif basis in {"source_review", "ai_summary_source_advisory"}:
            detailed += 1
        elif basis == "source_advisory":
            source_tagged += 1
        elif basis == "tmdb_keywords":
            themes += 1
        else:
            unknown += 1

    if detailed:
        grade = "detailed"
    elif source_tagged:
        grade = "advisory_summary"
    elif themes:
        grade = "thematic"
    else:
        grade = "unknown"
    return {
        "grade": grade,
        "detailed_categories": detailed,
        "source_tagged_categories": source_tagged,
        "thematic_categories": themes,
        "unknown_categories": unknown,
        "complete": detailed == len(CATEGORIES),
    }


def refresh_after_days(saved):
    quality = saved.get("guide_quality") or {}
    grade = quality.get("grade", "unknown")
    evidence = saved.get("category_evidence") or {}
    if grade == "detailed":
        # Completed source-reviewed guides are stable. Partially reviewed
        # guides can be revisited when more source-backed evidence arrives.
        # Legacy records without a complete field retain old protection.
        if quality.get("complete") is False:
            return 14
        for value in evidence.values():
            if isinstance(value, dict) and value.get("basis") == "source_review":
                return None
        return 30
    if grade == "advisory_summary":
        return 30
    if grade == "thematic":
        return 21
    return 14


def should_refresh(saved, now=None):
    if not isinstance(saved, dict):
        return True
    if saved.get("schema") != "titanium.content-guide.v3":
        return True
    if saved.get("guide_revision") != REVISION or not isinstance(
        saved.get("guide_quality"), dict
    ):
        return True
    days = refresh_after_days(saved)
    if days is None:
        return False
    now = now or datetime.now(timezone.utc)
    try:
        checked = datetime.fromisoformat(
            str(saved["checked_at"]).replace("Z", "+00:00")
        )
        if checked.tzinfo is None:
            checked = checked.replace(tzinfo=timezone.utc)
        return (now - checked).total_seconds() >= days * 86400
    except (ValueError, KeyError, TypeError):
        return True
