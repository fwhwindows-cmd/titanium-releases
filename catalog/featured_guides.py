"""Human-reviewed examples grounded in identifiable independent content guides.

These are short original summaries, not copies of review prose.
A category marked "not present" must have an explicit source stating absence.
Future batch enrichment can replace this small seed library with evidence-backed
generated descriptions, but must retain the six headings and source tracking.
"""
SOURCES = {
    "godfather_bbfc": "https://www.bbfc.co.uk/release/the-godfather-q29sbgvjdglvbjpwwc0yotezmtg",
    "godfather_csm": "https://www.commonsensemedia.org/movie-reviews/the-godfather",
    "matilda_bbfc": "https://www.bbfc.co.uk/release/matilda-q29sbgvjdglvbjpwwc0zmtg5mjq",
    "matilda_csm": "https://www.commonsensemedia.org/movie-reviews/matilda",
    "potter_bbfc": "https://www.bbfc.co.uk/release/harry-potter-and-the-philosophers-stone-q29sbgvjdglvbjpwwc0zmzm2odi",
    "spiderman_bbfc": "https://www.bbfc.co.uk/release/spider-man-no-way-home-more-fun-stuff-q29sbgvjdglvbjpwwc0xmdiymzk4",
}

# Indexed by TMDB movie ID. Every statement is independently paraphrased
# from one or both of the sources given in the category evidence.
FEATURED = {
    238: {
        "title": "The Godfather",
        "year": "1972",
        "descriptions": {
            "Violence": "Includes close-range shootings, a sustained strangling and a scene of domestic abuse involving a belt.",
            "Sex & Nudity": "Includes a brief sexual encounter and short glimpses of female breast nudity.",
            "Profanity": "Contains coarse language alongside offensive racial and ethnic slurs.",
            "Alcohol, Drugs & Smoking": "Characters drink wine and smoke cigarettes, with discussion of heroin, marijuana and Mafia drug dealing.",
            "Frightening & Intense Scenes": "Sudden killings, threats and the discovery of a severed horse's head create disturbing moments.",
            "Mature Content & Themes": "Examines organised crime, family loyalty, corruption and the moral consequences of violence.",
        },
        "sources": {
            "Violence": ["godfather_bbfc", "godfather_csm"],
            "Sex & Nudity": ["godfather_bbfc", "godfather_csm"],
            "Profanity": ["godfather_bbfc", "godfather_csm"],
            "Alcohol, Drugs & Smoking": ["godfather_csm"],
            "Frightening & Intense Scenes": ["godfather_bbfc", "godfather_csm"],
            "Mature Content & Themes": ["godfather_csm"],
        },
    },
    671: {
        "title": "Harry Potter and the Philosopher's Stone",
        "year": "2001",
        "descriptions": {
            "Violence": "A young wizard faces a dangerous enemy, and enchanted chess pieces fight in a life-sized game.",
            "Sex & Nudity": "Information not available",
            "Profanity": "Infrequent mild swearing includes words such as 'bloody' and 'bugger'.",
            "Alcohol, Drugs & Smoking": "Information not available",
            "Frightening & Intense Scenes": "A dungeon troll, a snake pit and a sinister forest pursuit create brief frightening moments.",
            "Mature Content & Themes": "An orphaned boy experiences an unkind home life, and the deaths of his parents are discussed.",
        },
        "sources": {
            "Violence": ["potter_bbfc"],
            "Sex & Nudity": [],
            "Profanity": ["potter_bbfc"],
            "Alcohol, Drugs & Smoking": [],
            "Frightening & Intense Scenes": ["potter_bbfc"],
            "Mature Content & Themes": ["potter_bbfc"],
        },
    },
    634649: {
        "title": "Spider-Man: No Way Home",
        "year": "2021",
        "descriptions": {
            "Violence": "Superheroes and villains clash with heavy punches, fantastical powers and advanced technology.",
            "Sex & Nudity": "Mild sexual references occur, without explicit scene details in the cited guidance.",
            "Profanity": "Mostly mild language is heard, together with a brief, unfinished stronger expression.",
            "Alcohol, Drugs & Smoking": "An undetailed reference to drugs appears.",
            "Frightening & Intense Scenes": "Explosions, falls from heights and sudden villain appearances create threatening moments and jump scares.",
            "Mature Content & Themes": "A superhero's exposed identity creates danger for those close to him and raises questions about responsibility.",
        },
        "sources": {
            "Violence": ["spiderman_bbfc"],
            "Sex & Nudity": ["spiderman_bbfc"],
            "Profanity": ["spiderman_bbfc"],
            "Alcohol, Drugs & Smoking": ["spiderman_bbfc"],
            "Frightening & Intense Scenes": ["spiderman_bbfc"],
            "Mature Content & Themes": ["spiderman_bbfc"],
        },
    },
    10830: {
        "title": "Matilda",
        "year": "1996",
        "descriptions": {
            "Violence": "Cartoonish bullying includes a girl being swung by her hair, a punishment cupboard and a forced cake-eating scene.",
            "Sex & Nudity": "The available parental guide reports no sexual content or nudity.",
            "Profanity": "Contains occasional mild swearing and harsh name-calling directed at children.",
            "Alcohol, Drugs & Smoking": "Adult characters are shown drinking beer; no substantial drug-related content is reported in the cited guide.",
            "Frightening & Intense Scenes": "A cruel headmistress intimidates and chases children, including scenes involving a frightening cupboard.",
            "Mature Content & Themes": "Explores child neglect, emotional cruelty, bullying and a young girl's efforts to stand up to abusive adults.",
        },
        "sources": {
            "Violence": ["matilda_bbfc", "matilda_csm"],
            "Sex & Nudity": ["matilda_csm"],
            "Profanity": ["matilda_bbfc", "matilda_csm"],
            "Alcohol, Drugs & Smoking": ["matilda_bbfc", "matilda_csm"],
            "Frightening & Intense Scenes": ["matilda_bbfc", "matilda_csm"],
            "Mature Content & Themes": ["matilda_csm"],
        },
    },
}


def compile_featured(movie_id, title, year):
    example = FEATURED.get(int(movie_id))
    if not example:
        return None
    if title.strip().casefold() != example["title"].casefold():
        return None
    if year.strip() != example["year"]:
        return None
    from keyword_guide import CATEGORIES
    descriptions = [
        name + " — " + example["descriptions"][name]
        for name in CATEGORIES
    ]
    evidence = {
        name: {
            "basis": "source_review",
            "sources": [SOURCES[key] for key in example["sources"][name]],
        }
        for name in CATEGORIES
    }
    return descriptions, evidence


# Source-checked 2026 releases; exact TMDB ID, title and year still required.
from recent_reviews import RECENT_SOURCES, RECENT_FEATURED
SOURCES.update(RECENT_SOURCES)
FEATURED.update(RECENT_FEATURED)
