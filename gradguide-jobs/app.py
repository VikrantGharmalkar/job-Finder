import json
from flask import Flask, jsonify, render_template, request
import db

app = Flask(__name__)

# First run with an empty database: load the dummy listings automatically so the UI is never blank.
with db.conn() as _c:
    if _c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
        import seed_demo; seed_demo.seed(_c)

@app.route("/")
def index(): return render_template("index.html")

@app.route("/api/jobs")
def jobs():
    a, where, args = request.args, ["1=1"], []
    if a.get("q"):
        where.append("(title LIKE ? OR employer LIKE ? OR description LIKE ?)"); args += [f"%{a['q']}%"] * 3
    if a.get("type"): where.append("job_type=?"); args.append(a["type"])
    if a.get("category"): where.append("category=?"); args.append(a["category"])
    if a.get("location"): where.append("location LIKE ?"); args.append(f"%{a['location']}%")
    if a.get("min_pay"): where.append("pay_min>=?"); args.append(float(a["min_pay"]))
    if a.get("student_friendly") == "1": where.append("student_friendly=1")
    if a.get("hide_risky") == "1": where.append("trust_score>=60")
    order = {"newest": "posted_date DESC", "pay": "pay_max DESC", "trust": "trust_score DESC"}.get(a.get("sort"), "posted_date DESC")
    with db.conn() as c:
        rows = c.execute(f"SELECT * FROM jobs WHERE {' AND '.join(where)} ORDER BY {order}, id DESC LIMIT 200", args).fetchall()
    out, seen = [], {}
    for r in rows:
        d = dict(r); d["flags"] = json.loads(d["flags"] or "[]"); d["description"] = (d["description"] or "")[:400]
        key = (d["title"] or "").strip().lower(), (d["employer"] or "").strip().lower(), (d["location"] or "").strip().lower()
        if key in seen:                      # same job re-posted on another site: collapse, keep the first
            seen[key]["also_on"].append(d["source"]); continue
        d["also_on"] = []; seen[key] = d; out.append(d)
    return jsonify(out)

@app.route("/api/meta")
def meta():
    with db.conn() as c:
        n, last = c.execute("SELECT COUNT(*), MAX(scraped_at) FROM jobs").fetchone()
        srcs = [r[0] for r in c.execute("SELECT DISTINCT source FROM jobs")]
    return jsonify({"count": n, "last_scraped": last, "sources": srcs})

if __name__ == "__main__": app.run(debug=True)
