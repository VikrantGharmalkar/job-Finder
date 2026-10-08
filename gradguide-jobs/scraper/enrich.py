"""Turn a raw scraped job into a student-oriented record: type, category, pay, hours, trust flags."""
import re

TYPE_RULES = [
    ("internship", r"\b(intern|internship|work experience|placement|co-?op|graduate program)\b"),
    ("part-time", r"\b(part[- ]?time|casual|weekend|shifts?|barista|crew member|waiter|waitress|kitchen hand|dishwasher|"
                  r"delivery|rider|retail assistant|sales assistant|cashier|tutor|team member|host(ess)?|server)\b"),
    ("full-time", r"\bfull[- ]?time|permanent\b"),
]
CATEGORIES = {
    "hospitality": r"barista|cafe|café|waiter|waitress|kitchen|chef|restaurant|bartender|hospitality|server",
    "retail": r"retail|sales assistant|cashier|store|shop|stock",
    "delivery": r"deliver|rider|courier|driver|uber|doordash",
    "tutoring": r"tutor|teaching assistant|instructor|coach",
    "tech": r"software|developer|engineer|data|analyst|it support|qa\b",
    "campus": r"campus|library|research assistant|student ambassador",
}
SCAM = [
    (r"registration fee|processing fee|pay (a )?(deposit|fee)|buy (a )?(starter|kit)", "Asks you to pay money"),
    (r"whats?app|telegram|signal only", "Contact only via chat app"),
    (r"\b[\w.]+@(gmail|yahoo|hotmail|outlook)\.com", "Personal email address"),
    (r"earn \$?\d{3,}\s*(/|per)\s*(day|hour)|guaranteed income|easy money|no experience.{0,20}high (pay|income)", "Unrealistic pay promise"),
    (r"send (a )?(copy of )?(passport|bank|tax file|ssn|id)", "Asks for ID/bank details upfront"),
]
FRIENDLY = r"visa|international students?|students? welcome|student[- ]friendly|flexible (hours|shifts)|no experience (needed|required)|will train|around (your )?(study|classes|uni)"

def classify(text, employment_type=""):
    et = employment_type.upper()
    if "INTERN" in et: return "internship"
    if "PART" in et or "CASUAL" in et or "TEMP" in et: return "part-time"
    if "FULL" in et: return "full-time"
    t = text.lower()
    for name, rx in TYPE_RULES:
        if re.search(rx, t): return name
    return "full-time"

def categorize(text):
    t = text.lower()
    for name, rx in CATEGORIES.items():
        if re.search(rx, t): return name
    return "other"

PAY_RX = re.compile(r"(?:[$£€₹]|AUD|NZD|CAD|USD)\s?(\d[\d,]*(?:\.\d+)?)(?:\s*(?:-|–|to)\s*[$£€₹]?\s*(\d[\d,]*(?:\.\d+)?))?"
                    r"\s*(?:/|per|an?|p\.?)?\s*(hour|hr|h|week|wk|year|yr|annum|pa|k)?\b", re.I)

def parse_pay(text):
    """Return (lo_hourly, hi_hourly) from free text like '$24-28 per hour' or '$65,000 pa'."""
    m = PAY_RX.search(text or "")
    if not m: return None, None
    lo = float(m.group(1).replace(",", "")); hi = float(m.group(2).replace(",", "")) if m.group(2) else lo
    unit = (m.group(3) or "").lower()
    div = {"hour": 1, "hr": 1, "h": 1, "week": 38, "wk": 38, "year": 1976, "yr": 1976, "annum": 1976, "pa": 1976}.get(unit)
    if div is None:                                  # no unit: guess from magnitude
        div = 1 if hi < 150 else 1976 if hi > 20000 else None
    if div is None: return None, None
    return round(lo / div, 2), round(hi / div, 2)

def parse_hours(text):
    m = re.search(r"(?:up to |max(?:imum)? |approx\.? )?(\d{1,2})\s*(?:(?:-|–|to)\s*(\d{1,2}))?\s*(?:hours?|hrs?)\s*(?:per|a|/|each)\s*week", text or "", re.I)
    return float(m.group(2) or m.group(1)) if m else None

def enrich(raw, source):
    desc = raw.get("description") or ""
    text = f"{raw.get('title','')} {raw.get('employment_type','')} {desc}"
    lo, hi = raw.get("pay_min"), raw.get("pay_max")
    pay_text = raw.get("pay_text") or ""
    if lo is None:
        lo, hi = parse_pay(pay_text or desc)
        if not pay_text and lo is not None:
            m = PAY_RX.search(desc); pay_text = m.group(0).strip() if m else ""
    flags, score = [], 70
    for rx, label in SCAM:
        if re.search(rx, text, re.I): flags.append("⚠ " + label); score -= 25
    if lo is not None: score += 10
    else: flags.append("ℹ Pay not listed")
    if raw.get("employer"): score += 10
    friendly = bool(re.search(FRIENDLY, text, re.I))
    if friendly: flags.append("✓ Student-friendly wording")
    return {"url": raw["url"], "title": raw.get("title"), "employer": raw.get("employer") or source,
            "location": raw.get("location"), "pay_text": pay_text or None, "pay_min": lo, "pay_max": hi,
            "job_type": classify(text, raw.get("employment_type", "")), "category": categorize(text),
            "hours_per_week": parse_hours(text), "posted_date": raw.get("posted_date") or None,
            "description": desc[:4000], "source": source, "trust_score": max(0, min(100, score)),
            "flags": flags, "student_friendly": int(friendly)}
