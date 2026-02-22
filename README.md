# Greek Property Finder 🏖️🇬🇷

Investment property finder for Greece — targeting coastal properties near decent-sized cities.  
Built for a Canadian/Estonian (EU citizen) exploring Greek real estate opportunities.

## Live Site

👉 **[View the property comparison site](https://matisaar.github.io/greek-property-finder/)**

## What This Does

1. **Scrapes** Greek real estate portals (Tranio, Rightmove, etc.) for investment properties  
2. **Curates** verified listings across 9 Greek coastal/city regions  
3. **Generates** a static comparison website with:
   - Interactive property cards with photos and clickable links
   - Filter by region, price, bedrooms
   - Side-by-side comparison table
   - Market data & investment context
   - Direct links to search portals yourself
   - Prices in both EUR and CAD

## Target Regions

| Region | Why? |
|--------|------|
| Thessaloniki & Halkidiki | 2nd biggest city, world-class beaches 30 min away |
| Chania, Crete | Stunning Venetian harbor, Europe's best beaches |
| Heraklion, Crete | Largest Cretan city, strong tourism |
| Kalamata | Emerging gem, beautiful coast, direct flights |
| Volos & Pelion | Half-mountain half-beach, undervalued |
| Kavala | Northern charm, very affordable |
| Patras | 3rd largest city, port city, student demand |
| Piraeus/Athens | Capital area, strong infrastructure |

## Usage

```bash
pip install -r requirements.txt
python scraper.py           # Scrape & collect data → data/properties.json
python generate_site.py     # Generate HTML site → docs/index.html
```

## EU Citizen Advantage

With an Estonian passport (EU citizen), you can buy property in Greece with **zero restrictions** — identical rights to Greek citizens. No Golden Visa needed.

## Disclaimer

For informational purposes only. Always verify listings directly with agents and conduct proper due diligence. Consult a Greek lawyer and tax advisor before any purchase.
