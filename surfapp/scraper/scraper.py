"""
Daily NOAA buoy scraper.
Pulls the latest observation for each station, posts it to the backend API,
and relies on the backend to maintain the 7-day rolling window.

Stations scraped:
  46225 — Torrey Pines, San Diego
  46254 — San Diego offshore

NDBC realtime2 format (space-separated, first two rows are headers):
  #YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS  PTDY  TIDE
  #yr  mo dy hr mn degT m/s  m/s     m   sec   sec degT   hPa  degC  degC  degC   mi  hPa    ft
  2024 03 15 12 00  270  5.1  6.2  1.52   9.0   7.3 280 1015.2  14.3  15.8  11.2   MM    MM    MM

Columns we care about:
  WVHT  — wave height (m)
  DPD   — dominant wave period (sec)
  MWD   — mean wave direction (degrees)
  WTMP  — water temperature (°C)
"""

import logging
import os
import sys
from datetime import date

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

BACKEND_URL = os.environ["BACKEND_URL"].rstrip("/")
ADMIN_KEY   = os.environ["ADMIN_API_KEY"]

STATIONS = os.environ.get("BUOY_STATIONS", "46225,46254").split(",")

NDBC_URL = "https://www.ndbc.noaa.gov/data/realtime2/{station}.txt"

HEADERS = {"X-Admin-Key": ADMIN_KEY}


def fetch_latest(station_id: str) -> dict | None:
    url = NDBC_URL.format(station=station_id)
    log.info("Fetching %s", url)

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    lines = resp.text.splitlines()

    # Skip the two header rows (start with #)
    data_lines = [l for l in lines if not l.startswith("#") and l.strip()]
    if not data_lines:
        log.warning("No data lines for station %s", station_id)
        return None

    # Most recent reading is the first data line
    parts = data_lines[0].split()
    if len(parts) < 15:
        log.warning("Unexpected line format for station %s: %s", station_id, data_lines[0])
        return None

    def parse(val):
        return None if val in ("MM", "99", "999", "9999") else float(val)

    return {
        "station_id":     station_id,
        "date":           date.today().isoformat(),
        "wave_height":    parse(parts[8]),   # WVHT
        "wave_period":    parse(parts[9]),   # DPD
        "wave_direction": parse(parts[11]),  # MWD
        "water_temp":     parse(parts[14]),  # WTMP
    }


def post_reading(reading: dict) -> None:
    url = f"{BACKEND_URL}/admin/buoy-data"
    resp = requests.post(url, json=reading, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    log.info("Posted station_id=%s date=%s", reading["station_id"], reading["date"])


def main():
    errors = []
    for station in STATIONS:
        station = station.strip()
        try:
            reading = fetch_latest(station)
            if reading:
                post_reading(reading)
        except Exception as e:
            log.error("Failed for station %s: %s", station, e)
            errors.append(station)

    if errors:
        log.error("Scraper finished with errors for stations: %s", errors)
        sys.exit(1)

    log.info("Scraper finished successfully for %d stations", len(STATIONS))


if __name__ == "__main__":
    main()
