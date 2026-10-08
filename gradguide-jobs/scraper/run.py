"""CLI:  python -m scraper.run            (scrape everything in sources.yaml)
        python -m scraper.run --fixtures (load offline test HTML, to try the UI without network)"""
import argparse, glob, os, yaml
import db
from scraper.fetch import Fetcher
from scraper.parse import jsonld_jobs, css_jobs, links
from scraper.enrich import enrich

def scrape_source(src, fetcher):
    html = fetcher.get(src["url"])
    if src["kind"] == "css":
        return css_jobs(html, src["url"], src)
    raw = jsonld_jobs(html, src["url"])                      # list page itself may carry JobPostings
    for link in links(html, src["url"], src["link_selector"])[: src.get("max_jobs", 40)]:
        try: raw += [dict(j, url=j["url"] if j["url"] != src["url"] else link) for j in jsonld_jobs(fetcher.get(link), link)]
        except Exception as e: print(f"  skip {link}: {e}")
    return raw

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--fixtures", action="store_true"); a = ap.parse_args()
    c, n = db.conn(), 0
    if a.fixtures:
        base = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures")
        for f in glob.glob(os.path.join(base, "*.html")):
            html = open(f, encoding="utf-8").read()
            cfg = {"item": "div.opening", "employer": "Fixture Cafe", "fields": {"title": "a", "link": "a@href", "location": "span.loc"}}
            raw = jsonld_jobs(html, "https://fixture.test/" + os.path.basename(f)) or css_jobs(html, "https://fixture.test/", cfg)
            for r in raw: db.upsert(c, enrich(r, "fixture")); n += 1
    else:
        fetcher = Fetcher(delay=2.0)
        for src in yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "..", "sources.yaml")))["sources"]:
            print("Scraping", src["name"])
            try:
                for r in scrape_source(src, fetcher): db.upsert(c, enrich(r, src["name"])); n += 1
            except Exception as e: print("  failed:", e)
    c.commit(); print(f"Stored {n} listings")

if __name__ == "__main__": main()
