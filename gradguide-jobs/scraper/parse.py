"""HTML -> raw job dicts. Two strategies:
 1. jsonld_jobs: schema.org JobPosting in <script type="application/ld+json"> (very common, stable)
 2. css_jobs:    config-driven CSS selectors for sites without structured data
"""
import json, re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def _flatten(node):
    if isinstance(node, list):
        for n in node: yield from _flatten(n)
    elif isinstance(node, dict):
        if "@graph" in node: yield from _flatten(node["@graph"])
        else: yield node

def _text(html):
    return re.sub(r"\s+", " ", BeautifulSoup(html or "", "lxml").get_text(" ")).strip()

def _name(v):
    return v.get("name") if isinstance(v, dict) else v

def _location(jl):
    if isinstance(jl, list): jl = jl[0] if jl else {}
    addr = (jl or {}).get("address", {}) if isinstance(jl, dict) else {}
    if isinstance(addr, str): return addr
    parts = [addr.get("addressLocality"), addr.get("addressRegion"), _name(addr.get("addressCountry"))]
    return ", ".join(p for p in parts if p)

def _salary(bs):
    if not isinstance(bs, dict): return {}
    v = bs.get("value", {})
    if not isinstance(v, dict): v = {"value": v}
    lo, hi = v.get("minValue", v.get("value")), v.get("maxValue", v.get("value"))
    unit = (v.get("unitText") or "").upper()
    div = {"HOUR": 1, "DAY": 7.6, "WEEK": 38, "MONTH": 164, "YEAR": 1976}.get(unit)
    try: lo, hi = float(lo), float(hi if hi is not None else lo)
    except (TypeError, ValueError): return {}
    cur = bs.get("currency", "")
    out = {"pay_text": f"{cur} {lo:g}-{hi:g} / {unit.lower() or 'period'}".strip()}
    if div: out.update(pay_min=round(lo / div, 2), pay_max=round(hi / div, 2))
    return out

def jsonld_jobs(html, url):
    soup, out = BeautifulSoup(html, "lxml"), []
    for tag in soup.find_all("script", type="application/ld+json"):
        try: data = json.loads(tag.string or tag.get_text() or "")
        except json.JSONDecodeError: continue
        for n in _flatten(data):
            t = n.get("@type")
            if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
                et = n.get("employmentType", "")
                job = {"title": n.get("title"), "employer": _name(n.get("hiringOrganization")),
                       "location": _location(n.get("jobLocation")) or ("Remote" if n.get("jobLocationType") == "TELECOMMUTE" else ""),
                       "description": _text(n.get("description")), "posted_date": (n.get("datePosted") or "")[:10],
                       "employment_type": " ".join(et) if isinstance(et, list) else et,
                       "url": n.get("url") or url}
                job.update(_salary(n.get("baseSalary")))
                out.append(job)
    return out

def _pick(el, spec):
    if not spec: return None
    sel, _, attr = spec.partition("@")
    node = el.select_one(sel) if sel else el
    if node is None: return None
    return node.get(attr) if attr else node.get_text(" ", strip=True)

def css_jobs(html, url, cfg):
    soup, out = BeautifulSoup(html, "lxml"), []
    f = cfg["fields"]
    for el in soup.select(cfg["item"]):
        title = _pick(el, f.get("title"))
        link = _pick(el, f.get("link"))
        if not title or not link: continue
        out.append({"title": title, "employer": _pick(el, f.get("employer")) or cfg.get("employer"),
                    "location": _pick(el, f.get("location")) or "", "employment_type": _pick(el, f.get("type")) or "",
                    "pay_text": _pick(el, f.get("pay")) or "", "posted_date": _pick(el, f.get("date")) or "",
                    "description": _pick(el, f.get("description")) or "", "url": urljoin(url, link)})
    return out

def links(html, base_url, selector):
    soup = BeautifulSoup(html, "lxml")
    return list(dict.fromkeys(urljoin(base_url, a["href"]) for a in soup.select(selector) if a.get("href")))
