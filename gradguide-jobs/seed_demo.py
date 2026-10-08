"""Fills jobs.db with DUMMY listings (source 'demo-*') so you can feel the UI before real scraping.
   python seed_demo.py          # add demo data (safe to re-run)
   python seed_demo.py --clear  # remove demo data only
Includes deliberate duplicates: same job posted on several boards, plus exact-URL repeats."""
import sys, datetime as dt
import db
from scraper.enrich import enrich

T = dt.date(2026, 10, 8)
d = lambda n: (T - dt.timedelta(days=n)).isoformat()
# (title, employer, location, employment_type, pay_text, description, days_ago)
JOBS = [
 ("Barista (Casual)", "Corner Cafe", "Melbourne, VIC", "PART_TIME", "$26-29 per hour", "Weekend shifts, 12-15 hours per week. International students welcome, we will train you.", 1),
 ("Barista", "Bean There Coffee", "Sydney, NSW", "PART_TIME", "$25 per hour", "Flexible shifts around your study, up to 18 hours per week. Visa holders welcome.", 2),
 ("Kitchen Hand", "Noodle House", "Melbourne, VIC", "", "$24.50 per hour", "Evening shifts, 15 hours per week. No experience needed.", 3),
 ("Waiter / Waitress", "Harbour Grill", "Sydney, NSW", "", "$27-30 per hour", "Busy restaurant, weekend and evening shifts, 16 hours per week.", 4),
 ("Retail Sales Assistant", "UrbanThreads", "Brisbane, QLD", "PART_TIME", "$25-26 per hour", "Casual retail role, 10-20 hours per week. Students welcome.", 2),
 ("Store Team Member", "FreshMart", "Melbourne, VIC", "", "$24 per hour", "Stocking and cashier duties. Hours vary, flexible hours around classes.", 5),
 ("Cashier", "QuickStop", "Perth, WA", "PART_TIME", "", "Night shifts available. Apply in store.", 6),
 ("Delivery Rider", "SwiftBites", "Melbourne, VIC", "", "$22-35 per hour", "Use your own bike or scooter. Choose your own hours, work up to 20 hours per week.", 1),
 ("Food Delivery Driver", "DashNow", "Sydney, NSW", "", "$20-32 per hour", "Flexible delivery shifts, you decide when to work.", 3),
 ("Maths Tutor (Year 7-10)", "BrightPath Tutoring", "Melbourne, VIC", "PART_TIME", "$40-50 per hour", "After-school sessions, 6 hours per week. Students welcome, training provided.", 2),
 ("English Conversation Tutor", "LinguaLink", "Sydney, NSW", "", "$35 per hour", "Help other international students practise English, 8 hours per week.", 7),
 ("Library Assistant", "Metro University", "Melbourne, VIC", "PART_TIME", "$29 per hour", "On-campus role, 10 hours per week during semester. Current students only.", 4),
 ("Student Ambassador", "Metro University", "Melbourne, VIC", "PART_TIME", "$30 per hour", "Campus tours and open days, up to 12 hours per week. International students encouraged.", 6),
 ("Research Assistant (Campus)", "City Tech University", "Sydney, NSW", "PART_TIME", "$35-40 per hour", "Support a research lab, 12 hours per week.", 9),
 ("Software Engineering Intern", "Nimbus Labs", "Melbourne, VIC", "INTERN", "$30-35 per hour", "3-month summer internship. Visa sponsorship may be available for graduates.", 3),
 ("Data Analyst Intern", "FinGrid", "Sydney, NSW", "INTERN", "$28 per hour", "Placement for penultimate-year students, 3 days per week.", 5),
 ("Marketing Intern", "Pixel & Co", "Brisbane, QLD", "INTERN", "", "Unpaid-looking? No: stipend discussed at interview. Work experience placement.", 8),
 ("Graduate Software Developer", "Nimbus Labs", "Melbourne, VIC", "FULL_TIME", "$85,000 pa", "Full-time graduate role. Visa support available for eligible candidates.", 4),
 ("Customer Support Specialist", "ShipFast", "Sydney, NSW", "FULL_TIME", "$62,000 pa", "Full-time, rotating roster. Bilingual candidates welcome.", 10),
 ("Warehouse Operator", "LogiHub", "Brisbane, QLD", "FULL_TIME", "$26 per hour", "Full-time permanent. Forklift ticket not required, will train.", 12),
 ("Hotel Housekeeper", "Skyline Hotel", "Gold Coast, QLD", "", "$25.50 per hour", "Casual shifts, up to 25 hours per week during peak season.", 5),

 ("Barista", "Daily Grind", "London, UK", "PART_TIME", "£12.50 per hour", "Weekend and evening shifts, up to 16 hours per week. Student visa holders welcome.", 2),
 ("Retail Assistant", "Northside Books", "London, UK", "PART_TIME", "£12 per hour", "Saturday and Sunday shifts, 12 hours per week. Flexible hours around your studies.", 3),
 ("Pizza Delivery Driver", "Slice Brothers", "Manchester, UK", "", "£11-14 per hour", "Evening deliveries, 15 hours per week, tips on top.", 4),
 ("Student Ambassador", "Greenfield University", "Leeds, UK", "PART_TIME", "£13 per hour", "Open days and campus tours, 10 hours per week. International students encouraged.", 5),
 ("Barista", "Maple Roast", "Toronto, ON", "PART_TIME", "$17.50 per hour", "Part-time, 15 hours per week. Students welcome, will train.", 1),
 ("Grocery Clerk", "FreshWay", "Vancouver, BC", "PART_TIME", "$18 per hour", "Evenings and weekends, up to 20 hours per week.", 6),
 ("Tim's Counter Crew", "NorthBrew", "Toronto, ON", "", "$17 per hour", "Casual crew member, flexible shifts, no experience needed.", 8),
 ("Coding Tutor for Kids", "CodeSprout", "Toronto, ON", "PART_TIME", "$30-40 per hour", "Teach Scratch and Python online, 6 hours per week.", 3),
 ("Dining Hall Staff", "Westbrook University", "Boston, MA", "PART_TIME", "$16 per hour", "On-campus job, 15 hours per week during term. F-1 students eligible.", 2),
 ("Campus Library Desk", "Westbrook University", "Boston, MA", "PART_TIME", "$15.50 per hour", "On-campus, 10 hours per week. Current students only.", 5),
 ("Lab Assistant", "Hudson Institute", "New York, NY", "PART_TIME", "$20 per hour", "On-campus research support, up to 12 hours per week.", 7),
 ("Product Design Intern", "Loop Studio", "San Francisco, CA", "INTERN", "$32 per hour", "Summer internship, CPT-eligible for international students.", 4),
 ("Cafe Assistant", "Kiwi Cup", "Auckland, NZ", "PART_TIME", "$23.50 per hour", "Weekend shifts, 14 hours per week. Student visa holders welcome.", 2),
 ("Retail Team Member", "Pacific Outfitters", "Wellington, NZ", "", "$24 per hour", "Casual retail, 12 hours per week, flexible hours.", 6),
 ("Farm Stand Packer", "Green Valley Produce", "Christchurch, NZ", "", "$23 per hour", "Seasonal packing, 18 hours per week.", 9),
 ("Barista", "Liffey Beans", "Dublin, IE", "PART_TIME", "€12.80 per hour", "Part-time, 16 hours per week. International students welcome.", 3),
 ("Pub Server", "The Old Anchor", "Dublin, IE", "", "€12 per hour", "Evening shifts, up to 18 hours per week. Will train.", 5),
 ("Software Intern", "Shamrock Systems", "Dublin, IE", "INTERN", "€18 per hour", "6-month placement for students, hybrid.", 4),
 ("Business Analyst", "Meridian Consulting", "Melbourne, VIC", "FULL_TIME", "$78,000 pa", "Full-time graduate analyst. Visa sponsorship considered.", 6),
 ("Registered Nurse Assistant", "CareWell Aged Care", "Adelaide, SA", "PART_TIME", "$29 per hour", "Casual shifts, 20 hours per week. Training provided.", 3),
 ("Cinema Crew", "Starlight Cinemas", "Sydney, NSW", "", "$24.50 per hour", "Casual crew, nights and weekends, 10-15 hours per week. Students welcome.", 4),
 ("Gym Front Desk", "FitHub", "Brisbane, QLD", "PART_TIME", "$27 per hour", "Early morning and evening shifts, 12 hours per week.", 7),
 ("Content Writer Intern", "StudyAbroad Weekly", "Remote", "INTERN", "$20 per hour", "Write guides for international students, 10 hours per week, flexible.", 5),
 ("UX Researcher Intern", "Orbit Apps", "Sydney, NSW", "INTERN", "$30 per hour", "Summer placement, 3 days per week.", 8),
 ("Mechanical Engineer", "Atlas Manufacturing", "Melbourne, VIC", "FULL_TIME", "$90,000 pa", "Full-time, graduates welcome, visa support available.", 11),
 ("Event Staff", "PopUp Events", "Perth, WA", "", "$28 per hour", "Casual event shifts, you pick the days, up to 15 hours per week.", 2),
 # suspicious ones
 ("Easy Money Parcel Packer", "QuickCash Co", "Remote", "", "", "Earn $500 per day from home, no experience, high pay! Pay a registration fee of $50 to start. Contact us on WhatsApp.", 1),
 ("Personal Assistant - Urgent", "", "Melbourne, VIC", "", "$60 per hour", "Send a copy of your passport and bank details to hr.recruit@gmail.com to be hired today.", 2),
 ("Data Entry Clerk", "GlobalOnline Jobs", "Remote", "", "", "Guaranteed income, easy money. Telegram only. Processing fee required.", 3),
]
# Same listing re-posted on other boards -> cross-site duplicates (different URL, source)
DUP_IDX = [0, 1, 4, 7, 9, 14, 17]

def build():
    rows = []
    for i, (title, emp, loc, et, pay, desc, ago) in enumerate(JOBS):
        rows.append(("demo-jobboard-a", f"https://demo.test/a/{i}", title, emp, loc, et, pay, desc, ago))
    for n, i in enumerate(DUP_IDX):
        title, emp, loc, et, pay, desc, ago = JOBS[i]
        rows.append(("demo-campus-board", f"https://demo.test/b/{i}", title, emp, loc, et, pay, desc, ago + 1))
        if n % 2 == 0:   # third copy on a different site for some
            rows.append(("demo-careers-page", f"https://demo.test/c/{i}", title.upper() if n == 2 else title, emp, loc, et, pay, desc, ago + 2))
    return rows

def seed(c):
    rows = build() + build()[:5]     # last 5 repeated exactly -> tests URL upsert (no new rows)
    for src, url, title, emp, loc, et, pay, desc, ago in rows:
        raw = {"url": url, "title": title, "employer": emp, "location": loc, "employment_type": et,
               "pay_text": pay, "description": desc, "posted_date": d(ago)}
        db.upsert(c, enrich(raw, src))
    c.commit()
    return c.execute("SELECT COUNT(*) FROM jobs WHERE source LIKE 'demo-%'").fetchone()[0]

def main():
    c = db.conn()
    if "--clear" in sys.argv:
        c.execute("DELETE FROM jobs WHERE source LIKE 'demo-%'"); c.commit(); print("Cleared demo data"); return
    print("Rows in DB:", seed(c))

if __name__ == "__main__": main()
