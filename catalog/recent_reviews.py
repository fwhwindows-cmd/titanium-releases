"""Reviewed UK-first six-category summaries for recent movies.

Original paraphrases from independently checked public classification reviews.
Never infer a category is absent simply because it was not mentioned.
Both 2026 Runner films are keyed by their distinct TMDB IDs.
"""

RECENT_SOURCES = {
    "runner_2026_bbfc": "https://www.bbfc.co.uk/release/runner-q29sbgvjdglvbjpwwc0xmte4ntq0",
    "the_runner_2026_csm": "https://www.commonsensemedia.org/movie-reviews/the-runner-2026"
}

RECENT_FEATURED = {
    1377237: {
        "title": "Runner",
        "year": "2026",
        "descriptions": {
            "Violence": "Repeated bloody action includes shootings, stabbings, fistfights and injuries from bladed weapons.",
            "Sex & Nudity": "Brief visual references to sex workers occur; the classification report does not establish explicit nudity.",
            "Profanity": "Strong swearing is heard throughout, alongside milder insults and exclamations.",
            "Alcohol, Drugs & Smoking": "There are references to alcohol addiction and a person attending Alcoholics Anonymous.",
            "Frightening & Intense Scenes": "Gun and knife threats, dangerous car crashes, explosions and threats to a seriously ill child create sustained peril.",
            "Mature Content & Themes": "The plot involves a criminal cartel, a vital medical delivery and references to the death of a child."
        },
        "sources": {
            "Violence": [
                "runner_2026_bbfc"
            ],
            "Sex & Nudity": [
                "runner_2026_bbfc"
            ],
            "Profanity": [
                "runner_2026_bbfc"
            ],
            "Alcohol, Drugs & Smoking": [
                "runner_2026_bbfc"
            ],
            "Frightening & Intense Scenes": [
                "runner_2026_bbfc"
            ],
            "Mature Content & Themes": [
                "runner_2026_bbfc"
            ]
        },
    },
    1386315: {
        "title": "The Runner",
        "year": "2026",
        "descriptions": {
            "Violence": "A woman is attacked and threatened, is struck by a car, and encounters bloody crime-scene imagery and references to domestic abuse.",
            "Sex & Nudity": "Suggestive photographs show a woman wearing lingerie, but the available review does not describe explicit sexual activity.",
            "Profanity": "Moderate swearing and insulting language occur during confrontations.",
            "Alcohol, Drugs & Smoking": "There are passing written references to cocaine and intoxication.",
            "Frightening & Intense Scenes": "A kidnapped child faces a life-threatening medical crisis while his mother is forced into dangerous, time-sensitive tasks.",
            "Mature Content & Themes": "Themes include child abduction, emotional manipulation, domestic abuse and misuse of hacked private information."
        },
        "sources": {
            "Violence": [
                "the_runner_2026_csm"
            ],
            "Sex & Nudity": [
                "the_runner_2026_csm"
            ],
            "Profanity": [
                "the_runner_2026_csm"
            ],
            "Alcohol, Drugs & Smoking": [
                "the_runner_2026_csm"
            ],
            "Frightening & Intense Scenes": [
                "the_runner_2026_csm"
            ],
            "Mature Content & Themes": [
                "the_runner_2026_csm"
            ]
        },
    },
}
