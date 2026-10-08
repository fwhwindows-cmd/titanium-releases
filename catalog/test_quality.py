import unittest
from datetime import datetime, timedelta, timezone
from featured_guides import compile_featured
from quality import CATEGORIES, REVISION, summarize, should_refresh

NOW = datetime(2026, 10, 8, tzinfo=timezone.utc)


class GuideQualityTests(unittest.TestCase):
    def test_generic_advisory_is_not_detailed(self):
        descriptions = [x + " — Information not available" for x in CATEGORIES]
        descriptions[0] = "Violence — The classification identifies violent content."
        evidence = {"Violence": {"basis": "source_advisory"}}
        score = summarize(descriptions, evidence)
        self.assertEqual(score["grade"], "advisory_summary")
        self.assertEqual(score["detailed_categories"], 0)
        self.assertEqual(score["unknown_categories"], 5)
        self.assertFalse(score["complete"])

    def test_keyword_only_is_not_verified(self):
        descriptions = [x + " — Information not available" for x in CATEGORIES]
        descriptions[0] = "Violence — TMDB tags murder as a story theme."
        score = summarize(descriptions, {
            "Violence": {"basis": "tmdb_keywords"}
        })
        self.assertEqual(score["grade"], "thematic")
        self.assertEqual(score["detailed_categories"], 0)

    def test_six_reviewed_statements_are_complete(self):
        found = compile_featured(634649, "Spider-Man: No Way Home", "2021")
        self.assertIsNotNone(found)
        descriptions, evidence = found
        score = summarize(descriptions, evidence)
        self.assertEqual(score["detailed_categories"], 6)
        self.assertTrue(score["complete"])

    def test_four_reviewed_statements_not_complete(self):
        found = compile_featured(
            671, "Harry Potter and the Philosopher's Stone", "2001"
        )
        self.assertIsNotNone(found)
        descriptions, evidence = found
        score = summarize(descriptions, evidence)
        self.assertEqual(score["detailed_categories"], 4)
        self.assertEqual(score["unknown_categories"], 2)
        self.assertFalse(score["complete"])

    def test_old_records_refresh_to_receive_quality_metadata(self):
        saved = {
            "schema": "titanium.content-guide.v3",
            "checked_at": NOW.isoformat(),
            "matched_advisory": True,
        }
        self.assertTrue(should_refresh(saved, NOW))

    def test_generic_sources_become_refreshable_after_30_days(self):
        saved = {
            "schema": "titanium.content-guide.v3",
            "guide_revision": REVISION,
            "guide_quality": {"grade": "advisory_summary"},
            "checked_at": (NOW - timedelta(days=31)).isoformat(),
        }
        self.assertTrue(should_refresh(saved, NOW))
        saved["checked_at"] = (NOW - timedelta(days=2)).isoformat()
        self.assertFalse(should_refresh(saved, NOW))

    def test_human_reviewed_record_not_overwritten_automatically(self):
        saved = {
            "schema": "titanium.content-guide.v3",
            "guide_revision": REVISION,
            "guide_quality": {"grade": "detailed"},
            "category_evidence": {
                "Violence": {"basis": "source_review"}
            },
            "checked_at": (NOW - timedelta(days=370)).isoformat(),
        }
        self.assertFalse(should_refresh(saved, NOW))


if __name__ == "__main__":
    unittest.main()
