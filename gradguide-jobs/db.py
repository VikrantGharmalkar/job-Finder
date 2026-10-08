"""SQLite storage. One table, upsert keyed on the listing URL."""
import json, sqlite3, os
DB_PATH = os.environ.get("JOBS_DB", os.path.join(os.path.dirname(__file__), "jobs.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT UNIQUE NOT NULL,
  title TEXT, employer TEXT, location TEXT,
  pay_text TEXT, pay_min REAL, pay_max REAL,      -- hourly estimate
  job_type TEXT, category TEXT, hours_per_week REAL,
  posted_date TEXT, description TEXT, source TEXT,
  trust_score INTEGER, flags TEXT, student_friendly INTEGER,
  scraped_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_type ON jobs(job_type);
"""

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c

COLS = ["url","title","employer","location","pay_text","pay_min","pay_max","job_type","category",
        "hours_per_week","posted_date","description","source","trust_score","flags","student_friendly"]

def upsert(c, job):
    j = dict(job); j["flags"] = json.dumps(j.get("flags", []))
    vals = [j.get(k) for k in COLS]
    sets = ",".join(f"{k}=excluded.{k}" for k in COLS if k != "url")
    c.execute(f"INSERT INTO jobs ({','.join(COLS)}) VALUES ({','.join('?'*len(COLS))}) "
              f"ON CONFLICT(url) DO UPDATE SET {sets}, scraped_at=CURRENT_TIMESTAMP", vals)
