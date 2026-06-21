#!/usr/bin/env python3
"""
Fetches daily weather/ET data for the Carbondale (CBL01) CoAgMET station
and maintains a running dataset at data/et_data.json.

Behavior:
- First run (no data file yet): backfills the full history from BACKFILL_START
  through today.
- Subsequent runs: re-fetches a recent window (REFRESH_WINDOW_DAYS) to catch
  any late corrections the station makes to recent days, and merges by date.

Run manually:
    python scripts/scrape_et.py
"""

import json
import os
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

STATION = "cbl01"
BASE_URL = f"https://coagmet.colostate.edu/table/daily/{STATION}"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, "..", "data", "et_data.json")
BACKFILL_START = "2020-01-01"
REFRESH_WINDOW_DAYS = 30

COLUMNS = [
    "date", "avgTemp", "maxTemp", "minTemp", "rhMax", "rhMin",
    "solarRad", "precip", "windRun", "gust", "etr", "pkEt", "eto",
    "soil5cm", "soil15cm",
]


def fetch_range(from_date: str, to_date: str) -> list:
    """Fetch and parse the CoAgMET daily table for a date range."""
    params = {"from": from_date, "to": to_date}
    resp = requests.get(
        BASE_URL,
        params=params,
        timeout=60,
        headers={"User-Agent": "Mozilla/5.0 (personal ET data fetch script)"},
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table")
    if table is None:
        raise RuntimeError(
            "No <table> found on the page. The site layout may have changed - "
            "check coagmet.colostate.edu manually."
        )

    rows = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) != len(COLUMNS):
            continue  # header/footer rows don't have the right cell count
        record = {}
        for col, val in zip(COLUMNS, cells):
            if col == "date":
                m, d, y = val.split("/")
                record[col] = f"{y}-{m}-{d}"
            else:
                cleaned = val.replace(",", "").strip()
                if cleaned in ("", "-", "--", "—"):
                    record[col] = None
                else:
                    try:
                        record[col] = float(cleaned)
                    except ValueError:
                        record[col] = None
        rows.append(record)
    return rows


def load_existing() -> dict:
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH) as f:
            records = json.load(f)
        return {r["date"]: r for r in records}
    return {}


def save(records_by_date: dict):
    records = sorted(records_by_date.values(), key=lambda r: r["date"])
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(records, f, indent=1)
        f.write("\n")


def main():
    existing = load_existing()
    today = date.today()

    if not existing:
        print(f"No existing data file found. Backfilling full history from {BACKFILL_START}...")
        from_date = BACKFILL_START
    else:
        from_date = (today - timedelta(days=REFRESH_WINDOW_DAYS)).isoformat()
        print(f"Found {len(existing)} existing days. Refreshing the last {REFRESH_WINDOW_DAYS} days...")

    to_date = today.isoformat()
    new_rows = fetch_range(from_date, to_date)
    print(f"Fetched {len(new_rows)} rows ({from_date} to {to_date}).")

    added = 0
    changed = 0
    for row in new_rows:
        prior = existing.get(row["date"])
        if prior is None:
            added += 1
        elif prior != row:
            changed += 1
        existing[row["date"]] = row

    save(existing)
    print(f"Done. {added} new day(s), {changed} corrected day(s). Total days stored: {len(existing)}.")


if __name__ == "__main__":
    main()
