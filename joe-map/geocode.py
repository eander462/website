"""Look up coordinates for every JOE location; results are cached in geo/places.json.
Places GeoNames can't match go in geo/overrides.json as {"City|State|COUNTRY": [lat, lon]}."""
import html, io, json, os, re, sys, unicodedata, zipfile, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "geo", "places.json")
OVERRIDES = os.path.join(HERE, "geo", "overrides.json")
CITIES = os.path.join(HERE, "geo", "cities15000.zip")  # GeoNames, https://download.geonames.org/export/dump/

ISO = {"ARGENTINA":"AR","AUSTRALIA":"AU","AUSTRIA":"AT","BELGIUM":"BE","BRAZIL":"BR","CANADA":"CA","CHILE":"CL","CHINA":"CN","COLOMBIA":"CO","CYPRUS":"CY","CZECH REPUBLIC":"CZ","DENMARK":"DK","EGYPT":"EG","FINLAND":"FI","FRANCE":"FR","GERMANY":"DE","GREECE":"GR","HONG KONG":"HK","INDIA":"IN","INDONESIA":"ID","IRELAND":"IE","ISRAEL":"IL","ITALY":"IT","JAPAN":"JP","KAZAKHSTAN":"KZ","KOREA, REPUBLIC OF":"KR","LEBANON":"LB","LUXEMBOURG":"LU","MACAO":"MO","MALAYSIA":"MY","MEXICO":"MX","NETHERLANDS":"NL","NEW ZEALAND":"NZ","NORWAY":"NO","PAKISTAN":"PK","PERU":"PE","POLAND":"PL","PORTUGAL":"PT","QATAR":"QA","SAUDI ARABIA":"SA","SINGAPORE":"SG","SOUTH AFRICA":"ZA","SPAIN":"ES","SWEDEN":"SE","SWITZERLAND":"CH","TAIWAN":"TW","THAILAND":"TH","TURKEY":"TR","UNITED ARAB EMIRATES":"AE","UNITED KINGDOM":"GB","UNITED STATES":"US","URUGUAY":"UY","VIETNAM":"VN"}
US_STATES = {"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}

def clean(s): return html.unescape(html.unescape((s or "").strip())).strip()
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\bst\.?\s", "saint ", s); s = re.sub(r"\bft\.?\s", "fort ", s)
    return re.sub(r"[^a-z]+", " ", s).strip()

def key(l): return "|".join(clean(l.findtext(k)) for k in ("city", "state", "country"))

def load_index():
    idx = {}
    with zipfile.ZipFile(CITIES) as z, io.TextIOWrapper(z.open("cities15000.txt"), encoding="utf-8") as f:
        for line in f:
            c = line.rstrip("\n").split("\t")
            rec = (float(c[4]), float(c[5]), c[8], c[10], int(c[14] or 0))
            for name in {c[1], c[2], *c[3].split(",")}:
                if name: idx.setdefault((norm(name), c[8]), []).append(rec)
    return idx

def lookup(idx, city, state, country):
    cc = ISO.get(country.upper())
    if not cc or not city: return None
    cands = idx.get((norm(city), cc), [])
    if cc == "US" and state:
        cands = [r for r in cands if r[3] == US_STATES.get(state, state)] or []
    return max(cands, key=lambda r: r[4])[:2] if cands else None

def geocode(locations):
    """locations: iterable of <location> elements. Returns {key: [lat, lon]} for every place found."""
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    overrides = json.load(open(OVERRIDES)) if os.path.exists(OVERRIDES) else {}
    todo = {key(l) for l in locations} - set(cache) - set(overrides)
    if todo:
        idx = load_index()
        for k in todo:
            hit = lookup(idx, *k.split("|"))
            if hit: cache[k] = list(hit)
        json.dump(cache, open(CACHE, "w"), indent=0, sort_keys=True)
    return {**cache, **overrides}

if __name__ == "__main__":
    # Usage: python3 geocode.py [path/to/joe_full_xml.xml]  -- lists any places that still need an override
    joe = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "joe_full_xml.xml")
    locs = list(ET.parse(joe).getroot().iter("location"))
    found = geocode(locs)
    missing = sorted({key(l) for l in locs} - set(found))
    print(f"{len({key(l) for l in locs}) - len(missing)} places matched, {len(missing)} missing")
    for m in missing: print("  ", m)
