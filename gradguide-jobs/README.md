# GradGuide Jobs — job discovery for international students

> 🎥 **Video walkthrough:** _paste your link here (Loom/YouTube unlisted)_

Finds part-time/casual (cafés, retail, delivery, tutoring), full-time and internship roles, scraped by my own code, and adds three features built around the real constraints of studying abroad.

## Tech stack
| Layer | Choice | Why |
|---|---|---|
| Scraper | Python, `requests`, `BeautifulSoup4` + `lxml` | Fetch pages, parse HTML myself. No job APIs, no AI scrapers |
| Storage | SQLite | Zero setup, enough for thousands of listings, upsert by URL |
| Backend | Flask | Tiny JSON API with filtering/sorting in SQL |
| Frontend | Vanilla HTML/CSS/JS, `localStorage` | Fast, no build step; tracker data stays on the user's device |
| Tests | pytest on saved HTML fixtures | Parsers are testable offline |

## Run it
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 1. edit sources.yaml with real sites (see "Adding a source")
python -m scraper.run            # scrape -> jobs.db
python app.py                    # open http://127.0.0.1:5000
python -m pytest                 # parser tests
```
`python -m scraper.run --fixtures` loads tiny offline test pages so you can try the UI with no network. **Don't submit with fixture data; the assignment requires real listings.**

## How the scraper works
```
sources.yaml -> Fetcher (robots.txt, 2s delay, retries, UA) -> parse.py -> enrich.py -> SQLite
```
1. **Fetcher** (`scraper/fetch.py`): checks `robots.txt`, rate-limits to one request per 2s, retries with backoff, identifies itself honestly.
2. **Two parsing strategies** (`scraper/parse.py`), chosen per site in `sources.yaml`:
   - `jsonld`: many job pages embed a schema.org `JobPosting` in `<script type="application/ld+json">`. Stable, so it survives redesigns. The scraper follows links from a list page (CSS selector) and reads each one.
   - `css`: for sites without structured data, selectors for item/title/link/location/pay are configured in YAML (`selector@attr` reads an attribute).
3. **Enrichment** (`scraper/enrich.py`): infers job type and category from text, normalises pay to $/hour (hourly, weekly, annual), extracts "N hours per week", detects scam patterns and student-friendly wording.
4. **Upsert** by URL so re-running refreshes rather than duplicates.

**Design choices to defend:** config-driven adapters mean adding a site is YAML, not code; JSON-LD first because it's more robust than layout selectors; `requests` over a headless browser because it's fast and simple (trade-off: JS-rendered sites need a different approach, e.g. their embedded JSON or Playwright); heuristics are transparent regex, not a model, so behaviour is explainable.
**Limits:** no JS rendering, no pagination crawling yet, text heuristics can misclassify.

### Adding a source
Open the site → View Source → check for `application/ld+json` containing `JobPosting` (use `kind: jsonld`) or find the repeating listing element (use `kind: css`). Read the site's robots.txt/terms first. Good targets: café/retail chain career pages, local job boards, university job boards.

## The 3 features and why
1. **Visa work-hour guard.** *Problem:* student visas cap working hours (e.g. AU 48h/fortnight, UK/NZ/IE 20h/week, CA 24h/week off-campus, US F-1 on-campus only). Breaching can mean visa cancellation, yet job ads rarely mention it. *Solution:* choose your country; each listing shows ✓ fits / ⚠ would exceed, based on parsed hours plus the hours of offers you've already accepted, with a live budget bar. Missing hours is flagged as "confirm before accepting" rather than assumed OK. Limits are simplified; users are told to verify officially.
2. **Employer trust signals.** *Problem:* students new to a country don't know local norms and are prime targets for fake jobs (pay-to-start, WhatsApp-only, ID requests, "$500/day, no experience"). *Solution:* each listing gets a 0–100 trust score and visible reasons (✓/⚠ flags); suspicious ones are hidden by default. Missing pay is also flagged, since pay transparency matters when you can't judge market rates.
3. **Application tracker with follow-up reminders.** *Problem:* students apply to dozens of casual jobs quickly and lose track; late follow-ups cost interviews. *Solution:* Save / I applied / interview / offer / rejected; applying sets a 7-day follow-up and a reminder banner appears when due. Stored locally, so no account is needed. Accepting an offer feeds back into Feature 1's hours budget.

## Project layout
```
app.py            Flask API + page          db.py          SQLite schema/upsert
scraper/          fetch.py parse.py enrich.py run.py       sources.yaml  sites to scrape
templates/        index.html (UI)           tests/         parser tests + HTML fixtures
```

## Ideas next
Commute/campus proximity (geocode + distance), pagination crawling, Playwright adapter for JS sites, email reminders, scheduled scraping (cron).
