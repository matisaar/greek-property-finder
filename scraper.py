"""
Greek Property Finder - Web Scraper
Scrapes Rightmove Overseas + Spitogatos for budget Greek investment properties.
Computes beach & airport distances from coordinates.
Budget: 150,000 CAD ≈ €102,000 EUR.
"""

import requests
from curl_cffi import requests as cffi_req
from bs4 import BeautifulSoup
import json
import re
import time
import os
import math
from datetime import datetime
from urllib.parse import urljoin

# ── Greek airports with coordinates ────────────────────────────────
AIRPORTS = {
    "ATH": {"name": "Athens Intl (ATH)", "lat": 37.9364, "lng": 23.9445, "year_round": True},
    "SKG": {"name": "Thessaloniki (SKG)", "lat": 40.5197, "lng": 22.9709, "year_round": True},
    "HER": {"name": "Heraklion (HER)", "lat": 35.3397, "lng": 25.1803, "year_round": True},
    "CHQ": {"name": "Chania (CHQ)", "lat": 35.5317, "lng": 24.1497, "year_round": True},
    "CFU": {"name": "Corfu (CFU)", "lat": 39.6019, "lng": 19.9117, "year_round": False},
    "RHO": {"name": "Rhodes (RHO)", "lat": 36.4054, "lng": 28.0862, "year_round": True},
    "KGS": {"name": "Kos (KGS)", "lat": 36.7934, "lng": 26.9402, "year_round": False},
    "JMK": {"name": "Mykonos (JMK)", "lat": 37.4351, "lng": 25.3481, "year_round": False},
    "JTR": {"name": "Santorini (JTR)", "lat": 36.3992, "lng": 25.4793, "year_round": False},
    "ZTH": {"name": "Zakynthos (ZTH)", "lat": 37.7509, "lng": 20.8843, "year_round": False},
    "EFL": {"name": "Cephalonia (EFL)", "lat": 38.1200, "lng": 20.5004, "year_round": False},
    "PVK": {"name": "Preveza/Lefkada (PVK)", "lat": 38.9268, "lng": 20.7653, "year_round": False},
    "VOL": {"name": "Volos (VOL)", "lat": 39.2196, "lng": 22.7943, "year_round": False},
    "KVA": {"name": "Kavala (KVA)", "lat": 40.9133, "lng": 24.6192, "year_round": False},
    "JKH": {"name": "Chios (JKH)", "lat": 38.3432, "lng": 26.1406, "year_round": False},
    "SMI": {"name": "Samos (SMI)", "lat": 37.6900, "lng": 26.9117, "year_round": False},
    "KLX": {"name": "Kalamata (KLX)", "lat": 37.0683, "lng": 22.0253, "year_round": False},
    "JSI": {"name": "Skiathos (JSI)", "lat": 39.1771, "lng": 23.5037, "year_round": False},
    "IOA": {"name": "Ioannina (IOA)", "lat": 39.6964, "lng": 20.8225, "year_round": False},
    "GPA": {"name": "Patras/Araxos (GPA)", "lat": 38.1511, "lng": 21.4256, "year_round": False},
    "KIT": {"name": "Kythira (KIT)", "lat": 36.2743, "lng": 23.0170, "year_round": False},
    "JSH": {"name": "Sitia (JSH)", "lat": 35.2160, "lng": 26.1013, "year_round": False},
    "AOK": {"name": "Karpathos (AOK)", "lat": 35.4214, "lng": 27.1460, "year_round": False},
    "LXS": {"name": "Lemnos (LXS)", "lat": 39.9170, "lng": 25.2363, "year_round": False},
    "MLO": {"name": "Milos (MLO)", "lat": 36.6969, "lng": 24.4769, "year_round": False},
    "JNX": {"name": "Naxos (JNX)", "lat": 37.0811, "lng": 25.3681, "year_round": False},
    "PAS": {"name": "Paros (PAS)", "lat": 37.0204, "lng": 25.1278, "year_round": False},
    "SKU": {"name": "Skyros (SKU)", "lat": 38.9676, "lng": 24.4872, "year_round": False},
}

# ── Coastal reference points (for beach distance estimates) ─────────
# Sample of Greek coastal/beach points spread around the country
BEACH_POINTS = [
    # Ionian coast
    (39.62, 19.92), (39.78, 19.83), (39.67, 19.73), (38.17, 20.49),
    (37.79, 20.90), (38.83, 20.71), (38.72, 20.64),
    # Western Peloponnese
    (37.04, 21.73), (37.72, 21.43), (36.50, 22.97),
    # Attica / Saronic
    (37.82, 23.72), (37.73, 23.77), (37.84, 24.04),
    # Thessaloniki & Halkidiki
    (40.55, 22.94), (40.27, 23.32), (40.14, 23.75), (39.98, 23.88),
    # Eastern coasts
    (40.94, 24.41), (40.85, 24.70), (39.16, 23.87),
    # Pelion
    (39.37, 23.04), (39.17, 23.12),
    # Crete north coast
    (35.51, 24.02), (35.34, 25.13), (35.42, 24.47), (35.19, 25.72),
    # Crete south coast
    (34.93, 24.11), (35.00, 24.47), (35.05, 25.74),
    # Dodecanese
    (36.44, 28.22), (36.89, 27.18), (36.67, 27.07),
    # Cyclades
    (37.42, 25.33), (36.40, 25.46), (37.09, 25.38), (36.70, 24.44),
    # NE Aegean
    (38.37, 26.14), (37.75, 26.98), (39.10, 26.55),
    # Sporades
    (39.16, 23.87), (39.20, 23.72),
    # Evvia
    (38.47, 23.60), (38.90, 23.17),
    # Kavala coast
    (40.93, 24.40), (40.78, 24.35),
    # Pieria
    (40.26, 22.59),
]

# ── Greek cities/towns (for "near civilization" distance) ───────────
CITIES = [
    # Major cities
    {"name": "Athens", "lat": 37.9838, "lng": 23.7275, "pop": 3700000},
    {"name": "Thessaloniki", "lat": 40.6401, "lng": 22.9444, "pop": 1100000},
    {"name": "Patras", "lat": 38.2466, "lng": 21.7346, "pop": 215000},
    {"name": "Heraklion", "lat": 35.3387, "lng": 25.1442, "pop": 175000},
    {"name": "Larissa", "lat": 39.6390, "lng": 22.4191, "pop": 170000},
    {"name": "Volos", "lat": 39.3615, "lng": 22.9422, "pop": 145000},
    {"name": "Ioannina", "lat": 39.6650, "lng": 20.8537, "pop": 115000},
    {"name": "Chania", "lat": 35.5138, "lng": 24.0180, "pop": 110000},
    # Medium cities
    {"name": "Kavala", "lat": 40.9399, "lng": 24.4014, "pop": 70000},
    {"name": "Serres", "lat": 41.0859, "lng": 23.5484, "pop": 76000},
    {"name": "Drama", "lat": 41.1500, "lng": 24.1467, "pop": 60000},
    {"name": "Kalamata", "lat": 37.0390, "lng": 22.1143, "pop": 70000},
    {"name": "Corfu Town", "lat": 39.6243, "lng": 19.9217, "pop": 40000},
    {"name": "Rhodes Town", "lat": 36.4354, "lng": 28.2176, "pop": 50000},
    {"name": "Argostoli", "lat": 38.1810, "lng": 20.4897, "pop": 14000},
    {"name": "Rethymno", "lat": 35.3693, "lng": 24.4738, "pop": 40000},
    {"name": "Zakynthos Town", "lat": 37.7873, "lng": 20.8987, "pop": 15000},
    {"name": "Chalkida", "lat": 38.4637, "lng": 23.5980, "pop": 100000},
    {"name": "Alexandroupoli", "lat": 40.8476, "lng": 25.8737, "pop": 72000},
    {"name": "Kos Town", "lat": 36.8940, "lng": 27.0921, "pop": 19000},
    {"name": "Mytilene", "lat": 39.1075, "lng": 26.5536, "pop": 37000},
    {"name": "Nafplio", "lat": 37.5678, "lng": 22.8019, "pop": 33000},
    {"name": "Trikala", "lat": 39.5555, "lng": 21.7686, "pop": 81000},
    {"name": "Veria", "lat": 40.5235, "lng": 22.2031, "pop": 67000},
    {"name": "Komotini", "lat": 41.1223, "lng": 25.4034, "pop": 67000},
    {"name": "Preveza", "lat": 38.9509, "lng": 20.7531, "pop": 32000},
]

# ── Distance helpers ────────────────────────────────────────────────

def _haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_airport(lat, lng):
    """Return (code, name, drive_min_estimate, year_round)."""
    best = None
    best_km = 9999
    for code, info in AIRPORTS.items():
        km = _haversine_km(lat, lng, info["lat"], info["lng"])
        if km < best_km:
            best_km = km
            best = (code, info)
    # Rough estimate: 1.4x straight-line for roads, 50 km/h average
    drive_min = int(best_km * 1.4 / 50 * 60) if best else 999
    code, info = best
    return code, info["name"], drive_min, info["year_round"]


def nearest_beach_min(lat, lng):
    """Estimate driving minutes to nearest beach."""
    min_km = min(_haversine_km(lat, lng, blat, blng) for blat, blng in BEACH_POINTS)
    # If within 2 km, basically on the beach
    if min_km < 2:
        return 5
    # Road factor + average speed
    drive_min = int(min_km * 1.3 / 40 * 60)
    return max(5, min(drive_min, 120))


def nearest_city(lat, lng):
    """Return (city_name, pop, drive_min)."""
    best = None
    best_km = 9999
    for c in CITIES:
        km = _haversine_km(lat, lng, c["lat"], c["lng"])
        if km < best_km:
            best_km = km
            best = c
    drive_min = int(best_km * 1.3 / 50 * 60) if best else 999
    return best["name"], best["pop"], max(5, drive_min)


def classify_region(lat, lng, display_address):
    """Auto-classify into a region based on coordinates & address text."""
    addr = display_address.lower()
    lat_f, lng_f = float(lat), float(lng)

    # Island / region detection from address
    if "corfu" in addr or "kerkyra" in addr:
        return "ionian_islands"
    if "cephalonia" in addr or "kefalonia" in addr:
        return "ionian_islands"
    if "zakynthos" in addr or "zante" in addr:
        return "ionian_islands"
    if "lefkada" in addr or "lefkas" in addr:
        return "ionian_islands"
    if "crete" in addr or "chania" in addr or "heraklion" in addr or "rethymno" in addr:
        return "crete"
    if "rhodes" in addr or "rodos" in addr:
        return "dodecanese"
    if "kos" in addr:
        return "dodecanese"
    if "mykonos" in addr or "santorini" in addr or "cyclades" in addr:
        return "cyclades"
    if "thessaloniki" in addr or "halkidiki" in addr or "chalkidiki" in addr:
        return "central_macedonia"
    if "serres" in addr or "drama" in addr:
        return "northern_greece"
    if "kavala" in addr or "thassos" in addr or "thrace" in addr:
        return "northern_greece"
    if "pelion" in addr or "magnesia" in addr or "volos" in addr:
        return "pelion_sporades"
    if "skiathos" in addr or "skopelos" in addr or "alonnisos" in addr:
        return "pelion_sporades"
    if "attica" in addr or "athens" in addr or "piraeus" in addr:
        return "attica"
    if "peloponnese" in addr or "kalamata" in addr or "nafplio" in addr:
        return "peloponnese"
    if "epirus" in addr or "ioannina" in addr or "preveza" in addr:
        return "epirus"

    # Coordinate-based fallback
    if lat_f > 40.2 and lng_f < 21.5:
        return "epirus"
    if lat_f > 40.2 and lng_f >= 21.5:
        return "northern_greece"
    if lat_f < 36.0:
        return "crete"
    if 38.5 < lat_f < 40.2 and lng_f < 21.0:
        return "ionian_islands"
    if lat_f < 38.5 and lng_f > 27.0:
        return "dodecanese"
    if 36.0 < lat_f < 38.0 and 24.5 < lng_f < 27.0:
        return "cyclades"
    if 37.5 < lat_f < 38.5 and 22.5 < lng_f < 24.5:
        return "attica"

    return "other"


# ── GBP to EUR conversion ──────────────────────────────────────────
GBP_TO_EUR = 1.18  # approximate Feb 2026
CAD_TO_EUR = 0.68  # approximate Feb 2026
MAX_EUR = 102000
MAX_GBP = int(MAX_EUR / GBP_TO_EUR)  # ~86,440


# ── Rightmove Overseas Scraper ──────────────────────────────────────

def scrape_rightmove_overseas(max_pages=10):
    """
    Live scrape Rightmove Overseas Greece — all regions.
    Returns list of property dicts with standardised fields.
    """
    properties = []
    seen_ids = set()

    for page_idx in range(max_pages):
        offset = page_idx * 24
        url = (
            f"https://www.rightmove.co.uk/overseas-property-for-sale/Greece.html"
            f"?maxPrice={MAX_GBP}&sortType=1&index={offset}"
        )
        print(f"    Page {page_idx + 1}: index={offset}...")
        try:
            r = cffi_req.get(url, impersonate="chrome", timeout=20)
            if r.status_code != 200:
                print(f"      HTTP {r.status_code}, skipping")
                continue

            soup = BeautifulSoup(r.text, "lxml")
            script = soup.find("script", id="__NEXT_DATA__")
            if not script or not script.string:
                print("      No __NEXT_DATA__ found")
                continue

            data = json.loads(script.string)
            page_props = data.get("props", {}).get("pageProps", {})

            # Find properties in the nested structure
            raw_props = None
            for path_fn in [
                lambda: page_props["properties"],
                lambda: page_props["searchResults"]["properties"],
            ]:
                try:
                    raw_props = path_fn()
                    break
                except (KeyError, TypeError):
                    continue

            if not raw_props:
                # Recursive find
                def _find(d, key, depth=0):
                    if depth > 6 or not isinstance(d, dict):
                        return None
                    if key in d and isinstance(d[key], list) and d[key]:
                        return d[key]
                    for v in d.values():
                        r2 = _find(v, key, depth + 1)
                        if r2:
                            return r2
                    return None
                raw_props = _find(data, "properties") or []

            page_count = 0
            for rp in raw_props:
                pid = rp.get("id")
                if not pid or pid in seen_ids:
                    continue
                seen_ids.add(pid)

                # Extract price in EUR
                price_data = rp.get("price", {})
                if isinstance(price_data, dict):
                    disp = price_data.get("displayPrices", [{}])
                    gbp_price = None
                    eur_price = None
                    for dp in disp:
                        dstr = dp.get("displayPrice", "")
                        if "€" in dstr:
                            m = re.search(r'[\d,]+', dstr.replace(",", ""))
                            if m:
                                eur_price = int(m.group())
                        elif "£" in dstr:
                            m = re.search(r'[\d,]+', dstr.replace(",", ""))
                            if m:
                                gbp_price = int(m.group())
                    if not eur_price and gbp_price:
                        eur_price = int(gbp_price * GBP_TO_EUR)
                    elif not eur_price:
                        amt = price_data.get("amount")
                        if amt:
                            eur_price = int(float(amt) * GBP_TO_EUR)
                else:
                    eur_price = int(float(price_data) * GBP_TO_EUR) if price_data else None

                if not eur_price or eur_price > MAX_EUR:
                    continue

                # Location
                loc = rp.get("location", {})
                lat = loc.get("latitude")
                lng = loc.get("longitude")
                display_addr = rp.get("displayAddress", "")

                # Images
                images = rp.get("images", [])
                image_url = images[0].get("srcUrl", "") if images else ""

                # Property sub-type
                ptype = rp.get("propertySubType", rp.get("propertyType", "Property"))
                bedrooms = rp.get("bedrooms")
                bathrooms = rp.get("bathrooms")

                # Summary / title
                summary = rp.get("summary", "")
                beds_str = f"{bedrooms}-Bed " if bedrooms else ""
                title = f"{beds_str}{ptype} - {display_addr}" if display_addr else summary[:80]

                # Area in sqm (try to extract from summary)
                area = None
                area_match = re.search(r'(\d+)\s*(?:sq\.?\s*m|m²|sqm)', summary, re.I)
                if area_match:
                    area = int(area_match.group(1))

                # Skip plots / land only
                if ptype and ptype.lower() in ("plot", "land", "plot of land"):
                    continue

                # Build listing URL
                listing_url = f"https://www.rightmove.co.uk/properties/{pid}#/?channel=OVERSEAS"

                # Compute distances if we have coords
                airport_code, airport_name, airport_min, airport_yr = "", "", 60, False
                beach_min_val = 30
                city_name, city_pop, city_min = "", 0, 60
                region = "other"

                if lat and lng:
                    airport_code, airport_name, airport_min, airport_yr = nearest_airport(lat, lng)
                    beach_min_val = nearest_beach_min(lat, lng)
                    city_name, city_pop, city_min = nearest_city(lat, lng)
                    region = classify_region(lat, lng, display_addr)

                # Estimate Airbnb numbers based on region type
                # Islands/coastal: higher rate, higher occupancy in summer
                # City: more consistent but moderate
                airbnb_rate, airbnb_occ = _estimate_airbnb(eur_price, region, bedrooms, beach_min_val, city_min)

                prop = {
                    "title": title[:120],
                    "price": eur_price,
                    "area_sqm": area,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "url": listing_url,
                    "image_url": image_url,
                    "source": "Rightmove",
                    "region": region,
                    "display_address": display_addr,
                    "features": _extract_features(summary, ptype, bedrooms, display_addr),
                    "roi": "",
                    "property_type": ptype or "Property",
                    "airport_drive_min": airport_min,
                    "airport_code": airport_code,
                    "airport_name": airport_name,
                    "beach_min": beach_min_val,
                    "nearest_city": city_name,
                    "nearest_city_pop": city_pop,
                    "nearest_city_min": city_min,
                    "needs_renovation": _guess_renovation(summary, ptype),
                    "airbnb_night_rate": airbnb_rate,
                    "airbnb_occupancy_pct": airbnb_occ,
                    "lat": lat,
                    "lng": lng,
                    "rightmove_id": pid,
                }
                properties.append(prop)
                page_count += 1

            print(f"      → {page_count} residential properties (total {len(properties)})")
            time.sleep(1.5)

        except Exception as e:
            print(f"      Error: {e}")

    return properties


def _extract_features(summary, ptype, bedrooms, addr):
    """Extract feature tags from listing data."""
    features = []
    s = (summary + " " + addr).lower()
    if bedrooms:
        features.append(f"{bedrooms} bedroom{'s' if bedrooms > 1 else ''}")
    if ptype:
        features.append(ptype)
    for kw, label in [
        ("renovated", "Renovated"), ("refurbished", "Refurbished"),
        ("sea view", "Sea View"), ("mountain view", "Mountain View"),
        ("garden", "Garden"), ("terrace", "Terrace"), ("balcony", "Balcony"),
        ("pool", "Pool"), ("parking", "Parking"), ("furnished", "Furnished"),
        ("stone", "Stone Building"), ("traditional", "Traditional"),
        ("near beach", "Near Beach"), ("central", "Central Location"),
    ]:
        if kw in s:
            features.append(label)
    return features[:6]


def _guess_renovation(summary, ptype):
    """Guess if property needs renovation from description."""
    s = summary.lower()
    reno_words = ["renovation", "renovate", "needs work", "restore", "ruin",
                  "shell", "unfinished", "project", "to be completed"]
    no_reno = ["renovated", "newly", "refurbished", "ready to move", "habitable"]
    for w in no_reno:
        if w in s:
            return False
    for w in reno_words:
        if w in s:
            return True
    # Budget properties often need work
    return False


def _estimate_airbnb(price_eur, region, bedrooms, beach_min, city_min):
    """Estimate nightly Airbnb rate and occupancy based on property attributes."""
    beds = bedrooms or 1

    # Base rate by region type
    if region in ("cyclades", "dodecanese"):
        base_rate = 55 + beds * 20
        base_occ = 50
    elif region in ("crete", "ionian_islands"):
        base_rate = 45 + beds * 18
        base_occ = 48
    elif region in ("attica",):
        base_rate = 40 + beds * 15
        base_occ = 60  # year-round city
    elif region in ("pelion_sporades",):
        base_rate = 40 + beds * 15
        base_occ = 42
    elif region in ("central_macedonia",):
        base_rate = 35 + beds * 12
        base_occ = 45
    else:
        base_rate = 30 + beds * 12
        base_occ = 35

    # Beach proximity bonus
    if beach_min <= 10:
        base_rate += 10
        base_occ += 5
    elif beach_min <= 20:
        base_rate += 5

    # City proximity bonus for year-round demand
    if city_min <= 15:
        base_occ += 8

    return int(base_rate), min(70, int(base_occ))


# ── Wikimedia Commons area-photo fetcher ──────────────────────────────

_PHOTO_BLACKLIST = re.compile(
    r'(logo|icon|map\b|flag|coat.of.arms|diagram|chart|stamp|sign\b|badge|seal|'
    r'woman.holding|fashion|coffee.cup|faux.fur|portrait|people.icon|'
    r'placeholder|symbol|\.svg|empty.highway|ISS\d|View.of.Earth|'
    r'Abandoned.Quarry|Ottoman.Archit|Singer|Showcase|elevation.model|'
    r'census|population|admin|district.map|municipalities)',
    re.IGNORECASE,
)

def _extract_location_hint(title: str) -> str:
    if " - " in title:
        title = title.split(" - ", 1)[1]
    title = re.sub(r'\([^)]*\)', '', title)
    title = re.sub(r'\b(city|centre|center|area|island|university)\b', '', title, flags=re.I)
    return title.strip().strip(",").strip()


def _score_photo(fname: str, hint: str) -> int:
    score = 0
    fname_lower = fname.lower()
    for word in hint.lower().replace(",", " ").split():
        if len(word) > 2 and word in fname_lower:
            score += 10
    for kw in ("panoramio", "view", "beach", "coast", "village", "town",
               "harbour", "harbor", "church", "bay", "landscape", "street"):
        if kw in fname_lower:
            score += 3
    if "unsplash" in fname_lower:
        score -= 2
    return score


def fetch_area_photos(lat, lng, title, n=3):
    hint = _extract_location_hint(title)
    candidates = []

    for query in [f"{hint} Greece", f"{hint} landscape beach"]:
        try:
            resp = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query", "generator": "search",
                    "gsrsearch": query, "gsrnamespace": "6", "gsrlimit": "20",
                    "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": "600",
                    "format": "json",
                },
                headers={"User-Agent": "GreekPropertyFinder/1.0"},
                timeout=12,
            )
            pages = resp.json().get("query", {}).get("pages", {})
            for p in pages.values():
                fname = p.get("title", "")
                ii = (p.get("imageinfo") or [{}])[0]
                mime = ii.get("mime", "")
                thumb = ii.get("thumburl", "")
                if not thumb or "image/" not in mime:
                    continue
                if _PHOTO_BLACKLIST.search(fname):
                    continue
                candidates.append((_score_photo(fname, hint), thumb))
        except Exception:
            pass

    if lat and lng:
        try:
            resp = requests.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query", "generator": "geosearch",
                    "ggscoord": f"{lat}|{lng}", "ggsradius": "10000",
                    "ggsnamespace": "6", "ggslimit": "20",
                    "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": "600",
                    "format": "json",
                },
                headers={"User-Agent": "GreekPropertyFinder/1.0"},
                timeout=12,
            )
            pages = resp.json().get("query", {}).get("pages", {})
            for p in pages.values():
                fname = p.get("title", "")
                ii = (p.get("imageinfo") or [{}])[0]
                mime = ii.get("mime", "")
                thumb = ii.get("thumburl", "")
                if not thumb or "image/" not in mime:
                    continue
                if _PHOTO_BLACKLIST.search(fname):
                    continue
                candidates.append((_score_photo(fname, hint), thumb))
        except Exception:
            pass

    candidates.sort(key=lambda x: x[0], reverse=True)
    seen = set()
    results = []
    for _score, thumb in candidates:
        if thumb not in seen:
            seen.add(thumb)
            results.append(thumb)
        if len(results) >= n:
            break
    return results


# ── Dynamic region info builder ─────────────────────────────────────

def build_region_info(properties):
    """Build region metadata from the actual scraped properties."""
    region_data = {}
    for p in properties:
        r = p.get("region", "other")
        if r not in region_data:
            region_data[r] = {
                "properties": [],
                "airport_codes": set(),
                "cities": set(),
            }
        region_data[r]["properties"].append(p)
        if p.get("airport_code"):
            region_data[r]["airport_codes"].add(p["airport_code"])
        if p.get("nearest_city"):
            region_data[r]["cities"].add(p["nearest_city"])

    regions = {}
    region_names = {
        "ionian_islands": "Ionian Islands",
        "crete": "Crete",
        "northern_greece": "Northern Greece",
        "pelion_sporades": "Pelion & Sporades",
        "attica": "Athens / Attica",
        "central_macedonia": "Central Macedonia",
        "dodecanese": "Dodecanese Islands",
        "cyclades": "Cyclades Islands",
        "peloponnese": "Peloponnese",
        "epirus": "Epirus",
        "other": "Other Regions",
    }

    for r, info in region_data.items():
        props = info["properties"]
        codes = sorted(info["airport_codes"])
        cities = sorted(info["cities"])
        avg_price = int(sum(p["price"] for p in props) / len(props)) if props else 0
        avg_airport = int(sum(p.get("airport_drive_min", 60) for p in props) / len(props))
        avg_beach = int(sum(p.get("beach_min", 30) for p in props) / len(props))

        # Estimate rental yield
        yields = []
        for p in props:
            rate = p.get("airbnb_night_rate", 50)
            occ = p.get("airbnb_occupancy_pct", 40) / 100
            annual = rate * 365 * occ
            if p["price"] > 0:
                yields.append(annual / p["price"] * 100)
        avg_yield = sum(yields) / len(yields) if yields else 4.5

        regions[r] = {
            "name": region_names.get(r, r.replace("_", " ").title()),
            "city_pop": ", ".join(cities[:3]),
            "airport": " / ".join(codes) if codes else "Nearest varies",
            "airport_code": " / ".join(codes),
            "airport_drive_min": avg_airport,
            "airport_note": f"Average {avg_airport} min drive to nearest airport",
            "airport_international": True,
            "airport_seasonal": r not in ("attica", "northern_greece"),
            "beach_distance": f"Average {avg_beach} min to nearest beach",
            "beach_distance_min": avg_beach,
            "description": f"{len(props)} properties found in {region_names.get(r, r)}.",
            "avg_price_sqm": int(avg_price / 60),  # rough estimate
            "rental_yield": f"{avg_yield:.0f}-{avg_yield+1:.0f}%",
            "rental_yield_mid": round(avg_yield, 1),
            "why_invest": f"{len(props)} budget properties available.",
        }

    return regions


# ── Main scraper ────────────────────────────────────────────────────

def run_scraper():
    """Main scraper function."""
    print("=" * 60)
    print("Greek Property Finder - Web Scraper")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    all_properties = []

    # 1. Live scrape Rightmove Overseas Greece
    print("\n[1/2] Live scraping Rightmove Overseas Greece...")
    try:
        rightmove = scrape_rightmove_overseas(max_pages=12)
        all_properties.extend(rightmove)
        print(f"  → Got {len(rightmove)} properties from Rightmove")
    except Exception as e:
        print(f"  → Rightmove scrape failed: {e}")

    # 2. Note: Spitogatos, xe.gr, tospitimou block automated access.
    #    Properties from Greek agents appear on Rightmove Overseas.
    print("\n  Note: Spitogatos/xe.gr/tospitimou block automated scraping.")
    print("  Rightmove aggregates from Greek agencies — this covers the market.")

    # Deduplicate by rightmove_id or title
    seen = set()
    unique = []
    for p in all_properties:
        key = p.get("rightmove_id") or p.get("title", "")
        if key not in seen:
            seen.add(key)
            unique.append(p)
    all_properties = unique

    # Filter: budget + actual buildings (not plots)
    investment_properties = [
        p for p in all_properties
        if p.get("price") and p["price"] <= MAX_EUR
        and p.get("lat") and p.get("lng")
    ]

    # Sort by price
    investment_properties.sort(key=lambda p: p["price"])

    print(f"\nTotal scraped: {len(all_properties)}")
    print(f"Budget residential with coords: {len(investment_properties)}")

    # Build dynamic region info
    regions = build_region_info(investment_properties)
    print(f"Regions found: {', '.join(regions.keys())}")

    # 2. Fetch area photos
    print(f"\n[2/2] Fetching area photos from Wikimedia Commons...")
    for i, p in enumerate(investment_properties):
        lat = p.get("lat")
        lng = p.get("lng")
        title = p.get("title", "")
        if lat and lng:
            photos = fetch_area_photos(lat, lng, title)
            p["area_photos"] = photos
            status = f"{len(photos)} photos" if photos else "none"
            print(f"  [{i+1}/{len(investment_properties)}] {title[:50]:50s} → {status}")
            time.sleep(0.4)
        else:
            p["area_photos"] = []

    # Save
    output = {
        "scraped_date": datetime.now().isoformat(),
        "total_properties": len(investment_properties),
        "regions": regions,
        "properties": investment_properties,
        "sources": ["Rightmove Overseas (rightmove.co.uk)"],
        "source_note": "Rightmove aggregates listings from Greek real estate agencies. "
                       "Spitogatos.gr, xe.gr, and tospitimou.gr block automated scraping. "
                       "Many local agency listings also appear on Rightmove Overseas.",
        "market_context": {
            "avg_annual_appreciation": "7-9% (2024-2025)",
            "mortgage_rate": "3.5% (variable, as of Oct 2025)",
            "transfer_tax": "3.09% of property value",
            "notary_fees": "0.65-1% of property value",
            "legal_fees": "1-2% of property value",
            "total_buying_costs": "~8-10% on top of purchase price",
            "budget": "150,000 CAD ≈ €102,000 EUR (Feb 2026 rate)",
            "budget_note": "Searching all of Greece for properties near beaches and civilization.",
            "golden_visa_threshold": "€250,000 (higher in prime areas)",
            "eu_citizen_note": "As an Estonian passport holder, you are an EU citizen. "
                              "No restrictions on buying property in Greece.",
            "canadian_note": "Canadian citizenship provides banking flexibility. "
                            "With Estonian (EU) passport, full rights to live, work, "
                            "and own property anywhere in the EU.",
            "rental_income_tax": "15% on first €12,000/year, 35% on €12,001-€35,000",
            "property_tax_annual": "ENFIA tax: €2-13 per sqm depending on location",
        }
    }

    os.makedirs("data", exist_ok=True)
    with open("data/properties.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nData saved to data/properties.json")
    print(f"Properties by region:")
    for r, info in sorted(regions.items(), key=lambda x: -len(x[1].get("city_pop", ""))):
        count = len([p for p in investment_properties if p.get("region") == r])
        print(f"  {regions[r]['name']:30s} — {count} properties")

    return output


if __name__ == "__main__":
    run_scraper()
