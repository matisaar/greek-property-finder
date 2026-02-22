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

# Budget: 100,000 CAD ≈ €65,000 EUR — regions with affordable properties
TARGET_REGIONS = {
    "ionian_islands": {
        "name": "Corfu & Cephalonia, Ionian Islands",
        "city_pop": "Corfu Town ~40,000; Argostoli ~14,000",
        "airport": "CFU (Corfu), EFL (Cephalonia) - seasonal EU flights",
        "beach_distance": "Islands are entirely coastal - beaches everywhere",
        "description": "The Ionian Islands on Greece's west coast have lush green landscapes, "
                       "crystal-clear turquoise waters, and Venetian architecture. Corfu and "
                       "Cephalonia offer some of Greece's most affordable island properties.",
        "avg_price_sqm": 900,
        "rental_yield": "4-6% (Airbnb seasonal)",
        "why_invest": "Affordable island properties, strong summer Airbnb demand, Venetian charm, "
                      "international airport access, EU ferry routes, authentic character homes, "
                      "renovation potential with high upside."
    },
    "northern_greece": {
        "name": "Drama & Serres, Northern Greece",
        "city_pop": "Drama ~60,000; Serres ~76,000",
        "airport": "SKG - Thessaloniki International (1-2 hr drive)",
        "beach_distance": "1-2 hours to Kavala coast & Thassos island beaches",
        "description": "Affordable cities in Northern Greece with very low cost of living. "
                       "Drama is known for wine country and scenic mountains, Serres for its "
                       "cultural heritage. Cheapest property market in Greece.",
        "avg_price_sqm": 500,
        "rental_yield": "5-7%",
        "why_invest": "Cheapest property prices in Greece, high rental yields relative to price, "
                      "growing domestic tourism, university rental demand, large houses for "
                      "the price of a studio elsewhere, cross-border visitors from Bulgaria."
    },
    "crete": {
        "name": "Chania, Western Crete",
        "city_pop": "~110,000",
        "airport": "CHQ - Chania International",
        "beach_distance": "City is on the coast - beaches within walking distance",
        "description": "One of the most beautiful cities in Crete with a stunning Venetian harbor. "
                       "World-famous beaches like Elafonissi and Balos nearby. Budget properties "
                       "available in mountain villages with easy beach access.",
        "avg_price_sqm": 1400,
        "rental_yield": "4-5%",
        "why_invest": "Tourism hotspot with year-round appeal, Venetian old town charm, "
                      "top beaches in Europe, strong Airbnb demand. Mountain village renovations "
                      "offer great value within budget."
    },
    "pelion_sporades": {
        "name": "Pelion & Alonnisos, Thessaly",
        "city_pop": "Volos ~145,000 (nearby hub)",
        "airport": "VOL - Volos Nea Anchialos (seasonal); SKG 2.5hr",
        "beach_distance": "Pelion has beaches on both sides; Alonnisos is entirely coastal",
        "description": "Pelion peninsula combines mountain villages with beautiful beaches. "
                       "Alonnisos is a pristine Sporades island with Greece's first marine park. "
                       "Both are off the mass-tourism radar, offering authentic Greek experiences.",
        "avg_price_sqm": 800,
        "rental_yield": "4-5% (seasonal)",
        "why_invest": "Hidden gem destinations, growing ecotourism, affordable prices, "
                      "Pelion ski + beach combo, Alonnisos marine park, less competition "
                      "from mass tourism, authentic character properties."
    },
    "attica": {
        "name": "Athens / Attica",
        "city_pop": "~3.7M (Athens metro)",
        "airport": "ATH - Athens International (major hub)",
        "beach_distance": "Athens Riviera beaches 20-30 min from center",
        "description": "Greece's capital region. Student areas like Zografos near universities "
                       "offer affordable apartments with strong year-round rental demand. "
                       "Best city for non-seasonal rental income.",
        "avg_price_sqm": 1800,
        "rental_yield": "5-6%",
        "why_invest": "Capital city with highest rental demand, major international airport hub, "
                      "year-round rentals (not seasonal), university district properties "
                      "have consistent tenant demand, metro connectivity."
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
    Curated budget properties from Rightmove Overseas, verified Feb 2026.
    Budget: 100,000 CAD ≈ €65,000 EUR.
    All URLs point to real individual Rightmove listing pages.
    """
    return [
        # === CORFU, IONIAN ISLANDS ===
        {
            "title": "1-Bed Stone House - Corfu Island",
            "price": 58000,
            "area_sqm": 55,
            "bedrooms": 1,
            "url": "https://www.rightmove.co.uk/properties/169757939#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/f501791a2/169757939/f501791a2928226c700059ba540bd212_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "ionian_islands",
            "features": ["Stone house", "Renovation potential", "Corfu island"],
            "roi": "4-6% (Airbnb)",
            "property_type": "House"
        },
        {
            "title": "2-Bed Property - Episkepsi, Corfu",
            "price": 60000,
            "area_sqm": 65,
            "bedrooms": 2,
            "url": "https://www.rightmove.co.uk/properties/147192746#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/52bf02e40/147192746/52bf02e402b24e10d1554e133d5e1f20_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "ionian_islands",
            "features": ["2 bedrooms", "North Corfu village", "Character property"],
            "roi": "4-5%",
            "property_type": "Property"
        },
        {
            "title": "2-Bed House - Karoussades, Corfu",
            "price": 69000,
            "area_sqm": 70,
            "bedrooms": 2,
            "url": "https://www.rightmove.co.uk/properties/157731170#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/1b5a9b9fe/157731170/1b5a9b9fe22825c0dbe215304a13d6d3_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "ionian_islands",
            "features": ["2 bedrooms", "Near north coast beaches", "Village charm"],
            "roi": "4-5%",
            "property_type": "House"
        },
        {
            "title": "3-Bed Property - Karoussades, Corfu",
            "price": 70000,
            "area_sqm": 85,
            "bedrooms": 3,
            "url": "https://www.rightmove.co.uk/properties/147192809#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/00fb7730c/147192809/00fb7730c403292ec505cb1ff08ed713_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "ionian_islands",
            "features": ["3 bedrooms", "North Corfu", "Near beaches"],
            "roi": "4-5%",
            "property_type": "Property"
        },
        {
            "title": "Property - Lakones, Corfu (Paleokastritsa area)",
            "price": 69000,
            "area_sqm": 60,
            "bedrooms": None,
            "url": "https://www.rightmove.co.uk/properties/147192770#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/9ee07dcfe/147192770/9ee07dcfe83bebe53a96d432940f7c3a_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "ionian_islands",
            "features": ["Near Paleokastritsa", "Corfu west coast", "Scenic location"],
            "roi": "4-6% (Airbnb)",
            "property_type": "Property"
        },

        # === CEPHALONIA, IONIAN ISLANDS ===
        {
            "title": "2-Bed House - Agia Irini, Cephalonia",
            "price": 58000,
            "area_sqm": 70,
            "bedrooms": 2,
            "url": "https://www.rightmove.co.uk/properties/164335409#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/ccbf671f7/164335409/ccbf671f791c9dd8962d06901e2cd4c7_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "ionian_islands",
            "features": ["2 bedrooms", "Cephalonia island", "Reduced price"],
            "roi": "4-5%",
            "property_type": "House"
        },
        {
            "title": "1-Bed Detached House - Kaminarata, Cephalonia",
            "price": 60000,
            "area_sqm": 50,
            "bedrooms": 1,
            "url": "https://www.rightmove.co.uk/properties/169522346#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/f02587829/169522346/f025878293b87c713ee22cc648c961cd_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "ionian_islands",
            "features": ["Detached house", "Cephalonia village", "Close to beaches"],
            "roi": "4-5%",
            "property_type": "Detached house"
        },

        # === CRETE (CHANIA AREA) ===
        {
            "title": "2-Bed Detached House - Topolia, Chania, Crete",
            "price": 60000,
            "area_sqm": 70,
            "bedrooms": 2,
            "url": "https://www.rightmove.co.uk/properties/159737804#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/a2b84270d/159737804/a2b84270d253ce62ea8aecae2c83f063_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "crete",
            "features": ["2 bedrooms", "Chania area", "Mountain village", "Character property"],
            "roi": "3-5%",
            "property_type": "Detached house"
        },

        # === NORTHERN GREECE (DRAMA & SERRES) ===
        {
            "title": "Studio Flat - Drama City Centre",
            "price": 56000,
            "area_sqm": 40,
            "bedrooms": 0,
            "url": "https://www.rightmove.co.uk/properties/162955775#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/793fe631c/162955775/793fe631cab7895c47f2ceebada11d35_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "northern_greece",
            "features": ["City centre", "Studio", "Ready to rent", "Lowest entry price"],
            "roi": "5-7%",
            "property_type": "Studio flat"
        },
        {
            "title": "2-Bed Detached House - Efkarpia, Serres",
            "price": 57000,
            "area_sqm": 85,
            "bedrooms": 2,
            "url": "https://www.rightmove.co.uk/properties/166495556#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/88e10b9f3/166495556/88e10b9f3311b29c12fc0c634fbe0f1b_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "northern_greece",
            "features": ["2 bedrooms", "Detached", "85m²", "Serres area"],
            "roi": "5-6%",
            "property_type": "Detached house"
        },
        {
            "title": "5-Bed Detached House - Chryso, Serres",
            "price": 57000,
            "area_sqm": 120,
            "bedrooms": 5,
            "url": "https://www.rightmove.co.uk/properties/169430747#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/4c5da3c84/169430747/4c5da3c841ead16360bc9541203fad0b_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "northern_greece",
            "features": ["5 bedrooms", "120m²", "Large family home", "Incredible value"],
            "roi": "5-7%",
            "property_type": "Detached house"
        },
        {
            "title": "Studio Flat - Serres City",
            "price": 58000,
            "area_sqm": 38,
            "bedrooms": 0,
            "url": "https://www.rightmove.co.uk/properties/170088143#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/705ae7346/170088143/705ae7346705e8d66d72ed72f1d04ed9_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "northern_greece",
            "features": ["City location", "Studio flat", "Rental ready"],
            "roi": "5-7%",
            "property_type": "Studio flat"
        },
        {
            "title": "2-Bed Flat - Drama City",
            "price": 70000,
            "area_sqm": 65,
            "bedrooms": 2,
            "url": "https://www.rightmove.co.uk/properties/169011563#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/b8e9e150e/169011563/b8e9e150e454d86cf1bab5110e7d7ae4_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "northern_greece",
            "features": ["2 bedrooms", "City apartment", "Ready to move in"],
            "roi": "5-6%",
            "property_type": "Flat"
        },
        {
            "title": "2-Bed Detached House - Adriani, Drama",
            "price": 70000,
            "area_sqm": 80,
            "bedrooms": 2,
            "url": "https://www.rightmove.co.uk/properties/159071498#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/443ad7c8a/159071498/443ad7c8a30b49564efaf26ffc4464c7_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "northern_greece",
            "features": ["2 bedrooms", "Detached", "80m²", "Village setting"],
            "roi": "5-6%",
            "property_type": "Detached house"
        },
        {
            "title": "4-Bed Detached House - Rodolivos, Serres",
            "price": 70000,
            "area_sqm": 130,
            "bedrooms": 4,
            "url": "https://www.rightmove.co.uk/properties/169742507#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/3633cb896/169742507/3633cb89629d936b52fb63a8b6e2b50e_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "northern_greece",
            "features": ["4 bedrooms", "130m²", "Large family home"],
            "roi": "5-6%",
            "property_type": "Detached house"
        },

        # === PELION & SPORADES ===
        {
            "title": "2-Bed Property - Alonnisos Island",
            "price": 60000,
            "area_sqm": 55,
            "bedrooms": 2,
            "url": "https://www.rightmove.co.uk/properties/169527362#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/ada9f3d64/169527362/ada9f3d641dc27ff3d07974a56d7e5d3_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "pelion_sporades",
            "features": ["Island living", "2 bedrooms", "Marine park island", "Reduced price"],
            "roi": "4-5% (seasonal)",
            "property_type": "Property"
        },
        {
            "title": "Detached House - Portaria, Pelion",
            "price": 70000,
            "area_sqm": 75,
            "bedrooms": None,
            "url": "https://www.rightmove.co.uk/properties/172463645#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/6331d4b20/172463645/6331d4b209afdc646bc0370a530a2c1f_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "pelion_sporades",
            "features": ["Pelion mountain village", "Near beaches", "Character property"],
            "roi": "4-5%",
            "property_type": "Detached house"
        },

        # === ATTICA / ATHENS ===
        {
            "title": "2-Bed Flat - Zografos, Athens (University area)",
            "price": 73000,
            "area_sqm": 65,
            "bedrooms": 2,
            "url": "https://www.rightmove.co.uk/properties/172039565#/?channel=OVERSEAS",
            "image_url": "https://media.rightmove.co.uk/dir/crop/10:9-16:9/property-photo/db7d7fd42/172039565/db7d7fd420cb1ededdddb6734a54cc59_max_476x317.jpeg",
            "source": "Rightmove",
            "region": "attica",
            "features": ["Athens location", "2 bedrooms", "Near university", "Strong rental demand"],
            "roi": "5-6%",
            "property_type": "Flat"
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

    # Filter: budget properties under 100k CAD (≈€65-75k EUR with buffer)
    investment_properties = [
        p for p in all_properties
        if p.get("price") and p["price"] <= 75000
    ]

    print(f"\nTotal unique properties: {len(all_properties)}")
    print(f"Budget properties (<=€75k / ~100k CAD): {len(investment_properties)}")

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
            "budget": "100,000 CAD ≈ €65,000 EUR (Feb 2026 rate)",
            "budget_note": "At this price point, expect smaller apartments, character houses needing "
                           "renovation, or properties in less touristy areas. Northern Greece "
                           "(Drama, Serres) offers the best value per square meter.",
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
