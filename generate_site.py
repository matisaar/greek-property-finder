"""
Generate a beautiful static HTML site from scraped property data.
Beach-trip-planner style: weighted preference sliders, live scoring, Airbnb comparison.
Outputs to docs/ for GitHub Pages deployment.
"""

import json
import os
from datetime import datetime


def generate_site():
    """Generate the static HTML site."""
    with open("data/properties.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    properties = data["properties"]
    regions = data["regions"]
    market = data["market_context"]
    scraped_date = data["scraped_date"][:10]

    # Build JS data array from properties
    js_data_items = []
    for i, p in enumerate(properties):
        region_info = regions.get(p.get("region", ""), {})
        region_name = region_info.get("name", p.get("region", "").replace("_", " ").title())
        beds = p.get("bedrooms")
        beds_str = str(beds) if beds and beds > 0 else ("Studio" if beds == 0 else "N/A")
        area = p.get("area_sqm", 0) or 0
        price = p.get("price", 0) or 0
        psqm = price // area if area else 0
        cad = int(price * 1.48)
        features = p.get("features", [])
        sat_fallback = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export?bbox={p.get('lng',23)-0.015},{p.get('lat',38)-0.01},{p.get('lng',23)+0.015},{p.get('lat',38)+0.01}&bboxSR=4326&size=600,400&imageSR=4326&format=jpg&f=image"
        img = p.get("image_url", sat_fallback)

        airbnb_rate = p.get("airbnb_night_rate", 50)
        airbnb_occ = p.get("airbnb_occupancy_pct", 40)
        annual_income = int(airbnb_rate * 365 * airbnb_occ / 100)
        gross_yield = round(annual_income / price * 100, 1) if price else 0

        lat = p.get("lat", 0)
        lng = p.get("lng", 0)
        maps_url = f"https://www.google.com/maps?q={lat},{lng}&z=14" if lat else "#"
        area_photos = p.get("area_photos", [])

        js_data_items.append(
            f'{{id:{i},title:"{p.get("title","").replace(chr(34),chr(39))}",'
            f'price:{price},cad:{cad},area:{area},psqm:{psqm},'
            f'beds:"{beds_str}",bedsN:{beds if beds else 0},'
            f'roi:"{p.get("roi","")}",'
            f'ptype:"{p.get("property_type","")}",'
            f'region:"{p.get("region","")}",'
            f'regionName:"{region_name.replace(chr(34),chr(39))}",'
            f'airport:{p.get("airport_drive_min", 60)},'
            f'airportName:"{p.get("airport_name","").replace(chr(34),chr(39))}",'
            f'beach:{p.get("beach_min", 30)},'
            f'beachKm:{p.get("beach_km", 0)},'
            f'beachName:"{p.get("beach_name","Beach").replace(chr(34),chr(39))}",'
            f'beachUrl:"{p.get("beach_directions_url","")}",'
            f'reno:{1 if p.get("needs_renovation") else 0},'
            f'nearestCity:"{p.get("nearest_city","").replace(chr(34),chr(39))}",'
            f'nearestCityMin:{p.get("nearest_city_min", 60)},'
            f'airbnbRate:{airbnb_rate},'
            f'airbnbOcc:{airbnb_occ},'
            f'annualIncome:{annual_income},'
            f'grossYield:{gross_yield},'
            f'lat:{lat},lng:{lng},'
            f'mapsUrl:"{maps_url}",'
            f'img:"{img}",'
            f'url:"{p.get("url","#")}",'
            f'source:"{p.get("source","")}",'
            f'features:{json.dumps(features[:4])},'
            f'areaPhotos:{json.dumps(area_photos[:3])}'
            f'}}'
        )

    js_data = "const DATA = [\n  " + ",\n  ".join(js_data_items) + "\n];"

    # Build region data for JS
    js_regions = []
    for k, v in regions.items():
        js_regions.append(
            f'"{k}":{{name:"{v["name"].replace(chr(34),chr(39))}",'
            f'airportCode:"{v.get("airport_code","")}",airportMin:{v.get("airport_drive_min",60)},'
            f'airportNote:"{v.get("airport_note","").replace(chr(34),chr(39))}",'
            f'beachMin:{v.get("beach_distance_min",30)},'
            f'yieldMid:{v.get("rental_yield_mid",4.5)},'
            f'avgPsqm:{v.get("avg_price_sqm",1000)}}}'
        )
    js_region_data = "const REGIONS = {" + ",".join(js_regions) + "};"

    # Market context cards HTML
    market_cards = ""
    market_items = [
        ("Budget", "150,000 CAD / ~\u20ac102,000"),
        ("Appreciation", market['avg_annual_appreciation']),
        ("Transfer Tax", market['transfer_tax']),
        ("Total Buy Costs", market['total_buying_costs']),
        ("Rental Tax", "15% (first \u20ac12k)"),
        ("ENFIA Tax", "\u20ac2-13/m\u00b2/yr"),
    ]
    for label, value in market_items:
        market_cards += f'<div class="m-card"><div class="m-label">{label}</div><div class="m-value">{value}</div></div>\n'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Greek Property Finder — Investment Properties Ranked</title>
<meta name="description" content="Budget Greek investment properties ranked by your priorities. Weighted scoring for airport proximity, price, size, beach distance, rental yield.">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
:root {{
  --ocean: #0077b6; --ocean-dark: #023e8a;
  --sunset: #ff6b35; --coral: #e63946;
  --palm: #2d6a4f; --dark: #1a1a2e; --gray: #6b7280;
  --gold: #f59e0b; --bg: #faf8f5; --border: #e8e4df;
  --card: #ffffff; --muted: #7a7a7a; --accent: #c2956a;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: var(--dark); line-height: 1.6; -webkit-font-smoothing: antialiased; }}

/* ── Hamburger Nav ── */
.hamburger-btn {{
  position: fixed; top: 14px; right: 16px; z-index: 9999;
  background: rgba(0,0,0,0.25); backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.2); border-radius: 10px;
  width: 40px; height: 40px; cursor: pointer;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 5px;
  transition: background 0.2s;
}}
.hamburger-btn:hover {{ background: rgba(0,0,0,0.4); }}
.hamburger-btn span {{
  display: block; width: 20px; height: 2px; background: white; border-radius: 2px;
  transition: transform 0.3s, opacity 0.3s;
}}
.hamburger-btn.open span:nth-child(1) {{ transform: translateY(7px) rotate(45deg); }}
.hamburger-btn.open span:nth-child(2) {{ opacity: 0; }}
.hamburger-btn.open span:nth-child(3) {{ transform: translateY(-7px) rotate(-45deg); }}

.nav-drawer-overlay {{
  position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 9990;
  opacity: 0; pointer-events: none; transition: opacity 0.3s;
}}
.nav-drawer-overlay.open {{ opacity: 1; pointer-events: auto; }}

.nav-drawer {{
  position: fixed; top: 0; right: -300px; width: 280px; height: 100%;
  background: linear-gradient(180deg, #1e3a5f 0%, #0e4a6f 100%);
  z-index: 9995; padding: 70px 24px 32px; transition: right 0.3s ease;
  box-shadow: -4px 0 20px rgba(0,0,0,0.3);
}}
.nav-drawer.open {{ right: 0; }}
.nav-drawer h3 {{
  color: rgba(255,255,255,0.5); font-size: 0.7rem; text-transform: uppercase;
  letter-spacing: 1.5px; margin-bottom: 16px; font-weight: 600;
}}
.nav-drawer a {{
  display: flex; align-items: center; gap: 12px;
  color: white; text-decoration: none; padding: 14px 16px;
  border-radius: 12px; margin-bottom: 6px; font-size: 0.88rem;
  font-weight: 500; transition: background 0.2s;
}}
.nav-drawer a:hover {{ background: rgba(255,255,255,0.1); }}
.nav-drawer a.active {{ background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.2); }}
.nav-drawer .nav-icon {{ font-size: 1.2rem; width: 28px; text-align: center; }}
.nav-drawer .nav-label {{ line-height: 1.3; }}
.nav-drawer .nav-label small {{ display: block; font-size: 0.7rem; color: rgba(255,255,255,0.5); font-weight: 400; }}

/* ── Hero ── */
.page-hero {{
  background: linear-gradient(135deg, #1e3a5f 0%, #0e76a8 50%, #1a9bc7 100%);
  color: white; padding: 44px 24px 32px; text-align: center;
  position: relative; overflow: hidden;
}}
.page-hero::before {{
  content: ''; position: absolute; inset: 0;
  background: url('https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Santorini_HDR_sunset.jpg/1600px-Santorini_HDR_sunset.jpg') center/cover;
  opacity: 0.12;
}}
.page-hero > * {{ position: relative; z-index: 1; }}
.page-hero h1 {{ font-size: clamp(1.5rem, 4vw, 2.2rem); font-weight: 900; margin-bottom: 6px; letter-spacing: -0.5px; }}
.page-hero p {{ font-size: 0.88rem; opacity: 0.8; margin-bottom: 16px; max-width: 620px; margin-left: auto; margin-right: auto; }}
.hero-badges {{ display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }}
.hero-badge {{
  background: rgba(255,255,255,0.15); backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.2); padding: 5px 14px;
  border-radius: 20px; font-size: 0.78rem; font-weight: 500;
}}
.page-hero-nav {{ display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 16px; }}
.page-hero-nav a {{
  color: rgba(255,255,255,0.75); text-decoration: none; font-size: 0.78rem;
  padding: 6px 16px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.2);
  transition: all 0.2s;
}}
.page-hero-nav a:hover {{ background: rgba(255,255,255,0.12); color: white; }}

.container {{ max-width: 1100px; margin: 0 auto; padding: 0 20px; }}

/* ── EU Notice ── */
.eu-bar {{
  background: linear-gradient(90deg, #d1fae5, #e0f2fe);
  border-bottom: 1px solid #a7f3d0; padding: 14px 24px;
  text-align: center; font-size: 0.85rem; color: #065f46;
  line-height: 1.6; overflow: visible;
}}
.eu-bar strong {{ color: #047857; }}

/* ── Weight Sliders Panel ── */
.weights-panel {{ margin: 16px auto 0; max-width: 1100px; padding: 0 20px; position: relative; z-index: 20; }}
.weights-card {{
  background: var(--card); border-radius: 16px; padding: 20px 24px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.08); border: 1px solid var(--border);
}}
.weights-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }}
.weights-title {{ font-size: 0.85rem; font-weight: 700; color: var(--dark); }}
.weights-reset {{
  font-size: 0.72rem; color: var(--ocean); cursor: pointer; border: none;
  background: none; font-family: inherit; font-weight: 600; padding: 4px 8px;
  border-radius: 6px; transition: background 0.2s;
}}
.weights-reset:hover {{ background: #e0f2fe; }}
.sliders {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px 24px; }}
.slider-group {{ }}
.slider-label {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }}
.slider-name {{ font-size: 0.72rem; font-weight: 700; }}
.slider-name.s-price {{ color: var(--palm); }}
.slider-name.s-airport {{ color: var(--coral); }}
.slider-name.s-beach {{ color: var(--ocean); }}
.slider-name.s-size {{ color: #7c3aed; }}
.slider-name.s-yield {{ color: var(--gold); }}
.slider-name.s-reno {{ color: var(--accent); }}
.slider-val {{ font-size: 0.72rem; font-weight: 800; color: var(--dark); }}
input[type="range"] {{
  width: 100%; height: 6px; -webkit-appearance: none; appearance: none;
  border-radius: 3px; outline: none; cursor: pointer;
}}
input[type="range"]::-webkit-slider-thumb {{
  -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.2); cursor: pointer;
}}
#sPrice {{ background: linear-gradient(90deg, #dcfce7, var(--palm)); }}
#sPrice::-webkit-slider-thumb {{ background: var(--palm); }}
#sAirport {{ background: linear-gradient(90deg, #fee2e2, var(--coral)); }}
#sAirport::-webkit-slider-thumb {{ background: var(--coral); }}
#sBeach {{ background: linear-gradient(90deg, #dbeafe, var(--ocean)); }}
#sBeach::-webkit-slider-thumb {{ background: var(--ocean); }}
#sSize {{ background: linear-gradient(90deg, #ede9fe, #7c3aed); }}
#sSize::-webkit-slider-thumb {{ background: #7c3aed; }}
#sYield {{ background: linear-gradient(90deg, #fef3c7, var(--gold)); }}
#sYield::-webkit-slider-thumb {{ background: var(--gold); }}
#sReno {{ background: linear-gradient(90deg, #fde8d8, var(--accent)); }}
#sReno::-webkit-slider-thumb {{ background: var(--accent); }}

/* ── #1 Pick Hero Card ── */
.pick-hero {{ margin: 20px auto 0; max-width: 1100px; padding: 0 20px; }}
.pick-hero-card {{
  display: grid; grid-template-columns: 1fr 1fr; border-radius: 20px; overflow: hidden;
  background: var(--card); box-shadow: 0 16px 60px rgba(0,0,0,0.12);
  border: 1px solid var(--border); cursor: pointer; transition: all 0.3s;
}}
.pick-hero-card:hover {{ box-shadow: 0 20px 70px rgba(0,0,0,0.18); transform: translateY(-2px); }}
.pick-hero-img {{ width: 100%; height: 340px; object-fit: cover; display: block; }}
.pick-hero-body {{ padding: 32px 36px; display: flex; flex-direction: column; justify-content: center; }}
.pick-hero-badge {{
  display: inline-flex; align-items: center; gap: 6px;
  background: linear-gradient(135deg, #e87d3e, #d4363b);
  color: white; font-size: 0.72rem; font-weight: 800; padding: 5px 14px;
  border-radius: 20px; width: fit-content; margin-bottom: 14px; letter-spacing: 0.3px;
}}
.pick-hero-name {{ font-size: 1.4rem; font-weight: 800; margin-bottom: 4px; line-height: 1.3; }}
.pick-hero-area {{ font-size: 0.82rem; color: var(--muted); margin-bottom: 18px; }}
.pick-hero-stats {{ display: flex; gap: 20px; margin-bottom: 18px; flex-wrap: wrap; }}
.pick-hero-stat {{ text-align: center; }}
.pick-hero-stat .val {{ font-size: 1.2rem; font-weight: 800; }}
.pick-hero-stat .val.price-c {{ color: var(--palm); }}
.pick-hero-stat .val.airport-c {{ color: var(--coral); }}
.pick-hero-stat .val.beach-c {{ color: var(--ocean); }}
.pick-hero-stat .val.yield-c {{ color: var(--gold); }}
.pick-hero-stat .lbl {{ font-size: 0.6rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }}
.pick-hero-score {{
  display: flex; align-items: center; gap: 10px;
  background: linear-gradient(135deg, #fff8f0, #fff5eb);
  border: 1px solid #fed7aa; border-radius: 12px; padding: 12px 16px;
}}
.score-ring {{ width: 48px; height: 48px; position: relative; }}
.score-ring svg {{ width: 48px; height: 48px; transform: rotate(-90deg); }}
.score-ring .bg {{ fill: none; stroke: #f5e6d3; stroke-width: 4; }}
.score-ring .fg {{ fill: none; stroke-width: 4; stroke-linecap: round; transition: stroke-dashoffset 0.6s ease; }}
.score-ring .num {{
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-size: 0.82rem; font-weight: 900; color: var(--ocean-dark);
}}
.score-info {{ flex: 1; }}
.score-info .title {{ font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #92400e; }}
.score-info .desc {{ font-size: 0.72rem; color: var(--muted); line-height: 1.4; }}

/* ── Card ── */
.card {{
  background: var(--card); border-radius: 16px; overflow: hidden;
  border: 1px solid var(--border); transition: all 0.25s; cursor: pointer;
}}
.card:hover {{ box-shadow: 0 10px 35px rgba(0,0,0,0.1); transform: translateY(-3px); }}
.card-img-wrap {{ position: relative; overflow: hidden; }}
.card-img {{ width: 100%; height: 175px; object-fit: cover; display: block; transition: transform 0.4s; }}
.card:hover .card-img {{ transform: scale(1.04); }}
.card-overlay {{ position: absolute; inset: 0; background: linear-gradient(to top, rgba(0,0,0,0.35) 0%, transparent 50%); }}
.card-rank {{
  position: absolute; top: 10px; left: 10px;
  min-width: 26px; height: 26px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; padding: 0 8px;
  font-size: 0.68rem; font-weight: 800; color: white;
  backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
}}
.card-rank.high {{ background: rgba(212,54,59,0.85); }}
.card-rank.mid {{ background: rgba(230,167,86,0.85); }}
.card-rank.low {{ background: rgba(160,174,192,0.85); }}
.card-price-tag {{
  position: absolute; bottom: 10px; left: 10px;
  background: rgba(0,0,0,0.55); color: white; font-size: 0.82rem;
  padding: 4px 10px; border-radius: 8px; font-weight: 700;
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
}}
.card-airport-tag {{
  position: absolute; bottom: 10px; right: 10px;
  background: rgba(230,57,70,0.75); color: white; font-size: 0.68rem;
  padding: 3px 8px; border-radius: 6px; font-weight: 600;
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
}}
.card-body {{ padding: 14px 16px 16px; }}
.card-name {{ font-size: 0.88rem; font-weight: 700; margin-bottom: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.card-area {{ font-size: 0.72rem; color: var(--muted); margin-bottom: 10px; }}
.card-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 0.72rem; color: var(--muted); }}
.card-row .hl {{ font-weight: 700; color: var(--dark); }}
.card-score-bar {{ display: flex; align-items: center; gap: 6px; margin-top: 8px; }}
.bar-track {{ flex: 1; height: 5px; border-radius: 3px; background: #f0ece7; overflow: hidden; }}
.bar-fill {{ height: 100%; border-radius: 3px; transition: width 0.4s ease; }}
.bar-fill.high {{ background: linear-gradient(90deg, #e87d3e, #d4363b); }}
.bar-fill.mid {{ background: linear-gradient(90deg, #f0c27f, #e6a756); }}
.bar-fill.low {{ background: #b8c9d6; }}
.bar-num {{ font-size: 0.7rem; font-weight: 800; color: var(--ocean-dark); min-width: 20px; transition: all 0.3s; }}

/* ── Area photos row ── */
.card-photos {{ display: flex; gap: 3px; padding: 0 3px; margin-top: -2px; }}
.card-photos img {{ flex: 1; height: 50px; object-fit: cover; border-radius: 4px; opacity: 0.85; transition: opacity 0.2s; }}
.card:hover .card-photos img {{ opacity: 1; }}

/* ── Maps button on card ── */
.card-maps-btn {{
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 0.68rem; font-weight: 600; color: var(--ocean);
  margin-top: 6px; padding: 3px 8px; border-radius: 6px;
  background: #e0f2fe; text-decoration: none; transition: background 0.2s;
}}
.card-maps-btn:hover {{ background: #bae6fd; }}
.beach-link {{ color: var(--ocean); text-decoration: underline dotted; cursor: pointer; font-weight: 600; }}
.beach-link:hover {{ color: var(--ocean-dark); text-decoration: underline; }}

/* ── Modal area gallery ── */
.m-gallery {{ display: flex; gap: 4px; margin-bottom: 10px; }}
.m-gallery img {{ flex: 1; height: 80px; object-fit: cover; border-radius: 8px; cursor: pointer; transition: opacity 0.2s; }}
.m-gallery img:hover {{ opacity: 0.8; }}
.m-maps-row {{ display: flex; gap: 8px; margin-bottom: 10px; }}
.m-maps-btn {{
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 0.78rem; font-weight: 600; color: var(--ocean);
  padding: 8px 14px; border-radius: 10px; background: #e0f2fe;
  text-decoration: none; transition: all 0.2s; flex: 1; justify-content: center;
}}
.m-maps-btn:hover {{ background: #bae6fd; }}
.m-maps-btn.listing {{
  background: #fef3c7; color: #92400e;
}}
.m-maps-btn.listing:hover {{ background: #fde68a; }}

/* ── Explainer ── */
.explainer {{ max-width: 1100px; margin: 32px auto 0; padding: 0 20px; }}
.explainer-card {{
  background: var(--card); border: 1px solid var(--border); border-radius: 16px;
  padding: 24px 28px; display: flex; gap: 24px; align-items: flex-start; flex-wrap: wrap;
}}
.explainer-card h3 {{ font-size: 0.88rem; font-weight: 800; margin-bottom: 6px; }}
.explainer-card p {{ font-size: 0.78rem; color: var(--muted); line-height: 1.6; }}
.explainer-item {{ flex: 1; min-width: 200px; }}
.explainer-formula {{
  background: var(--bg); border-radius: 10px; padding: 12px 16px;
  font-size: 0.78rem; color: var(--dark); font-weight: 500; margin-top: 6px;
  border: 1px solid var(--border); font-family: 'Inter', monospace;
}}
.explainer-formula span {{ font-weight: 800; }}

/* ── Market cards ── */
.market-row {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; max-width: 1100px; margin: 20px auto; padding: 0 20px; }}
.m-card {{ background: var(--card); border-radius: 12px; padding: 14px 16px; border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
.m-label {{ font-size: 0.65rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
.m-value {{ font-size: 0.92rem; font-weight: 700; color: var(--dark); }}

/* ── Browse All Grid ── */
.browse-section {{ max-width: 1100px; margin: 40px auto 0; padding: 0 20px; }}
.browse-header {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; }}
.browse-title {{ font-size: 1.3rem; font-weight: 800; letter-spacing: -0.3px; }}
.browse-sub {{ font-size: 0.82rem; color: var(--muted); margin-top: 2px; }}
.browse-count {{ font-weight: 700; color: var(--ocean); }}
.filters {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
.filter-select, .filter-input {{
  font-family: 'Inter', sans-serif; font-size: 0.78rem; font-weight: 500;
  padding: 7px 12px; border: 1px solid var(--border); border-radius: 10px;
  background: var(--card); color: var(--dark); cursor: pointer; transition: border-color 0.2s;
}}
.filter-select:focus, .filter-input:focus {{ outline: none; border-color: var(--ocean); }}
.filter-input {{ width: 90px; }}
.filter-label {{ font-size: 0.72rem; color: var(--muted); font-weight: 600; }}
.filter-clear {{
  font-size: 0.72rem; color: var(--ocean); cursor: pointer; border: none;
  background: none; font-family: inherit; font-weight: 600; padding: 4px 8px;
  border-radius: 6px; transition: background 0.2s;
}}
.filter-clear:hover {{ background: #e0f2fe; }}
.browse-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
.browse-grid .card {{ flex: none; }}

/* ── Airbnb comparison ── */
.airbnb-section {{ max-width: 1100px; margin: 40px auto 0; padding: 0 20px; }}
.airbnb-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; margin-top: 16px; }}
.airbnb-card {{
  background: var(--card); border-radius: 16px; overflow: hidden;
  border: 1px solid var(--border); transition: all 0.25s; cursor: pointer;
}}
.airbnb-card:hover {{ box-shadow: 0 10px 35px rgba(0,0,0,0.1); transform: translateY(-2px); }}
.airbnb-card-body {{ padding: 16px; }}
.airbnb-card-name {{ font-size: 0.92rem; font-weight: 700; margin-bottom: 4px; }}
.airbnb-card-region {{ font-size: 0.72rem; color: var(--muted); margin-bottom: 10px; }}
.airbnb-row {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 10px; }}
.airbnb-stat {{ background: var(--bg); border-radius: 8px; padding: 8px; text-align: center; }}
.airbnb-stat .v {{ font-size: 0.95rem; font-weight: 800; }}
.airbnb-stat .v.green {{ color: var(--palm); }}
.airbnb-stat .v.gold {{ color: var(--gold); }}
.airbnb-stat .v.blue {{ color: var(--ocean); }}
.airbnb-stat .l {{ font-size: 0.6rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.3px; margin-top: 2px; }}
.airbnb-bar {{ display: flex; align-items: center; gap: 8px; }}
.airbnb-bar-label {{ font-size: 0.68rem; font-weight: 600; color: var(--muted); min-width: 80px; }}
.airbnb-bar-track {{ flex: 1; height: 8px; border-radius: 4px; background: #f0ece7; overflow: hidden; }}
.airbnb-bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.4s; }}
.airbnb-bar-fill.roi {{ background: linear-gradient(90deg, #dcfce7, var(--palm)); }}
.airbnb-bar-fill.occ {{ background: linear-gradient(90deg, #dbeafe, var(--ocean)); }}
.airbnb-bar-num {{ font-size: 0.72rem; font-weight: 800; min-width: 36px; }}

/* ── Detail Modal ── */
.modal-overlay {{
  position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: 900;
  display: none; align-items: center; justify-content: center;
  backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px);
}}
.modal-overlay.visible {{ display: flex; }}
.modal {{
  background: var(--card); border-radius: 20px; width: 92%; max-width: 500px;
  max-height: 90vh; overflow-y: auto; position: relative;
  box-shadow: 0 24px 70px rgba(0,0,0,0.3); animation: modalIn 0.25s ease;
}}
@keyframes modalIn {{ from {{ opacity: 0; transform: scale(0.95) translateY(10px); }} to {{ opacity: 1; transform: scale(1) translateY(0); }} }}
.m-close {{
  position: absolute; top: 14px; right: 14px; z-index: 10;
  background: rgba(0,0,0,0.45); border: none; color: white;
  width: 34px; height: 34px; border-radius: 50%; font-size: 20px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); transition: background 0.2s;
}}
.m-close:hover {{ background: rgba(0,0,0,0.7); }}
.m-img {{ width: 100%; height: 200px; object-fit: cover; display: block; }}
.m-body {{ padding: 16px 22px 20px; }}
.m-name {{ font-size: 1.05rem; font-weight: 800; margin-bottom: 2px; line-height: 1.25; }}
.m-area {{ font-size: 0.78rem; color: var(--muted); margin-bottom: 10px; }}
.m-score-wrap {{
  background: linear-gradient(135deg, #fff8f0, #fff5eb);
  border: 1px solid #fed7aa; border-radius: 12px; padding: 10px 14px; margin-bottom: 10px;
}}
.m-score-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
.m-score-label {{ font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #92400e; }}
.m-score-num {{ font-size: 1.3rem; font-weight: 900; color: var(--ocean-dark); }}
.m-score-bar {{ height: 8px; border-radius: 4px; background: #f5e6d3; overflow: hidden; }}
.m-score-fill {{ height: 100%; border-radius: 4px; background: linear-gradient(90deg, #f0c27f, #e87d3e, #d4363b); transition: width 0.4s; }}
.m-breakdown {{
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; margin-top: 10px;
  font-size: 0.62rem; color: var(--muted); text-align: center;
}}
.m-breakdown .v {{ font-weight: 700; color: var(--dark); font-size: 0.78rem; }}
.m-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 12px; }}
.m-stat {{ background: var(--bg); border-radius: 10px; padding: 10px 8px; text-align: center; }}
.m-stat .v {{ font-size: 0.95rem; font-weight: 800; color: var(--ocean-dark); }}
.m-stat .v.price-c {{ color: var(--palm); }}
.m-stat .l {{ font-size: 0.58rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }}
.m-badges {{ display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 10px; }}
.m-badge {{ font-size: 0.7rem; font-weight: 600; padding: 4px 10px; border-radius: 7px; }}
.m-badge.fire {{ background: #ffedd5; color: #9a3412; }}
.m-badge.gold {{ background: #fef3c7; color: #92400e; }}
.m-badge.green {{ background: #dcfce7; color: var(--palm); }}
.m-badge.blue {{ background: #dbeafe; color: var(--ocean-dark); }}
.m-badge.red {{ background: #fee2e2; color: #991b1b; }}
.m-airbnb {{
  background: var(--bg); border-radius: 10px; padding: 12px; margin-bottom: 12px;
  border: 1px solid var(--border);
}}
.m-airbnb-title {{ font-size: 0.72rem; font-weight: 700; margin-bottom: 8px; color: var(--dark); }}
.m-airbnb-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; }}
.m-book {{
  display: block; width: 100%; padding: 12px; text-align: center;
  background: linear-gradient(135deg, var(--ocean), var(--ocean-dark));
  color: white; text-decoration: none; border-radius: 12px; font-size: 0.88rem;
  font-weight: 700; font-family: inherit; transition: all 0.2s;
}}
.m-book:hover {{ filter: brightness(1.1); transform: translateY(-1px); }}

/* ── Info sections ── */
.info-section {{ max-width: 1100px; margin: 30px auto; padding: 0 20px; }}
.info-card {{
  background: var(--card); border-radius: 16px; padding: 24px;
  border: 1px solid var(--border); box-shadow: 0 4px 14px rgba(0,0,0,0.05);
}}
.info-card h3 {{ font-size: 1rem; font-weight: 800; margin-bottom: 10px; }}
.info-card p {{ font-size: 0.82rem; color: var(--muted); line-height: 1.7; }}
.info-card strong {{ color: var(--dark); }}

/* ── Search links ── */
.search-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; margin-top: 16px; }}
.search-card {{
  background: var(--card); border-radius: 12px; padding: 16px;
  border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}}
.search-card h4 {{ font-size: 0.85rem; font-weight: 700; margin-bottom: 8px; }}
.search-card a {{ display: block; padding: 4px 0; color: var(--ocean); text-decoration: none; font-size: 0.78rem; }}
.search-card a:hover {{ text-decoration: underline; }}

.footer {{
  text-align: center; padding: 32px 20px 40px; color: var(--muted); font-size: 0.72rem;
  margin-top: 40px;
}}
.footer a {{ color: var(--ocean); text-decoration: none; }}

@media (max-width: 700px) {{
  .pick-hero-card {{ grid-template-columns: 1fr; }}
  .pick-hero-img {{ height: 220px; }}
  .pick-hero-body {{ padding: 20px; }}
  .card {{ flex: 0 0 260px; }}
  .sliders {{ grid-template-columns: 1fr 1fr; gap: 12px; }}
  .explainer-card {{ flex-direction: column; gap: 16px; }}
  .m-grid {{ grid-template-columns: repeat(2, 1fr); }}
  .airbnb-row {{ grid-template-columns: 1fr 1fr; }}
}}
@media (max-width: 480px) {{
  .sliders {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>

<!-- HAMBURGER NAV -->
<button class="hamburger-btn" id="hamburgerBtn" aria-label="Menu">
  <span></span><span></span><span></span>
</button>
<div class="nav-drawer-overlay" id="navOverlay"></div>
<nav class="nav-drawer" id="navDrawer">
  <h3>My Projects</h3>
  <a href="https://matisaar.github.io/greek-property-finder/" class="active">
    <span class="nav-icon">🏖️</span>
    <span class="nav-label">Greek Property Finder<small>Investment properties under 150k CAD</small></span>
  </a>
  <a href="https://matisaar.github.io/beach-trip-planner/">
    <span class="nav-icon">🌊</span>
    <span class="nav-label">Beach Trip Planner<small>Summer 2026 trip planning</small></span>
  </a>
  <a href="https://matisaar.github.io/T661-Checker/">
    <span class="nav-icon">🤖</span>
    <span class="nav-label">T661 AI Trainer<small>AI training tool</small></span>
  </a>
</nav>

<div class="page-hero">
  <h1>🏖️ Greek Property Finder</h1>
  <p>Live-scraped properties across all of Greece, under 150,000 CAD — ranked by your priorities.
  Adjust sliders to weight airport proximity, price, beach distance, size &amp; rental yield.</p>
  <div class="hero-badges">
    <span class="hero-badge">🇬🇷 {len(properties)} Properties</span>
    <span class="hero-badge">✈️ Airport Distance</span>
    <span class="hero-badge">🏖️ Beach Proximity</span>
    <span class="hero-badge">📈 Airbnb Yields</span>
    <span class="hero-badge">🇪🇺 EU Access</span>
  </div>
  <div class="page-hero-nav">
    <a href="#weights">⚙️ Adjust Weights</a>
    <a href="#browse">🔍 Browse All</a>
    <a href="#airbnb">🏠 Airbnb Income</a>
    <a href="#search">🔗 Search Live</a>
  </div>
</div>

<!-- EU NOTICE -->
<div class="eu-bar">
  <strong>🇪🇺 Estonian passport = EU citizen.</strong>
  Buy property in Greece with <strong>zero restrictions</strong>. No Golden Visa needed. Live, work &amp; rent freely.
</div>

<!-- WEIGHT SLIDERS -->
<div class="weights-panel" id="weights">
  <div class="weights-card">
    <div class="weights-header">
      <span class="weights-title">⚙️ Adjust What Matters to You</span>
      <button class="weights-reset" onclick="resetWeights()">Reset</button>
    </div>
    <div class="sliders">
      <div class="slider-group">
        <div class="slider-label">
          <span class="slider-name s-price">💰 Lower Price</span>
          <span class="slider-val" id="vPrice">25%</span>
        </div>
        <input type="range" id="sPrice" min="0" max="100" value="25">
      </div>
      <div class="slider-group">
        <div class="slider-label">
          <span class="slider-name s-airport">✈️ Airport Closeness</span>
          <span class="slider-val" id="vAirport">20%</span>
        </div>
        <input type="range" id="sAirport" min="0" max="100" value="20">
      </div>
      <div class="slider-group">
        <div class="slider-label">
          <span class="slider-name s-beach">🏖️ Beach Closeness</span>
          <span class="slider-val" id="vBeach">20%</span>
        </div>
        <input type="range" id="sBeach" min="0" max="100" value="20">
      </div>
      <div class="slider-group">
        <div class="slider-label">
          <span class="slider-name s-size">📐 Larger Size</span>
          <span class="slider-val" id="vSize">15%</span>
        </div>
        <input type="range" id="sSize" min="0" max="100" value="15">
      </div>
      <div class="slider-group">
        <div class="slider-label">
          <span class="slider-name s-yield">📈 Higher Yield</span>
          <span class="slider-val" id="vYield">15%</span>
        </div>
        <input type="range" id="sYield" min="0" max="100" value="15">
      </div>
      <div class="slider-group">
        <div class="slider-label">
          <span class="slider-name s-reno">🔧 Move-In Ready</span>
          <span class="slider-val" id="vReno">5%</span>
        </div>
        <input type="range" id="sReno" min="0" max="100" value="5">
      </div>
    </div>
  </div>
</div>

<!-- #1 PICK -->
<div class="pick-hero">
  <div class="pick-hero-card" id="heroCard">
    <img class="pick-hero-img" src="" alt="" id="heroImg">
    <div class="pick-hero-body">
      <div class="pick-hero-badge">👑 #1 BEST MATCH</div>
      <div class="pick-hero-name" id="heroName"></div>
      <div class="pick-hero-area" id="heroArea"></div>
      <div class="pick-hero-stats">
        <div class="pick-hero-stat"><div class="val price-c" id="heroPrice"></div><div class="lbl">Price</div></div>
        <div class="pick-hero-stat"><div class="val airport-c" id="heroAirport"></div><div class="lbl">To Airport</div></div>
        <div class="pick-hero-stat"><div class="val beach-c" id="heroBeach"></div><div class="lbl">To Beach</div></div>
        <div class="pick-hero-stat"><div class="val yield-c" id="heroYield"></div><div class="lbl">Gross Yield</div></div>
      </div>
      <div class="pick-hero-score">
        <div class="score-ring">
          <svg viewBox="0 0 48 48">
            <circle class="bg" cx="24" cy="24" r="20"/>
            <circle class="fg" id="heroRing" cx="24" cy="24" r="20"
              stroke-dasharray="125.6" stroke-dashoffset="125.6"/>
          </svg>
          <div class="num" id="heroScoreNum"></div>
        </div>
        <div class="score-info">
          <div class="title">Investment Score</div>
          <div class="desc" id="heroScoreDesc">Best match based on your weights</div>
        </div>
      </div>
      <div id="heroGallery" class="m-gallery" style="margin-top:12px"></div>
      <div id="heroMaps" class="m-maps-row" style="margin-top:8px"></div>
    </div>
  </div>
</div>

<!-- EXPLAINER -->
<div class="explainer">
  <div class="explainer-card">
    <div class="explainer-item">
      <h3>🧪 How scoring works</h3>
      <p>Each property gets a score (0-100) from six normalized dimensions. Adjust sliders above to change weights:</p>
      <div class="explainer-formula" id="formulaDisplay">
        Score = <span>25%</span> Price + <span>20%</span> Airport + <span>20%</span> Beach + <span>15%</span> Size + <span>15%</span> Yield + <span>5%</span> Ready
      </div>
    </div>
    <div class="explainer-item">
      <h3>📊 What we analyzed</h3>
      <p>{len(properties)} properties live-scraped from Rightmove Overseas, all under €102,000 (CA$150k).
      Airport &amp; beach distances auto-computed from GPS coordinates. Airbnb rental estimates based on regional comps.
      Data collected {scraped_date}.</p>
    </div>
  </div>
</div>

<!-- MARKET SNAPSHOT -->
<div style="max-width:1100px;margin:24px auto 0;padding:0 20px;">
  <h3 style="font-size:1rem;font-weight:800;margin-bottom:4px;">📊 Greek Market Snapshot</h3>
  <p style="font-size:0.78rem;color:var(--muted);margin-bottom:12px;">Prices up ~42% in 3 years but moderating. Strong rental demand from tourists &amp; digital nomads.</p>
</div>
<div class="market-row">{market_cards}</div>

<!-- EU/CANADIAN ADVANTAGE -->
<div class="info-section">
  <div class="info-card">
    <h3>🍁 Your Advantage: Canadian + Estonian (EU) Citizenship</h3>
    <p>
      <strong>Estonian passport:</strong> Full EU rights — buy property anywhere in Greece, no restrictions.
      No Golden Visa needed (that requires €250k+ minimum). Rent out on Airbnb or long-term freely.<br><br>
      <strong>Canadian passport:</strong> Banking flexibility + Canada-Greece tax treaty avoids double taxation.<br><br>
      <strong>Key costs:</strong> Transfer tax ~3.09%, notary ~0.65-1%, lawyer ~1-2%. Total ~8-10% on top.
      Rental income: 15% on first €12k/yr. ENFIA property tax: €2-13/m²/yr.
    </p>
  </div>
</div>

<!-- BROWSE ALL -->
<div class="browse-section" id="browse">
  <div class="browse-header">
    <div>
      <div class="browse-title">🔍 Browse All Properties</div>
      <div class="browse-sub">Showing <span class="browse-count" id="browseCount">0</span> properties, ranked by your weights</div>
    </div>
    <div class="filters">
      <select class="filter-select" id="fRegion"><option value="">All Regions</option></select>
      <span class="filter-label">€ max</span>
      <input class="filter-input" id="fPriceMax" type="number" placeholder="Max €" step="1000">
      <span class="filter-label">✈️ max min</span>
      <input class="filter-input" id="fAirportMax" type="number" placeholder="Max" step="10">
      <button class="filter-clear" onclick="clearFilters()">Clear</button>
    </div>
  </div>
  <div class="browse-grid" id="browseGrid"></div>
</div>

<!-- AIRBNB RENTAL INCOME COMPARISON -->
<div class="airbnb-section" id="airbnb">
  <h2 style="font-size:1.3rem;font-weight:800;letter-spacing:-0.3px;">🏠 Airbnb Rental Income Comparison</h2>
  <p style="font-size:0.82rem;color:var(--muted);margin-top:4px;">
    Estimated rental income if you Airbnb each property. Based on regional nightly rates &amp; occupancy data.
    Ranked by gross yield (annual income / purchase price).
  </p>
  <div class="airbnb-grid" id="airbnbGrid"></div>
</div>

<!-- SEARCH LIVE LINKS -->
<div class="info-section" id="search">
  <h2 style="font-size:1.3rem;font-weight:800;margin-bottom:4px;">🔗 Search Live Listings</h2>
  <p style="font-size:0.82rem;color:var(--muted);margin-bottom:12px;">Direct links to portals — prices change daily.</p>
  <div class="search-grid">
    <div class="search-card">
      <h4>🇬🇧 Rightmove Overseas</h4>
      <a href="https://www.rightmove.co.uk/overseas-property-for-sale/Greece.html?maxPrice=87000&amp;sortByPriceDescending=false" target="_blank">All Greece under £87k</a>
      <a href="https://www.rightmove.co.uk/overseas-property-for-sale/Greece/Corfu.html?maxPrice=87000" target="_blank">Corfu</a>
      <a href="https://www.rightmove.co.uk/overseas-property-for-sale/Greece/Crete.html?maxPrice=87000" target="_blank">Crete</a>
      <a href="https://www.rightmove.co.uk/overseas-property-for-sale/Greece/Thessaloniki.html?maxPrice=87000" target="_blank">Thessaloniki Area</a>
    </div>
    <div class="search-card">
      <h4>🏠 Greek Portals (manual)</h4>
      <a href="https://en.spitogatos.gr/search/results/residential/buy" target="_blank">Spitogatos.gr</a>
      <a href="https://www.xe.gr/property/en" target="_blank">xe.gr</a>
      <a href="https://www.tospitimou.gr/" target="_blank">tospitimou.gr</a>
      <p style="font-size:0.7rem;color:var(--muted);margin-top:6px;">Greek sites require manual browsing (bot-protected)</p>
    </div>
    <div class="search-card">
      <h4>✈️ Flights</h4>
      <a href="https://www.google.com/flights?q=flights+to+thessaloniki" target="_blank">→ Thessaloniki (SKG)</a>
      <a href="https://www.google.com/flights?q=flights+to+kavala" target="_blank">→ Kavala (KVA)</a>
      <a href="https://www.google.com/flights?q=flights+to+corfu" target="_blank">→ Corfu (CFU)</a>
      <a href="https://www.google.com/flights?q=flights+to+chania" target="_blank">→ Chania (CHQ)</a>
      <a href="https://www.google.com/flights?q=flights+to+athens" target="_blank">→ Athens (ATH)</a>
    </div>
    <div class="search-card">
      <h4>📊 Research</h4>
      <a href="https://www.globalpropertyguide.com/europe/greece/price-history" target="_blank">Global Property Guide</a>
      <a href="https://tranio.com/greece/buying/" target="_blank">Buying Guide for Foreigners</a>
      <a href="https://tranio.com/greece/taxes/" target="_blank">Tax Guide</a>
    </div>
  </div>
</div>

<!-- MODAL -->
<div class="modal-overlay" id="modalOverlay" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <button class="m-close" onclick="closeModal()">&times;</button>
    <img class="m-img" id="mImg" src="" alt="">
    <div class="m-body">
      <div class="m-name" id="mName"></div>
      <div class="m-area" id="mArea"></div>
      <div class="m-score-wrap">
        <div class="m-score-top">
          <span class="m-score-label">Investment Score</span>
          <span class="m-score-num" id="mScore"></span>
        </div>
        <div class="m-score-bar"><div class="m-score-fill" id="mScoreFill"></div></div>
        <div class="m-breakdown" id="mBreakdown"></div>
      </div>
      <div class="m-grid" id="mStats"></div>
      <div class="m-airbnb" id="mAirbnb">
        <div class="m-airbnb-title">🏠 Airbnb Rental Estimate</div>
        <div class="m-airbnb-grid" id="mAirbnbGrid"></div>
      </div>
      <div class="m-gallery" id="mGallery"></div>
      <div class="m-maps-row" id="mMapsRow"></div>
      <div class="m-badges" id="mBadges"></div>
      <a class="m-book" id="mLink" href="#" target="_blank">View on Rightmove →</a>
    </div>
  </div>
</div>

<div class="footer">
  {len(properties)} properties live-scraped from Rightmove Overseas · Data scraped {scraped_date} · Prices in EUR (CA$1 ≈ €0.68)<br>
  Covers all of Greece — beach &amp; airport distances auto-computed · ⚠️ Verify all listings before purchasing
</div>

<script>
{js_data}
{js_region_data}

// ── Compute normalized values (0–1) ──
const prices = DATA.map(d => d.price);
const areas = DATA.map(d => d.area);
const airports = DATA.map(d => d.airport);
const beaches = DATA.map(d => d.beachKm);
const yields = DATA.map(d => d.grossYield);

const minPrice = Math.min(...prices), maxPrice = Math.max(...prices);
const minArea = Math.min(...areas), maxArea = Math.max(...areas);
const minAirport = Math.min(...airports), maxAirport = Math.max(...airports);
const minBeach = Math.min(...beaches), maxBeach = Math.max(...beaches);
const minYield = Math.min(...yields), maxYield = Math.max(...yields);

DATA.forEach(d => {{
  d.nPrice = maxPrice === minPrice ? 0.5 : (maxPrice - d.price) / (maxPrice - minPrice);
  d.nArea = maxArea === minArea ? 0.5 : (d.area - minArea) / (maxArea - minArea);
  d.nAirport = maxAirport === minAirport ? 0.5 : (maxAirport - d.airport) / (maxAirport - minAirport);
  d.nBeach = maxBeach === minBeach ? 0.5 : (maxBeach - d.beachKm) / (maxBeach - minBeach);
  d.nYield = maxYield === minYield ? 0.5 : (d.grossYield - minYield) / (maxYield - minYield);
  d.nReno = d.reno === 0 ? 1 : 0;
}});

// Populate region filter
const fRegionEl = document.getElementById('fRegion');
const regionNames = [...new Set(DATA.map(d => d.region))];
regionNames.forEach(r => {{
  const o = document.createElement('option');
  o.value = r;
  o.textContent = REGIONS[r] ? REGIONS[r].name : r;
  fRegionEl.appendChild(o);
}});

// ── Weight state ──
let wPrice = 25, wAirport = 20, wBeach = 20, wSize = 15, wYield = 15, wReno = 5;

function score(d) {{
  const total = wPrice + wAirport + wBeach + wSize + wYield + wReno || 1;
  return (d.nPrice * wPrice + d.nAirport * wAirport + d.nBeach * wBeach +
          d.nArea * wSize + d.nYield * wYield + d.nReno * wReno) / total * 100;
}}

function scoreTier(s) {{ return s >= 65 ? 'high' : s >= 40 ? 'mid' : 'low'; }}
function scoreColor(s) {{ return s >= 65 ? '#d4363b' : s >= 40 ? '#e6a756' : '#b8c9d6'; }}

function makeCard(d) {{
  const s = score(d);
  const t = scoreTier(s);
  const photoRow = d.areaPhotos && d.areaPhotos.length ? `
    <div class="card-photos">
      ${{d.areaPhotos.map(u => `<img src="${{u}}" alt="${{d.regionName}} area" loading="lazy" onerror="this.style.display='none'">`).join('')}}
    </div>` : '';
  return `
    <div class="card" onclick="openModal(${{d.id}})">
      <div class="card-img-wrap">
        <img class="card-img" src="${{d.img}}" alt="${{d.title}}" loading="lazy"
             onerror="this.style.background='linear-gradient(135deg,#1e3a5f,#0e76a8)';this.style.minHeight='180px'">
        <div class="card-overlay"></div>
        <div class="card-rank ${{t}}">${{Math.round(s)}}</div>
        <div class="card-price-tag">\u20ac${{d.price.toLocaleString()}}</div>
        <div class="card-airport-tag">✈️ ${{d.airport}} min</div>
      </div>
      ${{photoRow}}
      <div class="card-body">
        <div class="card-name">${{d.title}}</div>
        <div class="card-area">📍 ${{d.regionName}}</div>
        <div class="card-row"><span class="hl">${{d.area}}m²</span> · ${{d.beds}} bed · 🏖️ ${{d.beach}} min · 🏘️ ${{d.nearestCity}} ${{d.nearestCityMin}} min · Yield ${{d.grossYield}}%</div>
        <div class="card-score-bar">
          <div class="bar-track"><div class="bar-fill ${{t}}" style="width:${{s.toFixed(0)}}%"></div></div>
          <span class="bar-num">${{Math.round(s)}}</span>
        </div>
        ${{d.mapsUrl !== '#' ? `<a class="card-maps-btn" href="${{d.mapsUrl}}" target="_blank" onclick="event.stopPropagation()">📍 View on Google Maps</a>` : ''}}
      </div>
    </div>`;
}}

function makeAirbnbCard(d) {{
  return `
    <div class="airbnb-card" onclick="openModal(${{d.id}})">
      <div class="airbnb-card-body">
        <div class="airbnb-card-name">${{d.title}}</div>
        <div class="airbnb-card-region">📍 ${{d.regionName}} · \u20ac${{d.price.toLocaleString()}} · ${{d.area}}m²</div>
        <div class="airbnb-row">
          <div class="airbnb-stat"><div class="v green">\u20ac${{d.airbnbRate}}</div><div class="l">Per Night</div></div>
          <div class="airbnb-stat"><div class="v gold">\u20ac${{d.annualIncome.toLocaleString()}}</div><div class="l">Annual</div></div>
          <div class="airbnb-stat"><div class="v blue">${{d.grossYield}}%</div><div class="l">Gross Yield</div></div>
        </div>
        <div style="display:flex;flex-direction:column;gap:4px;">
          <div class="airbnb-bar">
            <div class="airbnb-bar-label">Occupancy</div>
            <div class="airbnb-bar-track"><div class="airbnb-bar-fill occ" style="width:${{d.airbnbOcc}}%"></div></div>
            <div class="airbnb-bar-num">${{d.airbnbOcc}}%</div>
          </div>
          <div class="airbnb-bar">
            <div class="airbnb-bar-label">Yield</div>
            <div class="airbnb-bar-track"><div class="airbnb-bar-fill roi" style="width:${{Math.min(d.grossYield/15*100,100).toFixed(0)}}%"></div></div>
            <div class="airbnb-bar-num">${{d.grossYield}}%</div>
          </div>
        </div>
      </div>
    </div>`;
}}

function rebuild() {{
  const ranked = DATA.map(d => ({{...d, sc: score(d)}})).sort((a,b) => b.sc - a.sc);

  // Hero = #1
  const hero = ranked[0];
  const hs = hero.sc;

  document.getElementById('heroImg').src = hero.img;
  document.getElementById('heroImg').onerror = function(){{ this.style.background='linear-gradient(135deg,#1e3a5f,#0e76a8)'; this.style.minHeight='250px'; }};
  document.getElementById('heroName').textContent = hero.title;
  document.getElementById('heroArea').textContent = '📍 ' + hero.regionName + ' · ' + hero.area + 'm² · ' + hero.beds + ' bed';
  document.getElementById('heroPrice').textContent = '\u20ac' + hero.price.toLocaleString();
  document.getElementById('heroAirport').textContent = hero.airport + ' min';
  document.getElementById('heroBeach').innerHTML = `<a href="${{hero.beachUrl}}" target="_blank" style="color:inherit;text-decoration:underline dotted">${{hero.beachKm}} km</a>`;
  document.getElementById('heroYield').textContent = hero.grossYield + '%';
  document.getElementById('heroScoreNum').textContent = Math.round(hs);
  document.getElementById('heroCard').onclick = () => openModal(hero.id);
  const ring = document.getElementById('heroRing');
  ring.style.stroke = scoreColor(hs);
  ring.style.strokeDashoffset = 125.6 * (1 - hs / 100);

  // Hero area gallery
  const hGallery = document.getElementById('heroGallery');
  if (hero.areaPhotos && hero.areaPhotos.length) {{
    hGallery.innerHTML = hero.areaPhotos.map(u => `<img src="${{u}}" alt="${{hero.regionName}} area" loading="lazy" onerror="this.style.display='none'">`).join('');
  }} else {{ hGallery.innerHTML = ''; }}

  // Hero maps buttons
  const hMaps = document.getElementById('heroMaps');
  let mapsHtml = '';
  if (hero.mapsUrl !== '#') mapsHtml += `<a class="m-maps-btn" href="${{hero.mapsUrl}}" target="_blank" onclick="event.stopPropagation()">📍 Google Maps</a>`;
  mapsHtml += `<a class="m-maps-btn listing" href="${{hero.url}}" target="_blank" onclick="event.stopPropagation()">🏠 View Listing</a>`;
  hMaps.innerHTML = mapsHtml;

  // Update formula display
  const total = wPrice + wAirport + wBeach + wSize + wYield + wReno || 1;
  const pcts = [wPrice, wAirport, wBeach, wSize, wYield, wReno].map(w => Math.round(w / total * 100));
  const diff = 100 - pcts.reduce((a,b)=>a+b,0);
  pcts[0] += diff;
  document.getElementById('formulaDisplay').innerHTML =
    `Score = <span>${{pcts[0]}}%</span> Price + <span>${{pcts[1]}}%</span> Airport + <span>${{pcts[2]}}%</span> Beach + <span>${{pcts[3]}}%</span> Size + <span>${{pcts[4]}}%</span> Yield + <span>${{pcts[5]}}%</span> Ready`;

  rebuildBrowse();
  rebuildAirbnb();
}}

// ── Browse All Logic ──
function getFilters() {{
  return {{
    region: document.getElementById('fRegion').value,
    priceMax: parseFloat(document.getElementById('fPriceMax').value) || Infinity,
    airportMax: parseFloat(document.getElementById('fAirportMax').value) || Infinity,
  }};
}}

function rebuildBrowse() {{
  const f = getFilters();
  const filtered = DATA
    .map(d => ({{...d, sc: score(d)}}))
    .filter(d => {{
      if (f.region && d.region !== f.region) return false;
      if (d.price > f.priceMax) return false;
      if (d.airport > f.airportMax) return false;
      return true;
    }})
    .sort((a, b) => b.sc - a.sc);

  document.getElementById('browseCount').textContent = filtered.length;
  document.getElementById('browseGrid').innerHTML = filtered.map(d => makeCard(d)).join('');
}}

function rebuildAirbnb() {{
  const sorted = [...DATA].sort((a,b) => b.grossYield - a.grossYield);
  document.getElementById('airbnbGrid').innerHTML = sorted.map(d => makeAirbnbCard(d)).join('');
}}

function clearFilters() {{
  document.getElementById('fRegion').value = '';
  document.getElementById('fPriceMax').value = '';
  document.getElementById('fAirportMax').value = '';
  rebuildBrowse();
}}

// Filter change listeners
['fRegion', 'fPriceMax', 'fAirportMax'].forEach(id => {{
  const el = document.getElementById(id);
  el.addEventListener('change', rebuildBrowse);
  el.addEventListener('input', () => {{ clearTimeout(el._t); el._t = setTimeout(rebuildBrowse, 400); }});
}});

// ── Slider events ──
const sliderIds = ['sPrice', 'sAirport', 'sBeach', 'sSize', 'sYield', 'sReno'];
const valIds = ['vPrice', 'vAirport', 'vBeach', 'vSize', 'vYield', 'vReno'];

function updateFromSliders() {{
  wPrice = +document.getElementById('sPrice').value;
  wAirport = +document.getElementById('sAirport').value;
  wBeach = +document.getElementById('sBeach').value;
  wSize = +document.getElementById('sSize').value;
  wYield = +document.getElementById('sYield').value;
  wReno = +document.getElementById('sReno').value;
  const total = wPrice + wAirport + wBeach + wSize + wYield + wReno || 1;
  const weights = [wPrice, wAirport, wBeach, wSize, wYield, wReno];
  weights.forEach((w, i) => {{
    document.getElementById(valIds[i]).textContent = Math.round(w / total * 100) + '%';
  }});
  rebuild();
}}

sliderIds.forEach(id => {{
  document.getElementById(id).addEventListener('input', updateFromSliders);
}});

function resetWeights() {{
  const defaults = [25, 20, 20, 15, 15, 5];
  sliderIds.forEach((id, i) => {{ document.getElementById(id).value = defaults[i]; }});
  updateFromSliders();
}}

// ── Modal ──
function openModal(id) {{
  const d = DATA.find(x => x.id === id);
  if (!d) return;
  const s = score(d);
  document.getElementById('mImg').src = d.img;
  document.getElementById('mImg').onerror = function(){{ this.style.background='linear-gradient(135deg,#1e3a5f,#0e76a8)'; this.style.minHeight='200px'; }};
  document.getElementById('mName').textContent = d.title;
  document.getElementById('mArea').textContent = '📍 ' + d.regionName;
  document.getElementById('mScore').textContent = Math.round(s) + '/100';
  document.getElementById('mScoreFill').style.width = s.toFixed(0) + '%';

  document.getElementById('mBreakdown').innerHTML = `
    <div><div class="v">\u20ac${{d.price.toLocaleString()}}</div>Price</div>
    <div><div class="v">${{d.airport}} min</div>Airport</div>
    <div><a href="${{d.beachUrl}}" target="_blank" style="text-decoration:none"><div class="v" style="text-decoration:underline dotted;cursor:pointer">${{d.beachKm}} km</div></a>Beach</div>
  `;

  document.getElementById('mStats').innerHTML = `
    <div class="m-stat"><div class="v price-c">\u20ac${{d.price.toLocaleString()}}</div><div class="l">Price</div></div>
    <div class="m-stat"><div class="v">CA$${{d.cad.toLocaleString()}}</div><div class="l">CAD</div></div>
    <div class="m-stat"><div class="v">${{d.area}}m\u00b2</div><div class="l">Size</div></div>
    <div class="m-stat"><div class="v">${{d.beds}}</div><div class="l">Beds</div></div>
    <div class="m-stat"><div class="v">${{d.airport}} min</div><div class="l">✈️ Airport</div></div>
    <div class="m-stat"><a href="${{d.beachUrl}}" target="_blank" style="text-decoration:none"><div class="v" style="text-decoration:underline dotted">${{d.beachKm}} km</div><div class="l">🏖️ ${{d.beachName}}</div></a></div>
  `;

  document.getElementById('mAirbnbGrid').innerHTML = `
    <div class="m-stat"><div class="v" style="color:var(--palm)">\u20ac${{d.airbnbRate}}/n</div><div class="l">Nightly</div></div>
    <div class="m-stat"><div class="v" style="color:var(--gold)">\u20ac${{d.annualIncome.toLocaleString()}}/yr</div><div class="l">Annual</div></div>
    <div class="m-stat"><div class="v" style="color:var(--ocean)">${{d.grossYield}}%</div><div class="l">Gross Yield</div></div>
  `;

  // Area gallery
  const gallery = document.getElementById('mGallery');
  if (d.areaPhotos && d.areaPhotos.length) {{
    gallery.innerHTML = d.areaPhotos.map(u => `<img src="${{u}}" alt="Area" loading="lazy" onerror="this.style.display='none'">`).join('');
  }} else {{ gallery.innerHTML = ''; }}

  // Maps + listing + beach buttons
  let mRow = '';
  if (d.beachUrl) mRow += `<a class="m-maps-btn" href="${{d.beachUrl}}" target="_blank">🏖️ ${{d.beachKm}} km to ${{d.beachName}}</a>`;
  if (d.mapsUrl !== '#') mRow += `<a class="m-maps-btn" href="${{d.mapsUrl}}" target="_blank">📍 Open in Google Maps</a>`;
  mRow += `<a class="m-maps-btn listing" href="${{d.url}}" target="_blank">🏠 View Listing</a>`;
  document.getElementById('mMapsRow').innerHTML = mRow;

  let b = '';
  if (s >= 65) b += '<span class="m-badge fire">🔥 Top Match</span>';
  if (d.airport <= 30) b += '<span class="m-badge red">✈️ Close Airport</span>';
  if (d.beachKm <= 2) b += '<span class="m-badge blue">🏖️ Beach Nearby</span>';
  if (d.grossYield >= 6) b += '<span class="m-badge green">📈 High Yield</span>';
  if (d.reno === 0) b += '<span class="m-badge gold">✅ Move-in Ready</span>';
  if (d.area >= 100) b += '<span class="m-badge blue">📐 Large Property</span>';
  document.getElementById('mBadges').innerHTML = b;

  document.getElementById('mLink').href = d.url;
  document.getElementById('mLink').textContent = 'View on ' + d.source + ' \u2192';
  document.getElementById('modalOverlay').classList.add('visible');
}}

function closeModal() {{
  document.getElementById('modalOverlay').classList.remove('visible');
}}
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});

// ── Hamburger menu ──
const hBtn = document.getElementById('hamburgerBtn');
const nDrawer = document.getElementById('navDrawer');
const nOverlay = document.getElementById('navOverlay');
function toggleNav() {{
  hBtn.classList.toggle('open');
  nDrawer.classList.toggle('open');
  nOverlay.classList.toggle('open');
}}
hBtn.addEventListener('click', toggleNav);
nOverlay.addEventListener('click', toggleNav);

// ── Smooth scroll for nav links ──
document.querySelectorAll('.page-hero-nav a[href^="#"]').forEach(a => {{
  a.addEventListener('click', e => {{
    e.preventDefault();
    const target = document.querySelector(a.getAttribute('href'));
    if (target) target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }});
}});

// ── Initial render ──
rebuild();
</script>
</body>
</html>'''

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Site generated: docs/index.html ({len(properties)} properties)")
    return "docs/index.html"


if __name__ == "__main__":
    generate_site()
