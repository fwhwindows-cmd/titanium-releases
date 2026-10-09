# Titanium source-verified Content Guide enrichment

The scheduled GitHub Actions builder automatically fills **only categories
supported by evidence** from the existing NZ/AU classification advisory. It
revisits high-popularity incomplete films after 3 days (top 200) or 7 days
(top 1,500). The usual longer refresh periods remain for other titles.
A one-time revision flag processes existing generic records progressively.

This is not a scene-by-scene review: short classification terms will not
magically supply six detailed categories. The `guide_quality` field clearly
distinguishes generic advisories from detailed, sourced guidance.

## Licensed detailed guide feed (optional and off by default)

Bulk BBFC and Common Sense Media data access may require agreements.
Do **not** scrape or redistribute protected guides without permission.
An authorised feed can be connected by setting this repository's GitHub
Actions variable `TITANIUM_EVIDENCE_FEED_URL` and secret
`TITANIUM_EVIDENCE_FEED_TOKEN`. Leave both unset until permission is secured.
No Android app change or Android/API secrets are involved.

The feed is queried over HTTPS with a bearer token and three URL parameters:
`tmdb_id`, `title`, and `year`. Respond with JSON:

```json
{
  "rights": "licensed-for-titanium",
  "tmdb_id": 123,
  "title": "Exact Movie Title",
  "year": "2026",
  "categories": {
    "Violence": {
      "summary": "An independently verified, original one-sentence description.",
      "source_url": "https://licensed.example.org/film/123",
      "reviewed": true
    }
  }
}
```

Supported category names: Violence; Sex & Nudity; Profanity;
Alcohol, Drugs & Smoking; Frightening & Intense Scenes;
Mature Content & Themes. Each category needs independently verified evidence
and a HTTPS source URL. Partial responses are allowed. Unknown stays unknown.
The feed must supply correct licensing rights; the application does not grant
these by setting a flag. Existing human-reviewed seeds take precedence.
