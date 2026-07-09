"""
scripts/collect_dataset.py
───────────────────────────
Audits a curated list of websites and exports the results to a CSV
file that will be used to train the carbon prediction model.

Run from the backend/ folder with the venv active:
    python scripts/collect_dataset.py

Output:
    ml/dataset.csv   ← feature matrix + target variable
    ml/raw_audits.csv ← full per-asset breakdown for inspection
"""

import asyncio
import csv
import json
import logging
import os
import sys
from datetime import datetime

# ── Make sure the app package is importable ───────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraper import scrape_page
from app.services.carbon import (
    calculate_co2_grams,
    get_grade_and_score,
    get_asset_status,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
logger = logging.getLogger(__name__)

# ── Curated website list ──────────────────────────────────────────────────────
# Mix of industries, sizes, and expected sustainability grades.
# Add or remove URLs to grow your dataset — aim for 150+ for good model quality.
WEBSITES = [
    # High-traffic / likely heavy
    "https://www.bbc.co.uk",
    "https://www.cnn.com",
    "https://www.theguardian.com",
    "https://www.reddit.com",
    "https://www.ebay.co.uk",
    "https://www.amazon.co.uk",
    "https://www.dailymail.co.uk",
    "https://www.independent.co.uk",
    "https://www.mirror.co.uk",
    "https://www.express.co.uk",
    # Tech companies
    "https://www.github.com",
    "https://www.stackoverflow.com",
    "https://www.mozilla.org",
    "https://www.python.org",
    "https://fastapi.tiangolo.com",
    "https://www.postgresql.org",
    "https://www.linux.org",
    "https://www.debian.org",
    "https://www.ubuntu.com",
    "https://www.raspberrypi.org",
    # Universities (relevant to your project context)
    "https://www.beds.ac.uk",
    "https://www.ox.ac.uk",
    "https://www.cam.ac.uk",
    "https://www.ucl.ac.uk",
    "https://www.imperial.ac.uk",
    "https://www.ed.ac.uk",
    "https://www.manchester.ac.uk",
    "https://www.bristol.ac.uk",
    "https://www.warwick.ac.uk",
    "https://www.leeds.ac.uk",
    # Sustainability / green focused (expected low CO2)
    "https://www.greenpeace.org",
    "https://www.wwf.org.uk",
    "https://www.foe.co.uk",
    "https://www.sustainablewebdesign.org",
    "https://www.thegreenwebfoundation.org",
    "https://www.websitecarbon.com",
    "https://www.carbontrust.com",
    "https://www.clientearth.org",
    "https://www.climatecouncil.org.au",
    "https://www.cooleffect.org",
    # E-commerce (typically heavy)
    "https://www.asos.com",
    "https://www.zara.com",
    "https://www.hm.com",
    "https://www.ikea.com",
    "https://www.argos.co.uk",
    "https://www.currys.co.uk",
    "https://www.johnlewis.com",
    "https://www.next.co.uk",
    "https://www.marksandspencer.com",
    "https://www.dunelm.com",
    # Blogs / minimal sites (expected light)
    "https://www.example.com",
    "https://motherfuckingwebsite.com",
    "https://perfectmotherfuckingwebsite.com",
    "https://txti.es",
    "https://info.cern.ch",
    "https://lite.cnn.com",
    "https://text.npr.org",
    "https://en.m.wikipedia.org/wiki/Main_Page",
    "https://www.iana.org",
    "https://www.w3.org",
    # Government / public sector
    "https://www.gov.uk",
    "https://www.nhs.uk",
    "https://www.parliament.uk",
    "https://www.bbc.co.uk/news",
    "https://www.police.uk",
    "https://www.ofsted.gov.uk",
    "https://www.companies-house.gov.uk",
    "https://www.legislation.gov.uk",
    "https://ec.europa.eu",
    "https://www.un.org",
    # Social / content platforms
    "https://www.wikipedia.org",
    "https://www.medium.com",
    "https://www.substack.com",
    "https://www.devto.com",
    "https://hashnode.com",
    "https://www.producthunt.com",
    "https://www.hacker-news.firebaseapp.com",
    "https://lobste.rs",
    "https://news.ycombinator.com",
    "https://www.indiehackers.com",
]

# ── Feature extraction ────────────────────────────────────────────────────────

def extract_features(url: str, scrape_result: dict) -> dict:
    """
    Convert a raw scrape result into a flat feature dictionary.
    These features become the columns of the training dataset.
    """
    assets = scrape_result.get("assets", [])
    html_size = scrape_result.get("html_size", 0)

    # Separate assets by type
    images  = [a for a in assets if a["asset_type"] == "image"]
    scripts = [a for a in assets if a["asset_type"] == "script"]
    css     = [a for a in assets if a["asset_type"] == "css"]
    fonts   = [a for a in assets if a["asset_type"] == "font"]
    media   = [a for a in assets if a["asset_type"] == "media"]
    other   = [a for a in assets if a["asset_type"] == "other"]

    def total_kb(lst): return sum(a["size_bytes"] for a in lst) / 1024
    def avg_kb(lst):   return (total_kb(lst) / len(lst)) if lst else 0
    def max_kb(lst):   return max((a["size_bytes"] for a in lst), default=0) / 1024

    # Count assets by status for each type
    def count_status(lst, status):
        return sum(1 for a in lst if get_asset_status(a["asset_type"], a["size_bytes"]) == status)

    all_bytes = html_size + sum(a["size_bytes"] for a in assets)
    total_co2 = calculate_co2_grams(all_bytes)
    grade, score = get_grade_and_score(total_co2)

    red_count   = sum(count_status([a], "red")   for a in assets)
    amber_count = sum(count_status([a], "amber") for a in assets)
    green_count = sum(count_status([a], "green") for a in assets)

    return {
        # ── Identity ─────────────────────────────────────────────────────────
        "url":                  url,
        "scraped_at":           datetime.utcnow().isoformat(),

        # ── Page-level features ───────────────────────────────────────────────
        "html_size_kb":         round(html_size / 1024, 2),
        "total_assets":         len(assets),
        "total_size_kb":        round(all_bytes / 1024, 2),

        # ── Asset counts by type ──────────────────────────────────────────────
        "image_count":          len(images),
        "script_count":         len(scripts),
        "css_count":            len(css),
        "font_count":           len(fonts),
        "media_count":          len(media),
        "other_count":          len(other),

        # ── Size features by type (KB) ────────────────────────────────────────
        "image_total_kb":       round(total_kb(images),  2),
        "script_total_kb":      round(total_kb(scripts), 2),
        "css_total_kb":         round(total_kb(css),     2),
        "font_total_kb":        round(total_kb(fonts),   2),
        "media_total_kb":       round(total_kb(media),   2),

        "image_avg_kb":         round(avg_kb(images),  2),
        "script_avg_kb":        round(avg_kb(scripts), 2),
        "css_avg_kb":           round(avg_kb(css),     2),
        "font_avg_kb":          round(avg_kb(fonts),   2),

        "max_single_asset_kb":  round(max_kb(assets), 2),
        "max_image_kb":         round(max_kb(images),  2),
        "max_script_kb":        round(max_kb(scripts), 2),

        # ── Status counts ─────────────────────────────────────────────────────
        "red_asset_count":      red_count,
        "amber_asset_count":    amber_count,
        "green_asset_count":    green_count,

        # ── Ratios (useful for normalised comparisons) ────────────────────────
        "image_pct_of_weight":  round(total_kb(images)  / max(all_bytes / 1024, 1) * 100, 1),
        "script_pct_of_weight": round(total_kb(scripts) / max(all_bytes / 1024, 1) * 100, 1),

        # ── Target variables ──────────────────────────────────────────────────
        "total_co2_grams":      round(total_co2, 6),
        "grade":                grade,
        "score":                score,
    }


# ── Main collection loop ──────────────────────────────────────────────────────

async def collect():
    os.makedirs("ml", exist_ok=True)

    dataset_path   = "ml/dataset.csv"
    raw_audit_path = "ml/raw_audits.jsonl"

    collected = 0
    failed    = 0
    rows      = []

    logger.info("Starting dataset collection for %d websites…", len(WEBSITES))

    for i, url in enumerate(WEBSITES, 1):
        logger.info("[%d/%d] Scraping %s", i, len(WEBSITES), url)
        try:
            result = await scrape_page(url)
            features = extract_features(url, result)
            rows.append(features)
            collected += 1

            # Also save the full raw scrape result as JSONL for inspection
            with open(raw_audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"url": url, "result": result}) + "\n")

            logger.info(
                "    ✓ %d assets  %.2f KB  %.4fg CO₂  Grade: %s",
                result["total_assets_found"],
                features["total_size_kb"],
                features["total_co2_grams"],
                features["grade"],
            )

        except Exception as e:
            logger.warning("    ✗ Failed: %s", e)
            failed += 1

        # Small polite delay between requests
        await asyncio.sleep(1.5)

    # ── Write CSV ──────────────────────────────────────────────────────────────
    if rows:
        fieldnames = list(rows[0].keys())
        with open(dataset_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info("\n════════════════════════════════════")
        logger.info("Collection complete.")
        logger.info("  Successful : %d", collected)
        logger.info("  Failed     : %d", failed)
        logger.info("  Dataset    : %s  (%d rows)", dataset_path, len(rows))
        logger.info("════════════════════════════════════")
    else:
        logger.error("No data collected. Check your internet connection.")


if __name__ == "__main__":
    asyncio.run(collect())
