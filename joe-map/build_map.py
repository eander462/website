"""Build the economics job-openings map from a JOE XML export.

Usage:
    python3 build_map.py [path/to/joe_full_xml.xml] [-o index.html]

Defaults: reads joe_full_xml.xml in this folder and writes index.html in this folder.
"""
import argparse, html, json, os, re, datetime, xml.etree.ElementTree as ET
from geocode import geocode, key as place_key

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(description="Build the JOE job-openings map.")
ap.add_argument("joe", nargs="?", default=os.path.join(HERE, "joe_full_xml.xml"), help="JOE 'full XML' export")
ap.add_argument("-o", "--out", default=os.path.join(HERE, "index.html"), help="output HTML file")
args = ap.parse_args()
JOE = args.joe

US_STATES = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}
JEL = {"A":"General & Teaching","B":"History of Thought & Methodology","C":"Econometrics & Quantitative Methods","D":"Microeconomics","E":"Macro & Monetary","F":"International","G":"Finance","H":"Public","I":"Health, Education & Welfare","J":"Labor & Demographics","K":"Law & Economics","L":"Industrial Organization","M":"Business & Marketing","N":"Economic History","O":"Development, Innovation & Growth","P":"Political Economy & Systems","Q":"Agricultural, Environmental & Energy","R":"Urban, Rural & Regional","Y":"Miscellaneous","Z":"Other Special Topics"}
CATEGORY = {
    "US: Full-Time Academic (Permanent, Tenure Track or Tenured)": "Academic, tenure-track (US)",
    "International: Full-Time Academic (Permanent, Tenure Track or Tenured)": "Academic, tenure-track (International)",
    "US: Other Academic (Visiting or Temporary)": "Academic, visiting/postdoc (US)",
    "International: Other Academic (Visiting or Temporary)": "Academic, visiting/postdoc (International)",
    "US: Other Academic (Part-time or Adjunct)": "Academic, part-time (US)",
    "International: Other Academic (Part-time or Adjunct)": "Academic, part-time (International)",
    "Full-Time Nonacademic": "Nonacademic, full-time",
    "Other Nonacademic (Temporary, Part-Time, Non-Salaried, Consulting, Etc.)": "Nonacademic, other",
}

def clean(s): return html.unescape(html.unescape((s or "").strip())).replace("​", "").strip()
def tc(s): return s.title() if s.isupper() or s.islower() else s

def location(p):
    locs, countries, pins = [], [], []
    for l in p.findall(".//location"):
        city, state, country = (tc(clean(l.findtext(k))) for k in ("city", "state", "country"))
        us = country.upper() in ("UNITED STATES", "USA", "US", "")
        countries.append("United States" if us else country)
        label = ", ".join(x for x in ((city, US_STATES.get(state, state)) if us else (city, country)) if x)
        locs.append(label)
        c = COORDS.get(place_key(l))
        if c: pins.append([round(c[0], 3), round(c[1], 3), c[2] if len(c) > 2 else label])
    locs = list(dict.fromkeys(x for x in locs if x))
    text = "; ".join(locs[:3]) + (f" (+{len(locs) - 3} more)" if len(locs) > 3 else "")
    pins = [list(x) for x in dict.fromkeys(tuple(x) for x in pins)]
    return text, sorted(set(c for c in countries if c)), pins

root = ET.parse(JOE).getroot()
COORDS = geocode(root.iter("location"))
year = root.find("year").get("joe_year_ID")
issue = int(root.find(".//issue").get("joe_issue_ID"))
exported = datetime.date.fromtimestamp(os.path.getmtime(JOE))
jobs = []
for p in root.iter("position"):
    sec = clean(p.findtext("jp_section"))
    dl = clean(p.findtext("jp_application_deadline"))[:10]
    loc, countries, pins = location(p)
    codes = sorted({clean(j.findtext("jc_code"))[:1] for j in p.iter("jel_class")} & set(JEL))
    fields = list(dict.fromkeys(clean(j.findtext("jc_description")) for j in p.iter("jel_class")
                                if not clean(j.findtext("jc_code")).startswith("00")))
    dept = " · ".join(x for x in (clean(p.findtext("jp_department")), clean(p.findtext("jp_division"))) if x)
    jobs.append({
        "inst": clean(p.findtext("jp_institution")), "dept": dept, "title": clean(p.findtext("jp_title")),
        "cat": CATEGORY.get(sec, sec), "kw": clean(p.findtext("jp_keywords")), "loc": loc, "countries": countries, "pins": pins,
        "us": "United States" in countries, "jel": codes,
        "fields": ", ".join(fields) if fields else "Any field",
        "deadline": dl, "status": clean(p.findtext("jp_status")),
        "url": f"https://www.aeaweb.org/joe/listing.php?JOE_ID={year}-{issue:02d}_{p.get('jp_id')}",
    })
jobs.sort(key=lambda j: (j["deadline"] or "9999", j["inst"].lower()))


template = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
page = (template
        .replace("__JOBS__", json.dumps(jobs, ensure_ascii=False).replace("</", "<\\/"))
        .replace("__JEL__", json.dumps(JEL))
        .replace("__CATS__", json.dumps(list(dict.fromkeys(CATEGORY.values()))))
        .replace("__ASOF__", exported.strftime("%B %-d, %Y"))
        .replace("__ISSUE__", f"{year}-{issue:02d}"))
open(args.out, "w", encoding="utf-8").write(page)
print(f"{len(jobs)} postings written to {args.out}; updated through {exported}")
