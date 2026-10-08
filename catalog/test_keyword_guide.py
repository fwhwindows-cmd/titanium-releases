import unittest
from keyword_guide import CATEGORIES, UNKNOWN, compile_descriptors, keyword_hints


class TitaniumContentGuideTests(unittest.TestCase):
    def test_six_stable_headings(self):
        descriptions, evidence = compile_descriptors([], [])
        self.assertEqual(len(descriptions), 6)
        for index, category in enumerate(CATEGORIES):
            self.assertTrue(descriptions[index].startswith(category + " — "))
            self.assertEqual(evidence[category]["basis"], "unknown")

    def test_unknown_does_not_mean_safe(self):
        descriptions, evidence = compile_descriptors([], ["orchestra", "godfather"])
        self.assertTrue(all(x.endswith(UNKNOWN) for x in descriptions))
        self.assertEqual(evidence["Violence"]["basis"], "unknown")

    def test_v2_murder_and_assassination_keywords(self):
        descriptions, evidence = compile_descriptors([], ["mafia", "murder", "assassination"])
        self.assertIn("murder", descriptions[0])
        self.assertIn("assassination", descriptions[0])
        self.assertEqual(evidence["Violence"]["basis"], "tmdb_keywords")
        self.assertEqual(evidence["Sex & Nudity"]["basis"], "unknown")

    def test_authoritative_advice_beats_keyword(self):
        descriptions, evidence = compile_descriptors(
            ["GRAPHIC VIOLENCE", "STRONG LANGUAGE"], ["murder"]
        )
        self.assertEqual(descriptions[0], "Violence — The available classification advice reports graphic violence.")
        self.assertEqual(descriptions[2], "Profanity — The available classification advice reports strong language.")
        self.assertEqual(evidence["Violence"]["basis"], "source_advisory")

    def test_distinct_sex_and_drugs(self):
        descriptions, evidence = compile_descriptors([], [
            "nudity", "cocaine", "psychological horror"
        ])
        self.assertIn("nudity", descriptions[1])
        self.assertIn("cocaine", descriptions[3])
        self.assertIn("psychological horror", descriptions[4])

    def test_substring_does_not_trigger_false_positive(self):
        self.assertEqual(keyword_hints(["warrior"])["Violence"], [])
        self.assertEqual(keyword_hints(["adversary"])["Sex & Nudity"], [])


if __name__ == "__main__":
    unittest.main()
