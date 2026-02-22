"""
Generate a beautiful static HTML site from scraped property data.
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

    # Sort properties by price
    properties.sort(key=lambda p: p.get("price", 999999))

    # Group by region
    by_region = {}
    for p in properties:
        r = p.get("region", "other")
        if r not in by_region:
            by_region[r] = []
        by_region[r].append(p)

    # Generate property cards HTML
    def card_html(p):
        price = p.get("price", 0)
        price_fmt = f"€{price:,.0f}" if price else "Price on request"
        area = p.get("area_sqm")
        area_str = f"{area} m²" if area else "N/A"
        beds = p.get("bedrooms")
        bed_str = f"{beds} bed" if beds and beds > 0 else ("Studio" if beds == 0 else "N/A")
        roi = p.get("roi", "")
        features = p.get("features", [])
        ptype = p.get("property_type", "Property")
        img = p.get("image_url", "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600")
        region_info = regions.get(p.get("region", ""), {})
        region_name = region_info.get("name", p.get("region", "").replace("_", " ").title())
        price_per_sqm = f"€{price // area:,.0f}/m²" if price and area else ""
        cad_price = f"CA${int(price * 1.48):,.0f}" if price else ""

        features_html = ""
        if features:
            features_html = '<div class="features">' + "".join(
                f'<span class="feature-tag">{f}</span>' for f in features[:4]
            ) + "</div>"

        roi_badge = f'<span class="roi-badge">ROI {roi}</span>' if roi else ""

        return f'''
        <div class="property-card" data-region="{p.get('region', 'other')}" data-price="{price}" data-beds="{beds if beds else -1}" data-area="{area if area else 0}">
            <div class="card-image">
                <img src="{img}" alt="{p.get('title', 'Property')}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600'">
                <span class="card-region">{region_name}</span>
                <span class="card-type">{ptype}</span>
                {roi_badge}
            </div>
            <div class="card-body">
                <h3 class="card-title">{p.get('title', 'Property')}</h3>
                <div class="card-price">
                    <span class="price-eur">{price_fmt}</span>
                    <span class="price-cad">{cad_price}</span>
                </div>
                <div class="card-stats">
                    <span class="stat"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="2"/><text x="12" y="16" text-anchor="middle" font-size="10" fill="currentColor" stroke="none">m²</text></svg> {area_str}</span>
                    <span class="stat"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v11a2 2 0 002 2h14a2 2 0 002-2V7"/><path d="M3 7l9-4 9 4"/></svg> {bed_str}</span>
                    <span class="stat price-sqm">{price_per_sqm}</span>
                </div>
                {features_html}
                <a href="{p.get('url', '#')}" target="_blank" rel="noopener" class="card-link">
                    View on {p.get('source', 'Source')} &rarr;
                </a>
            </div>
        </div>'''

    # Generate region summary cards
    def region_summary(key, info):
        props = by_region.get(key, [])
        if not props:
            return ""
        prices = [p["price"] for p in props if p.get("price")]
        min_p = min(prices) if prices else 0
        max_p = max(prices) if prices else 0
        count = len(props)

        return f'''
        <div class="region-card" data-region-key="{key}">
            <h3>{info["name"]}</h3>
            <div class="region-stats">
                <div class="region-stat">
                    <span class="stat-label">Population</span>
                    <span class="stat-value">{info["city_pop"]}</span>
                </div>
                <div class="region-stat">
                    <span class="stat-label">Airport</span>
                    <span class="stat-value">{info["airport"]}</span>
                </div>
                <div class="region-stat">
                    <span class="stat-label">Beach</span>
                    <span class="stat-value">{info["beach_distance"]}</span>
                </div>
                <div class="region-stat">
                    <span class="stat-label">Avg Price/m²</span>
                    <span class="stat-value">€{info["avg_price_sqm"]:,}</span>
                </div>
                <div class="region-stat">
                    <span class="stat-label">Rental Yield</span>
                    <span class="stat-value">{info["rental_yield"]}</span>
                </div>
                <div class="region-stat">
                    <span class="stat-label">Listings</span>
                    <span class="stat-value">{count} properties</span>
                </div>
            </div>
            <p class="region-desc">{info["description"]}</p>
            <p class="region-why"><strong>Why invest:</strong> {info["why_invest"]}</p>
            <div class="region-price-range">
                Price range: <strong>€{min_p:,.0f} - €{max_p:,.0f}</strong>
                (CA${int(min_p*1.48):,.0f} - CA${int(max_p*1.48):,.0f})
            </div>
            <button class="btn-filter-region" onclick="filterByRegion('{key}')">
                Show {count} Properties &darr;
            </button>
        </div>'''

    all_cards = "\n".join(card_html(p) for p in properties)
    all_regions = "\n".join(
        region_summary(k, v)
        for k, v in sorted(regions.items(), key=lambda x: x[1]["avg_price_sqm"])
        if k in by_region
    )

    # Region filter buttons
    region_filters = '<button class="filter-btn active" onclick="filterByRegion(\'all\')">All Regions</button>\n'
    for k, v in sorted(regions.items(), key=lambda x: x[1]["name"]):
        if k in by_region:
            count = len(by_region[k])
            region_filters += f'<button class="filter-btn" onclick="filterByRegion(\'{k}\')">{v["name"]} ({count})</button>\n'

    # Build comparison table rows (outside f-string to avoid escaping issues)
    comparison_rows = ""
    for p in properties:
        empty = {}
        region_name = regions.get(p.get("region", ""), empty).get("name", p.get("region", "").replace("_", " ").title())
        title = p.get("title", "")[:50]
        price = p.get("price", 0)
        cad = int(price * 1.48)
        area = p.get("area_sqm", 0) or 0
        psqm = price // area if area else 0
        psqm_str = f"€{psqm:,.0f}" if area else "N/A"
        beds = p.get("bedrooms", -1) if p.get("bedrooms") is not None else -1
        beds_str = str(p.get("bedrooms", "N/A"))
        roi = p.get("roi", "")
        ptype = p.get("property_type", "")
        url = p.get("url", "#")
        comparison_rows += f'''<tr>
            <td>{region_name}</td>
            <td>{title}</td>
            <td data-sort="{price}">€{price:,.0f}</td>
            <td data-sort="{cad}">CA${cad:,.0f}</td>
            <td data-sort="{area}">{area} m²</td>
            <td data-sort="{psqm}">{psqm_str}</td>
            <td data-sort="{beds}">{beds_str}</td>
            <td>{roi}</td>
            <td>{ptype}</td>
            <td><a href="{url}" target="_blank" rel="noopener">View &rarr;</a></td>
        </tr>\n'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Greek Property Finder - Investment Properties Near Beach & City</title>
    <meta name="description" content="Find investment properties in Greece near beaches and cities. Curated listings for Canadian/EU investors.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --blue: #0066cc;
            --blue-dark: #004d99;
            --blue-light: #e6f0ff;
            --green: #059669;
            --green-light: #d1fae5;
            --orange: #ea580c;
            --orange-light: #fff7ed;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-500: #6b7280;
            --gray-700: #374151;
            --gray-900: #111827;
            --shadow: 0 1px 3px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 25px rgba(0,0,0,0.1);
            --radius: 12px;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--gray-50);
            color: var(--gray-900);
            line-height: 1.6;
        }}

        /* HERO */
        .hero {{
            background: linear-gradient(135deg, #1e3a5f 0%, #0e76a8 50%, #1a9bc7 100%);
            color: white;
            padding: 60px 20px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .hero::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: url('https://images.unsplash.com/photo-1555993539-1732b0258235?w=1600') center/cover;
            opacity: 0.15;
        }}
        .hero > * {{ position: relative; z-index: 1; }}
        .hero h1 {{ font-size: 2.5rem; font-weight: 700; margin-bottom: 12px; }}
        .hero .subtitle {{ font-size: 1.15rem; opacity: 0.9; max-width: 700px; margin: 0 auto 20px; }}
        .hero-badges {{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-top: 16px; }}
        .hero-badge {{
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.3);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }}

        /* NOTICE BAR */
        .notice-bar {{
            background: var(--green-light);
            border-bottom: 1px solid #a7f3d0;
            padding: 14px 20px;
            text-align: center;
            font-size: 0.9rem;
            color: #065f46;
        }}
        .notice-bar strong {{ color: #047857; }}

        /* CONTAINER */
        .container {{ max-width: 1280px; margin: 0 auto; padding: 0 20px; }}

        /* SECTION */
        .section {{ padding: 40px 0; }}
        .section-title {{
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--gray-900);
        }}
        .section-subtitle {{
            color: var(--gray-500);
            margin-bottom: 24px;
            font-size: 1rem;
        }}

        /* MARKET CONTEXT */
        .market-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}
        .market-card {{
            background: white;
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow);
            border: 1px solid var(--gray-200);
        }}
        .market-card .label {{ font-size: 0.8rem; color: var(--gray-500); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
        .market-card .value {{ font-size: 1.1rem; font-weight: 600; color: var(--gray-900); }}

        /* EU NOTICE */
        .eu-notice {{
            background: var(--blue-light);
            border: 1px solid #bfdbfe;
            border-radius: var(--radius);
            padding: 24px;
            margin-bottom: 30px;
        }}
        .eu-notice h3 {{ color: var(--blue-dark); margin-bottom: 8px; font-size: 1.1rem; }}
        .eu-notice p {{ color: #1e40af; font-size: 0.95rem; }}

        /* REGION CARDS */
        .region-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .region-card {{
            background: white;
            border-radius: var(--radius);
            padding: 24px;
            box-shadow: var(--shadow);
            border: 1px solid var(--gray-200);
            transition: box-shadow 0.2s;
        }}
        .region-card:hover {{ box-shadow: var(--shadow-lg); }}
        .region-card h3 {{ font-size: 1.25rem; margin-bottom: 12px; color: var(--blue-dark); }}
        .region-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-bottom: 12px;
        }}
        .region-stat {{ text-align: center; }}
        .stat-label {{ display: block; font-size: 0.7rem; color: var(--gray-500); text-transform: uppercase; letter-spacing: 0.5px; }}
        .stat-value {{ display: block; font-size: 0.85rem; font-weight: 600; }}
        .region-desc {{ font-size: 0.9rem; color: var(--gray-700); margin-bottom: 8px; }}
        .region-why {{ font-size: 0.85rem; color: var(--green); margin-bottom: 10px; }}
        .region-price-range {{ font-size: 0.9rem; margin-bottom: 12px; color: var(--gray-700); }}
        .btn-filter-region {{
            width: 100%;
            padding: 10px;
            background: var(--blue);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.2s;
        }}
        .btn-filter-region:hover {{ background: var(--blue-dark); }}

        /* FILTERS */
        .filters {{
            background: white;
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow);
            border: 1px solid var(--gray-200);
            margin-bottom: 24px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }}
        .filters label {{ font-weight: 600; font-size: 0.85rem; color: var(--gray-700); }}
        .filter-btn {{
            padding: 8px 16px;
            border: 1px solid var(--gray-300);
            border-radius: 20px;
            background: white;
            cursor: pointer;
            font-size: 0.85rem;
            font-weight: 500;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .filter-btn:hover {{ border-color: var(--blue); color: var(--blue); }}
        .filter-btn.active {{ background: var(--blue); color: white; border-color: var(--blue); }}
        .filter-sort {{
            margin-left: auto;
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .filter-sort select {{
            padding: 8px 12px;
            border: 1px solid var(--gray-300);
            border-radius: 8px;
            font-size: 0.85rem;
            background: white;
        }}
        .filter-range {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        .filter-range input {{
            width: 100px;
            padding: 8px;
            border: 1px solid var(--gray-300);
            border-radius: 8px;
            font-size: 0.85rem;
        }}

        /* PROPERTY GRID */
        .property-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }}
        .property-card {{
            background: white;
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: var(--shadow);
            border: 1px solid var(--gray-200);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .property-card:hover {{ transform: translateY(-4px); box-shadow: var(--shadow-lg); }}
        .card-image {{
            position: relative;
            height: 200px;
            overflow: hidden;
        }}
        .card-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        .card-region {{
            position: absolute;
            top: 12px;
            left: 12px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .card-type {{
            position: absolute;
            top: 12px;
            right: 12px;
            background: var(--blue);
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .roi-badge {{
            position: absolute;
            bottom: 12px;
            right: 12px;
            background: var(--green);
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
        }}
        .card-body {{ padding: 16px; }}
        .card-title {{ font-size: 1rem; font-weight: 600; margin-bottom: 8px; line-height: 1.4; color: var(--gray-900); }}
        .card-price {{ margin-bottom: 10px; }}
        .price-eur {{ font-size: 1.35rem; font-weight: 700; color: var(--blue-dark); }}
        .price-cad {{ font-size: 0.85rem; color: var(--gray-500); margin-left: 8px; }}
        .card-stats {{
            display: flex;
            gap: 14px;
            margin-bottom: 10px;
            color: var(--gray-500);
            font-size: 0.85rem;
        }}
        .stat {{ display: flex; align-items: center; gap: 4px; }}
        .price-sqm {{ margin-left: auto; font-weight: 600; color: var(--gray-700); }}
        .features {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }}
        .feature-tag {{
            background: var(--gray-100);
            color: var(--gray-700);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        .card-link {{
            display: block;
            text-align: center;
            padding: 10px;
            background: var(--blue);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            transition: background 0.2s;
        }}
        .card-link:hover {{ background: var(--blue-dark); }}

        /* COMPARISON TABLE */
        .comparison-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: var(--shadow);
            margin-top: 20px;
        }}
        .comparison-table th {{
            background: var(--gray-900);
            color: white;
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
            white-space: nowrap;
        }}
        .comparison-table td {{
            padding: 10px 16px;
            border-bottom: 1px solid var(--gray-200);
            font-size: 0.85rem;
        }}
        .comparison-table tr:nth-child(even) {{ background: var(--gray-50); }}
        .comparison-table tr:hover {{ background: var(--blue-light); }}
        .comparison-table a {{ color: var(--blue); text-decoration: none; font-weight: 500; }}
        .comparison-table a:hover {{ text-decoration: underline; }}

        /* LIVE SEARCH LINKS */
        .search-links {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }}
        .search-link-card {{
            background: white;
            border-radius: var(--radius);
            padding: 20px;
            box-shadow: var(--shadow);
            border: 1px solid var(--gray-200);
        }}
        .search-link-card h4 {{ margin-bottom: 10px; color: var(--gray-900); }}
        .search-link-card a {{
            display: block;
            padding: 6px 0;
            color: var(--blue);
            text-decoration: none;
            font-size: 0.9rem;
        }}
        .search-link-card a:hover {{ text-decoration: underline; }}

        /* FOOTER */
        footer {{
            background: var(--gray-900);
            color: var(--gray-300);
            padding: 40px 20px;
            text-align: center;
            font-size: 0.85rem;
        }}
        footer a {{ color: var(--blue); }}
        .disclaimer {{ max-width: 700px; margin: 16px auto 0; font-size: 0.8rem; color: var(--gray-500); }}

        .count-display {{
            font-size: 0.9rem;
            color: var(--gray-500);
            margin-bottom: 16px;
        }}

        /* Tabs */
        .tabs {{ display: flex; gap: 4px; margin-bottom: 24px; background: var(--gray-100); padding: 4px; border-radius: 10px; width: fit-content; }}
        .tab-btn {{
            padding: 10px 20px;
            border: none;
            background: transparent;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9rem;
            border-radius: 8px;
            transition: all 0.2s;
            color: var(--gray-500);
        }}
        .tab-btn.active {{ background: white; color: var(--gray-900); box-shadow: var(--shadow); }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}

        .no-results {{
            text-align: center;
            padding: 60px 20px;
            color: var(--gray-500);
            font-size: 1.1rem;
        }}

        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 1.75rem; }}
            .property-grid {{ grid-template-columns: 1fr; }}
            .region-grid {{ grid-template-columns: 1fr; }}
            .market-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .filters {{ flex-direction: column; }}
            .filter-sort {{ margin-left: 0; }}
            .region-stats {{ grid-template-columns: repeat(2, 1fr); }}
            .comparison-table {{ font-size: 0.75rem; }}
            .comparison-table td, .comparison-table th {{ padding: 6px 8px; }}
            .tabs {{ width: 100%; overflow-x: auto; }}
        }}
    </style>
</head>
<body>

<!-- HERO -->
<div class="hero">
    <h1>🏖️ Greek Property Finder</h1>
    <p class="subtitle">
        Budget investment properties under 100,000 CAD (≈€65,000) near beaches & cities in Greece.
        Curated for a Canadian/Estonian EU citizen exploring affordable Greek real estate.
    </p>
    <div class="hero-badges">
        <span class="hero-badge">🇬🇷 {len(properties)} Properties</span>
        <span class="hero-badge">🏖️ Beach Proximity</span>
        <span class="hero-badge">🏙️ Near Cities</span>
        <span class="hero-badge">📈 Investment Focus</span>
        <span class="hero-badge">🇪🇺 EU Citizen Rights</span>
    </div>
</div>

<!-- EU CITIZEN NOTICE -->
<div class="notice-bar">
    <strong>🇪🇺 Estonian passport = EU citizen.</strong>
    You can buy property in Greece with <strong>zero restrictions</strong>, identical rights to Greek citizens.
    No Golden Visa needed. You can live, work, and rent out property freely.
</div>

<div class="container">

<!-- YOUR SITUATION -->
<div class="section">
    <div class="eu-notice">
        <h3>🍁 Your Advantage: Canadian + Estonian (EU) Dual Citizenship</h3>
        <p>
            <strong>Estonian passport:</strong> Full EU citizen rights - buy property anywhere in Greece without restrictions.
            No need for Golden Visa program (which requires €250,000+ minimum). You can buy at any price point.
            You can rent out your property (long-term or Airbnb) and even live in Greece permanently.<br><br>
            <strong>Canadian passport:</strong> Additional travel flexibility and banking options. Canada-Greece tax treaty
            helps avoid double taxation on rental income.<br><br>
            <strong>Key costs:</strong> Transfer tax ~3.09%, notary ~0.65-1%, lawyer ~1-2%. Total ~8-10% on top of purchase price.
            Rental income taxed at 15% on first €12,000/year. Annual property tax (ENFIA) is €2-13/m² depending on location.
        </p>
    </div>
</div>

<!-- MARKET CONTEXT -->
<div class="section">
    <h2 class="section-title">📊 Greek Market Snapshot (2025-2026)</h2>
    <p class="section-subtitle">Prices have risen ~42% in 3 years but growth is moderating. Strong rental demand from tourists and digital nomads.</p>
    <div class="market-grid">
        <div class="market-card">
            <div class="label">Annual Appreciation</div>
            <div class="value">{market['avg_annual_appreciation']}</div>
        </div>
        <div class="market-card">
            <div class="label">Mortgage Rate</div>
            <div class="value">{market['mortgage_rate']}</div>
        </div>
        <div class="market-card">
            <div class="label">Transfer Tax</div>
            <div class="value">{market['transfer_tax']}</div>
        </div>
        <div class="market-card">
            <div class="label">Total Buying Costs</div>
            <div class="value">{market['total_buying_costs']}</div>
        </div>
        <div class="market-card">
            <div class="label">Rental Income Tax</div>
            <div class="value">15% (first €12k)</div>
        </div>
        <div class="market-card">
            <div class="label">Annual Property Tax</div>
            <div class="value">€2-13/m² (ENFIA)</div>
        </div>
    </div>
</div>

<!-- TABS -->
<div class="section">
    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('regions')">📍 By Region</button>
        <button class="tab-btn" onclick="switchTab('properties')">🏠 All Properties</button>
        <button class="tab-btn" onclick="switchTab('comparison')">📋 Comparison Table</button>
        <button class="tab-btn" onclick="switchTab('links')">🔗 Live Search Links</button>
    </div>

    <!-- REGIONS TAB -->
    <div id="tab-regions" class="tab-content active">
        <h2 class="section-title">Investment Regions</h2>
        <p class="section-subtitle">Click a region to see its properties. All regions have beaches + city amenities.</p>
        <div class="region-grid">
            {all_regions}
        </div>
    </div>

    <!-- PROPERTIES TAB -->
    <div id="tab-properties" class="tab-content">
        <h2 class="section-title">All Properties</h2>
        <p class="section-subtitle">Filter and sort to find your ideal investment + vacation property.</p>

        <div class="filters">
            <label>Region:</label>
            {region_filters}
        </div>
        <div class="filters">
            <label>Sort:</label>
            <div class="filter-sort">
                <select id="sort-select" onchange="sortProperties()">
                    <option value="price-asc">Price: Low to High</option>
                    <option value="price-desc">Price: High to Low</option>
                    <option value="area-desc">Size: Largest First</option>
                    <option value="psqm-asc">€/m²: Low to High</option>
                </select>
            </div>
            <label style="margin-left: 16px;">Max price:</label>
            <div class="filter-range">
                <input type="number" id="max-price" placeholder="€ max" onchange="applyFilters()" value="">
            </div>
        </div>

        <div class="count-display" id="count-display">Showing {len(properties)} properties</div>
        <div class="property-grid" id="property-grid">
            {all_cards}
        </div>
        <div class="no-results" id="no-results" style="display:none">
            No properties match your filters. Try adjusting your criteria.
        </div>
    </div>

    <!-- COMPARISON TAB -->
    <div id="tab-comparison" class="tab-content">
        <h2 class="section-title">Side-by-Side Comparison</h2>
        <p class="section-subtitle">All properties in a sortable table format. Click column headers to sort.</p>
        <div style="overflow-x: auto;">
        <table class="comparison-table" id="comparison-table">
            <thead>
                <tr>
                    <th onclick="sortTable(0)" style="cursor:pointer">Region ↕</th>
                    <th onclick="sortTable(1)" style="cursor:pointer">Property ↕</th>
                    <th onclick="sortTable(2)" style="cursor:pointer">Price (€) ↕</th>
                    <th onclick="sortTable(3)" style="cursor:pointer">Price (CA$) ↕</th>
                    <th onclick="sortTable(4)" style="cursor:pointer">Area (m²) ↕</th>
                    <th onclick="sortTable(5)" style="cursor:pointer">€/m² ↕</th>
                    <th onclick="sortTable(6)" style="cursor:pointer">Beds ↕</th>
                    <th>ROI</th>
                    <th>Type</th>
                    <th>Link</th>
                </tr>
            </thead>
            <tbody>
                {comparison_rows}
            </tbody>
        </table>
        </div>
    </div>

    <!-- LIVE SEARCH LINKS TAB -->
    <div id="tab-links" class="tab-content">
        <h2 class="section-title">🔗 Search Live Listings Yourself</h2>
        <p class="section-subtitle">Direct links to search on major Greek real estate portals. Prices and availability change daily.</p>
        <div class="search-links">
            <div class="search-link-card">
                <h4>�🇧 Rightmove Overseas (Budget under £55k / €65k)</h4>
                <a href="https://www.rightmove.co.uk/overseas-property-for-sale/Greece.html?maxPrice=55000&sortByPriceDescending=false" target="_blank">All Greece under £55k</a>
                <a href="https://www.rightmove.co.uk/overseas-property-for-sale/Greece/Corfu.html?maxPrice=55000" target="_blank">Corfu listings</a>
                <a href="https://www.rightmove.co.uk/overseas-property-for-sale/Greece/Crete.html?maxPrice=55000" target="_blank">Crete listings</a>
                <a href="https://www.rightmove.co.uk/overseas-property-for-sale/Greece/Cephalonia.html?maxPrice=55000" target="_blank">Cephalonia listings</a>
            </div>
            <div class="search-link-card">
                <h4>🏠 Spitogatos.gr (Largest Greek portal)</h4>
                <a href="https://en.spitogatos.gr/search/results/residential/buy" target="_blank">Browse all Greece</a>
                <a href="https://en.spitogatos.gr/search/results/residential/buy?geo_place_ids[]=ChIJ8UNwBh-9oRQR3Y1mdkU1Nic" target="_blank">Northern Greece</a>
                <a href="https://en.spitogatos.gr/search/results/residential/buy?geo_place_ids[]=ChIJZ07eRWGEhBQRIL8BPxhkSaQ" target="_blank">Chania, Crete</a>
                <a href="https://en.spitogatos.gr/search/results/residential/buy?geo_place_ids[]=ChIJoQLn3YvhgxQRp9lfWq2IJis" target="_blank">Ionian Islands</a>
            </div>
            <div class="search-link-card">
                <h4>🔍 Properstar.com</h4>
                <a href="https://www.properstar.com/greece/buy" target="_blank">All Greece</a>
                <a href="https://www.properstar.com/greece/crete-region/buy" target="_blank">Crete region</a>
                <a href="https://www.properstar.com/greece/macedonia-and-thrace/buy" target="_blank">Macedonia & Thrace</a>
                <a href="https://www.properstar.com/greece/peloponnese-western-greece-ionian/buy" target="_blank">Peloponnese & Ionian</a>
            </div>
            <div class="search-link-card">
                <h4>📊 Market Research</h4>
                <a href="https://www.globalpropertyguide.com/europe/greece/price-history" target="_blank">Global Property Guide - Greece</a>
                <a href="https://en.spitogatos.gr/blog/real-estate-market-greece-q3-2025" target="_blank">Spitogatos Market Report Q3 2025</a>
                <a href="https://tranio.com/greece/buying/" target="_blank">Buying Guide for Foreigners</a>
                <a href="https://tranio.com/greece/taxes/" target="_blank">Property Tax Guide</a>
            </div>
            <div class="search-link-card">
                <h4>✈️ Flight Connections</h4>
                <a href="https://www.google.com/flights?q=flights+to+corfu" target="_blank">Flights to Corfu (CFU)</a>
                <a href="https://www.google.com/flights?q=flights+to+chania" target="_blank">Flights to Chania (CHQ)</a>
                <a href="https://www.google.com/flights?q=flights+to+thessaloniki" target="_blank">Flights to Thessaloniki (SKG)</a>
                <a href="https://www.google.com/flights?q=flights+to+volos" target="_blank">Flights to Volos (VOL)</a>
                <a href="https://www.google.com/flights?q=flights+to+athens" target="_blank">Flights to Athens (ATH)</a>
            </div>
        </div>
    </div>
</div>

</div><!-- container -->

<!-- FOOTER -->
<footer>
    <p>Greek Property Finder &middot; Data scraped on {scraped_date} &middot;
    Built for a 🍁 Canadian / 🇪🇪 Estonian exploring Greek investment opportunities</p>
    <p class="disclaimer">
        ⚠️ <strong>Disclaimer:</strong> This site is for informational purposes only. Property data is aggregated from
        public real estate portals and may not reflect current prices or availability. Always verify listings directly
        with agents and conduct proper due diligence before purchasing. Exchange rate used: €1 ≈ CA$1.48.
        Consult a Greek lawyer and tax advisor before any purchase.
    </p>
</footer>

<script>
// Tab switching
function switchTab(tab) {{
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    event.target.classList.add('active');
}}

// Region filter
let currentRegion = 'all';
function filterByRegion(region) {{
    currentRegion = region;
    // Switch to properties tab
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById('tab-properties').classList.add('active');
    document.querySelectorAll('.tab-btn')[1].classList.add('active');

    // Update filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {{
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase().includes(region) || (region === 'all' && btn.textContent.includes('All'))) {{
            btn.classList.add('active');
        }}
    }});

    applyFilters();
}}

function applyFilters() {{
    const maxPrice = parseInt(document.getElementById('max-price').value) || Infinity;
    const cards = document.querySelectorAll('.property-card');
    let visible = 0;

    cards.forEach(card => {{
        const cardRegion = card.dataset.region;
        const cardPrice = parseInt(card.dataset.price) || 0;
        const regionMatch = currentRegion === 'all' || cardRegion === currentRegion;
        const priceMatch = cardPrice <= maxPrice;

        if (regionMatch && priceMatch) {{
            card.style.display = '';
            visible++;
        }} else {{
            card.style.display = 'none';
        }}
    }});

    document.getElementById('count-display').textContent = `Showing ${{visible}} properties`;
    document.getElementById('no-results').style.display = visible === 0 ? '' : 'none';
}}

// Sort properties
function sortProperties() {{
    const grid = document.getElementById('property-grid');
    const cards = Array.from(grid.querySelectorAll('.property-card'));
    const sortBy = document.getElementById('sort-select').value;

    cards.sort((a, b) => {{
        switch(sortBy) {{
            case 'price-asc': return (parseInt(a.dataset.price)||0) - (parseInt(b.dataset.price)||0);
            case 'price-desc': return (parseInt(b.dataset.price)||0) - (parseInt(a.dataset.price)||0);
            case 'area-desc': return (parseInt(b.dataset.area)||0) - (parseInt(a.dataset.area)||0);
            case 'psqm-asc':
                const aP = (parseInt(a.dataset.price)||0) / (parseInt(a.dataset.area)||1);
                const bP = (parseInt(b.dataset.price)||0) / (parseInt(b.dataset.area)||1);
                return aP - bP;
        }}
        return 0;
    }});

    cards.forEach(card => grid.appendChild(card));
}}

// Sort comparison table
let sortAsc = {{}};
function sortTable(n) {{
    const table = document.getElementById('comparison-table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    sortAsc[n] = !sortAsc[n];

    rows.sort((a, b) => {{
        let aVal = a.cells[n].dataset.sort || a.cells[n].textContent.trim();
        let bVal = b.cells[n].dataset.sort || b.cells[n].textContent.trim();

        const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
        const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));

        if (!isNaN(aNum) && !isNaN(bNum)) {{
            return sortAsc[n] ? aNum - bNum : bNum - aNum;
        }}
        return sortAsc[n] ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }});

    rows.forEach(row => tbody.appendChild(row));
}}
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
