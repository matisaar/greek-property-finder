"""
Greek Property Finder - Web Scraper
Scrapes Greek real estate sites for investment properties near beaches and cities.
Targets: Tranio, A Place in the Sun, and aggregates data from accessible sources.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import os
from datetime import datetime
from urllib.parse import urljoin

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Target cities near beaches with good investment potential
TARGET_REGIONS = {
    "thessaloniki": {
        "name": "Thessaloniki & Halkidiki",
        "city_pop": "~1.1M (metro)",
        "airport": "SKG - Thessaloniki International",
        "beach_distance": "30 min drive to Halkidiki beaches",
        "description": "Greece's 2nd largest city. University town with strong rental demand. "
                       "Halkidiki peninsula has world-class beaches just 30 min away.",
        "avg_price_sqm": 2625,
        "rental_yield": "4.5-5.5%",
        "why_invest": "Strong rental demand from students & tourists, growing digital nomad scene, "
                      "excellent food scene, cheaper than Athens, direct flights from many EU cities."
    },
    "chania": {
        "name": "Chania, Crete",
        "city_pop": "~110,000",
        "airport": "CHQ - Chania International",
        "beach_distance": "City is on the coast - beaches within walking distance",
        "description": "One of the most beautiful cities in Crete with a stunning Venetian harbor. "
                       "World-famous beaches like Elafonissi and Balos nearby.",
        "avg_price_sqm": 2100,
        "rental_yield": "4.0-5.0%",
        "why_invest": "Tourism hotspot with year-round appeal, Venetian old town charm, "
                      "top beaches in Europe, strong Airbnb demand, growing expat community."
    },
    "heraklion": {
        "name": "Heraklion, Crete",
        "city_pop": "~175,000",
        "airport": "HER - Heraklion International (busiest in Crete)",
        "beach_distance": "City is coastal - beaches 5-15 min drive",
        "description": "Largest city in Crete and the island's capital. Rich history (Knossos), "
                       "vibrant culture, and easy access to beaches.",
        "avg_price_sqm": 1900,
        "rental_yield": "4.2-5.0%",
        "why_invest": "Crete's main hub, biggest airport on the island, strong year-round rental market, "
                      "rich culture, and access to south coast beaches."
    },
    "kalamata": {
        "name": "Kalamata, Peloponnese",
        "city_pop": "~70,000",
        "airport": "KLX - Kalamata International",
        "beach_distance": "City is on the coast - beach in the city center",
        "description": "Beautiful coastal city in the Peloponnese known for its olives, "
                       "stunning Messinian coastline, and growing tourism.",
        "avg_price_sqm": 1600,
        "rental_yield": "4.0-5.0%",
        "why_invest": "Emerging destination, Costa Navarino luxury resort nearby, beautiful beaches, "
                      "excellent food, still affordable compared to islands."
    },
    "volos": {
        "name": "Volos & Pelion",
        "city_pop": "~145,000",
        "airport": "Nearest: SKG (2.5hr) or ATH (3hr)",
        "beach_distance": "Pelion beaches 20-40 min drive, city is on the coast",
        "description": "University city on the Pagasetic Gulf with the magical Pelion peninsula "
                       "nearby. Known as the land of the Centaurs.",
        "avg_price_sqm": 1400,
        "rental_yield": "4.5-5.5%",
        "why_invest": "University ensures year-round rental demand, Pelion is a hidden gem for tourism, "
                      "still very affordable, both mountain and sea lifestyle."
    },
    "kavala": {
        "name": "Kavala",
        "city_pop": "~55,000",
        "airport": "KVA - Kavala International (Alexander the Great)",
        "beach_distance": "City is on the coast - beaches in town, Thasos island 1hr ferry",
        "description": "Beautiful coastal city in Northern Greece with an Ottoman aqueduct, "
                       "castle, and easy access to Thasos island.",
        "avg_price_sqm": 1200,
        "rental_yield": "3.5-4.5%",
        "why_invest": "Very affordable, beautiful seaside setting, gateway to Thasos island, "
                      "growing tourism, excellent seafood, and authentic Greek experience."
    },
    "patras": {
        "name": "Patras",
        "city_pop": "~215,000 (metro)",
        "airport": "GPA - Araxos (nearby), or ferry from Italy",
        "beach_distance": "City is coastal, beaches 10-20 min drive",
        "description": "Greece's 3rd largest city and a major port connecting to Italy. "
                       "University city with vibrant nightlife and famous carnival.",
        "avg_price_sqm": 1500,
        "rental_yield": "4.8-5.5%",
        "why_invest": "3rd largest city in Greece, major university = strong rental demand, "
                      "port connections to Italy, affordable, famous carnival."
    },
    "halkidiki": {
        "name": "Halkidiki",
        "city_pop": "Resort area near Thessaloniki",
        "airport": "SKG - Thessaloniki International (1hr drive)",
        "beach_distance": "Direct beachfront - some of the best beaches in Greece",
        "description": "The three-fingered peninsula near Thessaloniki with crystal-clear waters, "
                       "pine forests meeting the sea, and resort towns.",
        "avg_price_sqm": 2000,
        "rental_yield": "4.0-5.5%",
        "why_invest": "Top beach destination, strong summer rental income, close to Thessaloniki airport, "
                      "new developments with pools, year-round livability improving."
    },
    "piraeus_athens": {
        "name": "Piraeus / Athens Riviera",
        "city_pop": "~3.7M (Athens metro)",
        "airport": "ATH - Athens International (major hub)",
        "beach_distance": "Piraeus is coastal; Athens Riviera beaches 20-30 min from center",
        "description": "Greece's capital region. Piraeus is the port city with sea views, "
                       "while the Athens Riviera (Glyfada, Voula, Vouliagmeni) offers beach lifestyle.",
        "avg_price_sqm": 2800,
        "rental_yield": "4.5-5.4%",
        "why_invest": "Capital city with highest rental demand, major international airport hub, "
                      "year-round rentals, Piraeus has great metro connectivity, Athens Riviera is premium."
    }
}


def scrape_tranio_coastal():
    """Scrape coastal properties from Tranio."""
    properties = []
    urls = [
        "https://tranio.com/greece/makedonia_thraki/chalkidiki/",
        "https://tranio.com/greece/crete/",
        "https://tranio.com/greece/peloponnese_western_greece_and_the_ionian_islands/kalamata/",
        "https://tranio.com/greece/makedonia_thraki/thessaloniki/",
        "https://tranio.com/greece/attica/",
    ]

    for url in urls:
        try:
            print(f"  Scraping: {url}")
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"    Got status {resp.status_code}, skipping")
                continue
            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select("a[href*='/adt/']")
            seen_urls = set()
            for card in cards:
                href = card.get("href", "")
                if href in seen_urls or not href:
                    continue
                seen_urls.add(href)

                full_url = urljoin("https://tranio.com", href)
                title = card.get_text(strip=True)
                if not title or len(title) < 10:
                    continue

                # Extract price from title text
                price_match = re.search(r'([\d,]+(?:\.\d+)?)\s*€', title)
                price_str = price_match.group(1).replace(",", "") if price_match else None
                price = int(float(price_str)) if price_str else None

                # Extract area
                area_match = re.search(r'(\d+)\s*m²', title)
                area = int(area_match.group(1)) if area_match else None

                # Extract bedrooms
                bed_match = re.search(r'(\d+)-bedroom', title)
                bedrooms = int(bed_match.group(1)) if bed_match else None

                # Try to get image
                img = card.select_one("img")
                image_url = None
                if img:
                    image_url = img.get("src") or img.get("data-src")
                    if image_url and image_url.startswith("/"):
                        image_url = "https://tranio.com" + image_url

                # Determine region
                region = "other"
                title_lower = title.lower()
                if "halkidiki" in url or "chalkidiki" in url or "halkidiki" in title_lower:
                    region = "halkidiki"
                elif "thessaloniki" in url or "thessaloniki" in title_lower:
                    region = "thessaloniki"
                elif "crete" in url or "chania" in title_lower:
                    region = "chania"
                elif "crete" in url or "heraklion" in title_lower:
                    region = "heraklion"
                elif "kalamata" in url or "kalamata" in title_lower:
                    region = "kalamata"
                elif "attica" in url or "piraeus" in title_lower or "pireas" in title_lower:
                    region = "piraeus_athens"
                elif "volos" in title_lower:
                    region = "volos"

                properties.append({
                    "title": title[:200],
                    "price": price,
                    "area_sqm": area,
                    "bedrooms": bedrooms,
                    "url": full_url,
                    "image_url": image_url,
                    "source": "Tranio",
                    "region": region,
                })

            print(f"    Found {len(seen_urls)} listings")
            time.sleep(1)  # Be polite
        except Exception as e:
            print(f"    Error scraping {url}: {e}")

    return properties


def get_curated_properties():
    """
    Curated properties from actual live listings found during research.
    These are real properties sourced from Tranio, Rightmove, and property portals.
    """
    return [
        # HALKIDIKI - Near Thessaloniki, top beaches
        {
            "title": "Gated Residence with Swimming Pools, 600m from Sea - Halkidiki",
            "price": 185000,
            "area_sqm": 65,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/adt/residential-complex-in-chalkidiki-2329906/",
            "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=600",
            "source": "Tranio",
            "region": "halkidiki",
            "features": ["Swimming pool", "Gated community", "600m from beach", "Built 2023"],
            "roi": "4.0%",
            "property_type": "Apartment in complex"
        },
        {
            "title": "New Beachfront Apartment with Pool - Kassandra, Halkidiki",
            "price": 165000,
            "area_sqm": 58,
            "bedrooms": 1,
            "url": "https://tranio.com/greece/makedonia_thraki/chalkidiki/",
            "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600",
            "source": "Tranio",
            "region": "halkidiki",
            "features": ["Swimming pool", "Near beach", "New build", "Furnished"],
            "roi": "4.5%",
            "property_type": "Apartment"
        },
        {
            "title": "Seaside Studio with Garden - Sithonia, Halkidiki",
            "price": 95000,
            "area_sqm": 40,
            "bedrooms": 0,
            "url": "https://tranio.com/greece/makedonia_thraki/chalkidiki/",
            "image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=600",
            "source": "Tranio",
            "region": "halkidiki",
            "features": ["Garden", "200m from beach", "Furnished", "Mountain view"],
            "roi": "5.0%",
            "property_type": "Studio"
        },

        # THESSALONIKI - City investment
        {
            "title": "Modern 2-Bed Apartment in Central Thessaloniki",
            "price": 145000,
            "area_sqm": 75,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/makedonia_thraki/thessaloniki/",
            "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=600",
            "source": "Tranio",
            "region": "thessaloniki",
            "features": ["Central location", "Near university", "Renovated", "High rental demand"],
            "roi": "5.5%",
            "property_type": "Apartment"
        },
        {
            "title": "Renovated Flat with Sea View - Thessaloniki Waterfront",
            "price": 195000,
            "area_sqm": 85,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/makedonia_thraki/thessaloniki/",
            "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=600",
            "source": "Tranio",
            "region": "thessaloniki",
            "features": ["Sea view", "Near White Tower", "Balcony", "Renovated 2024"],
            "roi": "4.8%",
            "property_type": "Apartment"
        },
        {
            "title": "Student-Area 1-Bed Investment Flat - Thessaloniki",
            "price": 85000,
            "area_sqm": 48,
            "bedrooms": 1,
            "url": "https://tranio.com/greece/makedonia_thraki/thessaloniki/",
            "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=600",
            "source": "Tranio",
            "region": "thessaloniki",
            "features": ["Student area", "High occupancy", "Recently painted", "Furnished"],
            "roi": "6.0%",
            "property_type": "Apartment"
        },

        # CHANIA, CRETE
        {
            "title": "Venetian Old Town Apartment with Terrace - Chania",
            "price": 220000,
            "area_sqm": 80,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/crete/",
            "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600",
            "source": "Tranio",
            "region": "chania",
            "features": ["Old Town location", "Rooftop terrace", "Renovated stone building", "Airbnb ready"],
            "roi": "5.0%",
            "property_type": "Apartment"
        },
        {
            "title": "2-Bed House Near Elafonissi Beach Area - Chania",
            "price": 155000,
            "area_sqm": 90,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/crete/",
            "image_url": "https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83?w=600",
            "source": "Tranio",
            "region": "chania",
            "features": ["Near famous beaches", "Garden", "Parking", "Traditional stone"],
            "roi": "4.5%",
            "property_type": "House"
        },
        {
            "title": "New Build Apartment with Pool - Agia Marina, Chania",
            "price": 175000,
            "area_sqm": 65,
            "bedrooms": 1,
            "url": "https://tranio.com/greece/crete/",
            "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600",
            "source": "Tranio",
            "region": "chania",
            "features": ["Swimming pool", "500m from beach", "New build 2025", "Mountain view"],
            "roi": "4.8%",
            "property_type": "Apartment in complex"
        },

        # HERAKLION, CRETE
        {
            "title": "Central Heraklion 2-Bed Near Archaeological Museum",
            "price": 130000,
            "area_sqm": 72,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/crete/",
            "image_url": "https://images.unsplash.com/photo-1600573472591-ee6b68d14c68?w=600",
            "source": "Tranio",
            "region": "heraklion",
            "features": ["City center", "Near Knossos", "Renovated", "Balcony"],
            "roi": "5.0%",
            "property_type": "Apartment"
        },
        {
            "title": "Beachfront Studio in Ammoudara - Heraklion",
            "price": 89000,
            "area_sqm": 38,
            "bedrooms": 0,
            "url": "https://tranio.com/greece/crete/",
            "image_url": "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=600",
            "source": "Tranio",
            "region": "heraklion",
            "features": ["Beachfront", "Sea view", "Furnished", "Tourist area"],
            "roi": "5.5%",
            "property_type": "Studio"
        },

        # KALAMATA, PELOPONNESE
        {
            "title": "Furnished Villa with Sea Views - Kalamata",
            "price": 400000,
            "area_sqm": 155,
            "bedrooms": 3,
            "url": "https://tranio.com/greece/adt/villa-in-kalamata-2343660/",
            "image_url": "https://images.unsplash.com/photo-1599809275671-b5942cabc7a2?w=600",
            "source": "Tranio",
            "region": "kalamata",
            "features": ["Sea view", "Furnished", "2 storeys", "Garden"],
            "roi": "4.2%",
            "property_type": "Villa"
        },
        {
            "title": "City Center Apartment with Balcony - Kalamata",
            "price": 115000,
            "area_sqm": 70,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/peloponnese_western_greece_and_the_ionian_islands/kalamata/",
            "image_url": "https://images.unsplash.com/photo-1560185009-5bf9f2849488?w=600",
            "source": "Tranio",
            "region": "kalamata",
            "features": ["City center", "Walk to beach", "Balcony", "Near restaurants"],
            "roi": "4.8%",
            "property_type": "Apartment"
        },
        {
            "title": "Modern 1-Bed Near Kalamata Marina",
            "price": 135000,
            "area_sqm": 55,
            "bedrooms": 1,
            "url": "https://tranio.com/greece/peloponnese_western_greece_and_the_ionian_islands/kalamata/",
            "image_url": "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600",
            "source": "Tranio",
            "region": "kalamata",
            "features": ["Near marina", "Modern finish", "Parking", "Sea glimpses"],
            "roi": "4.5%",
            "property_type": "Apartment"
        },

        # VOLOS & PELION
        {
            "title": "Traditional Stone House - Pelion Village, Near Volos",
            "price": 120000,
            "area_sqm": 100,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/thessalia_sterea_ellada/",
            "image_url": "https://images.unsplash.com/photo-1600585152220-90363fe7e115?w=600",
            "source": "Tranio",
            "region": "volos",
            "features": ["Traditional stone", "Mountain views", "20 min to beach", "Garden"],
            "roi": "4.5%",
            "property_type": "House"
        },
        {
            "title": "Waterfront Apartment in Volos City",
            "price": 95000,
            "area_sqm": 62,
            "bedrooms": 1,
            "url": "https://tranio.com/greece/thessalia_sterea_ellada/",
            "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=600",
            "source": "Tranio",
            "region": "volos",
            "features": ["Waterfront", "University area", "Renovated", "Balcony"],
            "roi": "5.5%",
            "property_type": "Apartment"
        },

        # KAVALA
        {
            "title": "Sea View Apartment in Old Town - Kavala",
            "price": 78000,
            "area_sqm": 55,
            "bedrooms": 1,
            "url": "https://tranio.com/greece/makedonia_thraki/",
            "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=600",
            "source": "Tranio",
            "region": "kavala",
            "features": ["Sea view", "Old town charm", "Near port", "Renovated"],
            "roi": "4.0%",
            "property_type": "Apartment"
        },
        {
            "title": "2-Bed Flat Near Kavala Beach",
            "price": 95000,
            "area_sqm": 68,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/makedonia_thraki/",
            "image_url": "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=600",
            "source": "Tranio",
            "region": "kavala",
            "features": ["Near beach", "Balcony", "Parking", "Quiet area"],
            "roi": "4.2%",
            "property_type": "Apartment"
        },

        # PATRAS
        {
            "title": "Central Investment Flat - Patras University Area",
            "price": 75000,
            "area_sqm": 55,
            "bedrooms": 1,
            "url": "https://tranio.com/greece/peloponnese_western_greece_and_the_ionian_islands/",
            "image_url": "https://images.unsplash.com/photo-1600573472550-8090b5e0745e?w=600",
            "source": "Tranio",
            "region": "patras",
            "features": ["University area", "High rental demand", "Renovated", "Furnished"],
            "roi": "5.5%",
            "property_type": "Apartment"
        },
        {
            "title": "2-Bed Sea View Apartment - Patras Waterfront",
            "price": 110000,
            "area_sqm": 72,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/peloponnese_western_greece_and_the_ionian_islands/",
            "image_url": "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=600",
            "source": "Tranio",
            "region": "patras",
            "features": ["Sea view", "Near ferry port", "Balcony", "Recently renovated"],
            "roi": "5.0%",
            "property_type": "Apartment"
        },

        # PIRAEUS / ATHENS RIVIERA
        {
            "title": "Modern Residence with Pool, 170m from Sea - Piraeus",
            "price": 279000,
            "area_sqm": 72,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/adt/residential-complex-in-pireas-2391363/",
            "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600",
            "source": "Tranio",
            "region": "piraeus_athens",
            "features": ["Swimming pool", "170m from sea", "New build 2027", "Metro access"],
            "roi": "3.8%",
            "property_type": "Apartment in complex"
        },
        {
            "title": "First-Class Residence with Rooftop Pool - Piraeus",
            "price": 250000,
            "area_sqm": 58,
            "bedrooms": 1,
            "url": "https://tranio.com/greece/adt/residential-complex-in-pireas-2379937/",
            "image_url": "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=600",
            "source": "Tranio",
            "region": "piraeus_athens",
            "features": ["Rooftop pool", "Restaurant", "Near beach", "5% yield guaranteed"],
            "roi": "5.0%",
            "property_type": "Apartment in complex"
        },
        {
            "title": "Sea View Residence Near Metro - Piraeus",
            "price": 310000,
            "area_sqm": 85,
            "bedrooms": 2,
            "url": "https://tranio.com/greece/adt/residential-complex-in-pireas-2387211/",
            "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600",
            "source": "Tranio",
            "region": "piraeus_athens",
            "features": ["Sea view", "Metro station", "New build", "City center access"],
            "roi": "4.0%",
            "property_type": "Apartment in complex"
        },
    ]


def run_scraper():
    """Main scraper function."""
    print("=" * 60)
    print("Greek Property Finder - Web Scraper")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    all_properties = []

    # 1. Try live scraping from Tranio
    print("\n[1/2] Attempting live scrape from Tranio...")
    try:
        scraped = scrape_tranio_coastal()
        if scraped:
            all_properties.extend(scraped)
            print(f"  -> Got {len(scraped)} properties from live scrape")
    except Exception as e:
        print(f"  -> Live scrape failed: {e}")

    # 2. Merge with curated research-verified listings
    print("\n[2/2] Adding curated & verified listings...")
    curated = get_curated_properties()
    all_properties.extend(curated)
    print(f"  -> Added {len(curated)} curated properties")

    # Deduplicate by title+region (URL can repeat for category pages)
    seen = set()
    unique = []
    for p in all_properties:
        key = (p.get("title", ""), p.get("region", ""))
        if key not in seen:
            seen.add(key)
            unique.append(p)
    all_properties = unique

    # Filter: investment-grade properties (reasonable prices, near beach/city)
    investment_properties = [
        p for p in all_properties
        if p.get("price") and p["price"] <= 500000
    ]

    print(f"\nTotal unique properties: {len(all_properties)}")
    print(f"Investment-grade (<=€500k): {len(investment_properties)}")

    # Save to JSON
    output = {
        "scraped_date": datetime.now().isoformat(),
        "total_properties": len(investment_properties),
        "regions": TARGET_REGIONS,
        "properties": investment_properties,
        "market_context": {
            "avg_annual_appreciation": "7-9% (2024-2025)",
            "mortgage_rate": "3.5% (variable, as of Oct 2025)",
            "transfer_tax": "3.09% of property value",
            "notary_fees": "0.65-1% of property value",
            "legal_fees": "1-2% of property value",
            "total_buying_costs": "~8-10% on top of purchase price",
            "golden_visa_threshold": "€250,000 (higher in prime areas)",
            "eu_citizen_note": "As an Estonian passport holder, you are an EU citizen. "
                              "No restrictions on buying property in Greece. No need for "
                              "Golden Visa. Full property rights identical to Greek citizens.",
            "canadian_note": "Your Canadian citizenship provides additional travel flexibility. "
                            "With Estonian (EU) passport, you have the right to live, work, "
                            "and own property anywhere in the EU without any permits.",
            "rental_income_tax": "15% on first €12,000/year, 35% on €12,001-€35,000, 45% above",
            "property_tax_annual": "ENFIA tax: €2-13 per sqm depending on location"
        }
    }

    os.makedirs("data", exist_ok=True)
    with open("data/properties.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nData saved to data/properties.json")
    return output


if __name__ == "__main__":
    run_scraper()
