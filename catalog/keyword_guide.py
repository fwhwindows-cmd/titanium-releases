"""Evidence-conscious Titanium six-sentence content guide compiler.

Six categories follow the user's Google benchmarking examples. Each compiled
entry tracks whether its text comes from explicit consumer advice, a thematic
TMDB tag, a human-reviewed source, or is genuinely unknown. Never manufacture
scene events or claim "no content" solely because a source omitted a category.
"""
import re

CATEGORIES = [
    "Violence",
    "Sex & Nudity",
    "Profanity",
    "Alcohol, Drugs & Smoking",
    "Frightening & Intense Scenes",
    "Mature Content & Themes",
]
UNKNOWN = "Information not available"

V2_KEYWORD_HINTS = {
    "Violence": [
        ("gun violence", "gun violence"), ("gang violence", "gang violence"),
        ("domestic violence", "domestic violence"), ("shooting", "shootings"),
        ("murder", "murder"), ("assassination", "assassination"),
        ("torture", "torture"), ("fight", "fighting"),
        ("blood", "bloody imagery"), ("gore", "gore"),
        ("dismemberment", "dismemberment"), ("mutilation", "mutilation"),
        ("violence", "violence"), ("abuse", "abuse"),
    ],
    "Sex & Nudity": [
        ("nudity", "nudity"), ("sexual assault", "sexual assault"),
        ("sexual content", "sexual content"), ("sex scene", "sex scenes"),
        ("prostitution", "sex work"), ("erotic", "erotic themes"),
    ],
    "Profanity": [
        ("strong language", "strong language"), ("profanity", "profanity"),
        ("swearing", "swearing"), ("coarse language", "coarse language"),
    ],
    "Alcohol, Drugs & Smoking": [
        ("drug dealing", "drug dealing"), ("drug use", "drug use"),
        ("drug addiction", "drug addiction"), ("narcotic", "narcotics"),
        ("cocaine", "cocaine"), ("heroin", "heroin"),
        ("alcoholism", "alcohol misuse"), ("drinking", "drinking"),
        ("alcohol", "alcohol"), ("smoking", "smoking"),
        ("tobacco", "tobacco"),
    ],
    "Frightening & Intense Scenes": [
        ("psychological horror", "psychological horror"),
        ("supernatural horror", "supernatural horror"),
        ("nightmare", "nightmares"), ("threat", "threat"),
        ("frightening", "frightening themes"), ("terror", "terror"),
        ("horror", "horror"), ("disturbing", "disturbing themes"),
    ],
    "Mature Content & Themes": [
        ("child abuse", "child abuse"), ("child neglect", "child neglect"),
        ("organised crime", "organised crime"), ("organized crime", "organised crime"),
        ("mafia", "Mafia crime"), ("gangster", "gangster crime"),
        ("suicide", "suicide"), ("self-harm", "self-harm"),
        ("racism", "racism"), ("discrimination", "discrimination"),
        ("domestic violence", "domestic violence"),
        ("revenge", "revenge"), ("corruption", "corruption"),
        ("bullying", "bullying"), ("trauma", "trauma"),
    ],
}

SOURCE_TAGS = {
    "Violence": {"GRAPHIC VIOLENCE", "VIOLENCE", "GORE", "GRAPHIC INJURY", "INJURY DETAIL", "STRONG VIOLENCE"},
    "Sex & Nudity": {"SEXUAL CONTENT", "NUDITY", "SEX / NUDITY"},
    "Profanity": {"LANGUAGE", "STRONG LANGUAGE", "PROFANITY"},
    "Alcohol, Drugs & Smoking": {"DRUG USE", "ALCOHOL", "SMOKING", "ALCOHOL / SMOKING"},
    "Frightening & Intense Scenes": {"FRIGHTENING SCENES", "HORROR", "THREAT"},
    "Mature Content & Themes": {"SELF-HARM", "ANIMAL HARM", "DISCRIMINATION"},
}


def keyword_hints(keywords):
    matches = {category: [] for category in CATEGORIES}
    for raw in keywords or []:
        name = str(raw).strip().lower()
        if not name:
            continue
        for category, patterns in V2_KEYWORD_HINTS.items():
            for needle, description in patterns:
                if re.search(r"(?<![a-z])" + re.escape(needle) + r"(?![a-z])", name):
                    if description not in matches[category]:
                        matches[category].append(description)
                    break
    return matches


def compile_descriptors(tags, keywords, consumer_advice=""):
    tags = {str(tag).upper().strip() for tag in (tags or [])}
    hints = keyword_hints(keywords)
    descriptions, evidence = [], {}
    for category in CATEGORIES:
        matched_tags = SOURCE_TAGS[category] & tags
        matched_keywords = hints[category][:4]
        if matched_tags:
            if category == "Violence":
                if "GRAPHIC VIOLENCE" in matched_tags:
                    sentence = "The available classification advice reports graphic violence."
                elif "GORE" in matched_tags:
                    sentence = "The available classification advice reports blood, gore or injury detail."
                else:
                    sentence = "The available classification advice identifies violent content."
            elif category == "Sex & Nudity":
                sentence = "The available classification advice identifies sexual material or nudity."
            elif category == "Profanity":
                sentence = ("The available classification advice reports strong language."
                            if "STRONG LANGUAGE" in matched_tags
                            else "The available classification advice reports some language concerns.")
            elif category == "Alcohol, Drugs & Smoking":
                parts = []
                for tag, label in [("DRUG USE", "drugs"), ("ALCOHOL", "alcohol"),
                                   ("SMOKING", "smoking")]:
                    if tag in matched_tags:
                        parts.append(label)
                if "ALCOHOL / SMOKING" in matched_tags:
                    parts += ["alcohol", "smoking"]
                sentence = "The classification advice mentions " + ", ".join(dict.fromkeys(parts or ["substance use"])) + "."
            elif category == "Frightening & Intense Scenes":
                sentence = "The classification advice reports frightening or distressing material."
            else:
                sentence = "The classification advice identifies mature or sensitive themes."
            basis = "source_advisory"
        elif matched_keywords:
            sentence = ("TMDB lists " + ", ".join(matched_keywords) +
                        " among this film's story themes; specific scenes are unverified.")
            basis = "tmdb_keywords"
        else:
            sentence = UNKNOWN
            basis = "unknown"
        descriptions.append(category + " — " + sentence)
        evidence[category] = {
            "basis": basis,
            "advisory_tags": sorted(matched_tags),
            "keywords": matched_keywords,
        }
    return descriptions, evidence
