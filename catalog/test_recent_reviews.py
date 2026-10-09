"""Tests for two distinct 2026 Runner films and immediate enrichment."""
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone

from build import should_fetch
from featured_guides import FEATURED, compile_featured
from keyword_guide import CATEGORIES
from quality import REVISION, summarize

NOW = datetime(2026, 10, 9, tzinfo=timezone.utc)


class VerifiedRunnerGuideTests(unittest.TestCase):
    def test_identity_never_crosses_runner_titles(self):
        self.assertIsNone(compile_featured(1377237, "The Runner", "2026"))
        self.assertIsNone(compile_featured(1386315, "Runner", "2026"))
        self.assertIsNone(compile_featured(1377237, "Runner", "2025"))

    def test_both_have_six_source_checked_categories(self):
        for mid in (1377237, 1386315):
            item = FEATURED[mid]
            descriptors, evidence = compile_featured(mid, item["title"], item["year"])
            self.assertEqual(len(descriptors), 6)
            self.assertTrue(summarize(descriptors, evidence)["complete"])
            for name, line in zip(CATEGORIES, descriptors):
                self.assertTrue(line.startswith(name + " — "))
                self.assertNotIn("Information not available", line)
                self.assertEqual(evidence[name]["basis"], "source_review")
                self.assertTrue(evidence[name]["sources"])

    def test_new_review_upgrades_fresh_generic_record_once(self):
        film_id = 1377237
        item = FEATURED[film_id]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "runner.json"
            saved = {
                "schema": "titanium.content-guide.v3",
                "guide_revision": REVISION,
                "guide_quality": {"grade": "advisory_summary"},
                "checked_at": NOW.isoformat(),
                "tmdb_id": film_id,
                "title": item["title"],
                "year": item["year"],
                "content_descriptors": [
                    name + " — Information not available" for name in CATEGORIES
                ],
                "category_evidence": {},
            }
            path.write_text(json.dumps(saved), encoding="utf-8")
            self.assertTrue(should_fetch(path, NOW))
            descriptors, evidence = compile_featured(film_id, item["title"], item["year"])
            saved.update({
                "guide_quality": summarize(descriptors, evidence),
                "content_descriptors": descriptors,
                "category_evidence": evidence,
            })
            path.write_text(json.dumps(saved), encoding="utf-8")
            self.assertFalse(should_fetch(path, NOW))


if __name__ == "__main__":
    unittest.main()
