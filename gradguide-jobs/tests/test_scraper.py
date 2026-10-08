import os
from scraper.parse import jsonld_jobs, css_jobs
from scraper.enrich import enrich, parse_pay, parse_hours
F = os.path.join(os.path.dirname(__file__), "fixtures")
read = lambda n: open(os.path.join(F, n), encoding="utf-8").read()

def test_jsonld_and_enrich():
    raw = jsonld_jobs(read("jsonld_job.html"), "https://x.test/1")[0]
    job = enrich(raw, "t")
    assert job["title"] == "Barista (Casual)" and job["employer"] == "Corner Cafe"
    assert job["job_type"] == "part-time" and job["category"] == "hospitality"
    assert job["pay_min"] == 26 and job["hours_per_week"] == 15 and job["student_friendly"] == 1
    assert job["trust_score"] >= 90

def test_css_and_scam_flags():
    cfg = {"item": "div.opening", "employer": "Shop", "fields": {"title": "a", "link": "a@href", "location": "span.loc"}}
    jobs = [enrich(r, "t") for r in css_jobs(read("css_list.html"), "https://x.test/", cfg)]
    assert len(jobs) == 2 and jobs[0]["url"] == "https://x.test/jobs/1"
    assert jobs[1]["trust_score"] < 70 and any("Unrealistic" in f for f in jobs[1]["flags"])

def test_pay_and_hours():
    assert parse_pay("$24-28 per hour") == (24, 28)
    assert parse_pay("$65,000 pa")[0] == round(65000 / 1976, 2)
    assert parse_hours("up to 20 hours per week") == 20
