"""Conservative source-grounded enrichment from the existing classification advice.
Never invent scenes, absences, or imply that advisory text is a detailed review.
"""
import re

PHRASES = {
 "Violence": (
  ("domestic violence","domestic violence"),("bloody violence","bloody violence"),
  ("graphic violence","graphic violence"),("sexual violence","sexual violence"),
  ("strong violence","strong violence"),("gun violence","gun violence"),
  ("knife violence","knife violence"),("injury detail","injury detail"),
  ("violence","violence"),("blood","blood")),
 "Sex & Nudity": (
  ("sexual violence","sexual violence"),("sexual threat","sexual threat"),
  ("sexual activity","sexual activity"),("sexual content","sexual material"),
  ("sexual references","sexual references"),("sex references","sexual references"),
  ("sex scenes","sex scenes"),("nudity","nudity")),
 "Profanity": (
  ("very strong language","very strong language"),("strong language","strong language"),
  ("offensive language","offensive language"),("coarse language","coarse language"),
  ("racial slurs","racial slurs"),("discriminatory language","discriminatory language"),
  ("swearing","swearing"),("language","language concerns")),
 "Alcohol, Drugs & Smoking": (
  ("drug dealing","drug dealing"),("drug misuse","drug misuse"),
  ("drug use","drug use"),("drug references","drug references"),
  ("substance misuse","substance misuse"),("alcohol misuse","alcohol misuse"),
  ("alcohol addiction","alcohol addiction"),("alcohol","alcohol"),
  ("smoking","smoking"),("cocaine","cocaine references")),
 "Frightening & Intense Scenes": (
  ("sustained threat","sustained threat"),("strong threat","strong threat"),
  ("frightening scenes","frightening scenes"),("disturbing scenes","disturbing scenes"),
  ("disturbing images","disturbing images"),("horror","horror"),("threat","threat")),
 "Mature Content & Themes": (
  ("domestic violence","domestic abuse"),("child abuse","child abuse"),
  ("child abduction","child abduction"),("sexual violence","sexual violence"),
  ("suicide","suicide"),("self-harm","self-harm"),("racism","racism"),
  ("discrimination","discrimination")),
}

def _extract_phrases(advice, category):
    text = str(advice).casefold()
    found, spans = [], []
    for needle, phrase in PHRASES[category]:
        match = re.search(r"(?<![a-z])" + re.escape(needle) + r"(?![a-z])", text)
        if match is None:
            continue
        if any(start <= match.start() and match.end() <= end for start, end in spans):
            continue
        if phrase not in found:
            found.append(phrase)
            spans.append(match.span())
    return found[:3]

def enrich(descriptions, evidence, consumer_advice, source="", matched_url=""):
    if not isinstance(consumer_advice, str) or not consumer_advice.strip():
        return descriptions, evidence
    descriptions = list(descriptions)
    evidence = {name: dict(item) for name, item in evidence.items()}
    for index, category in enumerate(PHRASES):
        phrases = _extract_phrases(consumer_advice, category)
        if not phrases:
            continue
        existing = evidence.get(category, {})
        if existing.get("basis") in ("source_review","ai_summary_source_advisory"):
            continue
        if len(phrases) == 1 and phrases[0] in ("violence","language concerns","threat"):
            if existing.get("basis") == "source_advisory":
                continue
        descriptions[index] = category + " — Classification advice mentions " + ", ".join(phrases) + "."
        updated = dict(existing)
        updated.update({
            "basis": "source_advisory",
            "classification_source": str(source)[:96],
            "advice_fragments": phrases,
        })
        if isinstance(matched_url, str) and matched_url.startswith("https://"):
            updated["source_url"] = matched_url[:512]
        evidence[category] = updated
    return descriptions, evidence
