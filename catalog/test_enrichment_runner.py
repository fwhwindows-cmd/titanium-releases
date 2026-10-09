"""Automatic enrichment and prioritisation regression checks."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from advice_enrichment import enrich
from approved_evidence import validate, fetch_approved, merge
from build import should_fetch
from keyword_guide import CATEGORIES
from quality import REVISION, summarize, should_refresh

NOW = datetime(2026, 10, 9, tzinfo=timezone.utc)

def blank():
    return ([name + " — Information not available" for name in CATEGORIES],
            {name: {"basis":"unknown"} for name in CATEGORIES})

class EnrichmentTests(unittest.TestCase):
    def test_specific_advice_grounded_not_six_fabricated(self):
        d, e = blank()
        d, e = enrich(d, e,
            "Violence, offensive language, domestic violence, and dangerous behaviour",
            "nz_classification", "https://example.org/advisory")
        self.assertIn("domestic violence", d[0])
        self.assertIn("offensive language", d[2])
        self.assertIn("domestic abuse", d[5])
        self.assertTrue(all("Information not available" in d[i] for i in (1,3,4)))
        self.assertEqual(e["Violence"]["basis"], "source_advisory")
        self.assertEqual(summarize(d, e)["detailed_categories"], 0)
    def test_review_not_overwritten(self):
        d, e = blank()
        d[0] = "Violence — Independently confirmed bloody scene."
        e["Violence"] = {"basis":"source_review"}
        found, _ = enrich(d, e, "graphic violence")
        self.assertEqual(found[0], d[0])
    def test_no_unmatched_word_fragments(self):
        d, e = blank()
        found, _ = enrich(d, e, "Advanced linguistic techniques")
        self.assertEqual(found, d)
    def test_approved_feed_needs_licensed_exact_identity(self):
        item = {"tmdb_id":123,"title":"Movie","year":"2026",
                "rights":"licensed-for-titanium",
                "categories":{"Violence":{"summary":"A verified extended physical confrontation is described.",
                                         "source_url":"https://example.org/movie", "reviewed":True},
                              "Profanity":{"summary":"Unsupported writer guess about curses.",
                                         "source_url":"https://example.org/movie", "reviewed":False}}}
        self.assertIsNone(validate(item,124,"Movie","2026"))
        self.assertIsNone(validate({**item,"rights":"other"},123,"Movie","2026"))
        approved = validate(item,123,"Movie","2026")
        d, e = blank()
        out, ev = merge(d,e,approved)
        self.assertIn("verified",out[0])
        self.assertEqual(out[2],d[2])
        self.assertEqual(ev["Violence"]["basis"],"source_review")
    def test_feed_disabled_without_explicit_configuration(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(fetch_approved(123,"Movie","2026"))
    def test_quality_refresh_and_popular_priority(self):
        record = {"schema":"titanium.content-guide.v3",
                  "tmdb_id": 88888888, "title":"Test", "year":"2026",
                  "guide_revision": REVISION,
                  "guide_enrichment_revision":1,
                  "guide_quality":{"grade":"advisory_summary"},
                  "content_descriptors":[],
                  "category_evidence":{},
                  "checked_at":(NOW - timedelta(days=4)).isoformat()}
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"test.json"
            path.write_text(json.dumps(record),encoding="utf-8")
            self.assertTrue(should_fetch(path,NOW,100))
            self.assertFalse(should_fetch(path,NOW,2000))
            record["checked_at"]=(NOW - timedelta(days=1)).isoformat()
            path.write_text(json.dumps(record),encoding="utf-8")
            self.assertFalse(should_fetch(path,NOW,100))
            record.pop("guide_enrichment_revision")
            path.write_text(json.dumps(record),encoding="utf-8")
            self.assertTrue(should_fetch(path,NOW,100))
    def test_partial_review_can_refresh_without_losing_full_review(self):
        record={"schema":"titanium.content-guide.v3","guide_revision":REVISION,
                "guide_quality":{"grade":"detailed","complete":False},
                "category_evidence":{"Violence":{"basis":"source_review"}},
                "checked_at":(NOW-timedelta(days=15)).isoformat()}
        self.assertTrue(should_refresh(record,NOW))
        record["guide_quality"]["complete"]=True
        self.assertFalse(should_refresh(record,NOW))

if __name__ == "__main__":
    unittest.main()
