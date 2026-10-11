"""Stage 2: download 15 minute rainfall and river data from the Environment Agency Hydrology API."""
import io
import json

import pandas as pd
import requests

from config import (END_DATE, RAIN_STATION, RAW, RIVER_PROPERTY, RIVER_STATION,
                    START_DATE)

BASE = "https://environment.data.gov.uk/hydrology"


def find_15min_measure(station, observed_property):
    """Return the id of the 15 minute (900 second) series for a station and property."""
    params = {"station": station, "observedProperty": observed_property}
    response = requests.get(f"{BASE}/id/measures.json", params=params, timeout=60)
    response.raise_for_status()
    measures = [m for m in response.json()["items"] if float(m.get("period", 0) or 0) == 900]
    if not measures:
        raise SystemExit(
            f"No 15 minute {observed_property} series found for station {station}. "
            "Choose another station with find_stations.py."
        )
    qualified = [m for m in measures if "qualified" in m.get("notation", "").lower()]
    chosen = (qualified or measures)[0]
    return chosen.get("notation") or chosen["@id"].rsplit("/", 1)[-1]


def download_readings(measure_id):
    """Download readings one year at a time to keep each request small."""
    start, end = pd.Timestamp(START_DATE), pd.Timestamp(END_DATE)
    years = [start]
    while years[-1] + pd.DateOffset(years=1) < end:
        years.append(years[-1] + pd.DateOffset(years=1))
    years = [d.strftime("%Y-%m-%d") for d in years] + [end.strftime("%Y-%m-%d")]

    chunks = []
    for start, end in zip(years[:-1], years[1:]):
        print(f"  {start} to {end}")
        params = {"mineq-date": start, "max-date": end, "_limit": 500000}
        url = f"{BASE}/id/measures/{measure_id}/readings.csv"
        response = requests.get(url, params=params, timeout=300)
        response.raise_for_status()
        chunks.append(pd.read_csv(io.StringIO(response.text)))
    return pd.concat(chunks, ignore_index=True)


def main():
    if not RAIN_STATION or not RIVER_STATION:
        raise SystemExit("Set RAIN_STATION and RIVER_STATION in src/config.py first.")

    metadata = {}
    for name, station, prop in [
        ("rainfall", RAIN_STATION, "rainfall"),
        ("river", RIVER_STATION, RIVER_PROPERTY),
    ]:
        measure = find_15min_measure(station, prop)
        print(f"Downloading {name}: {measure}")
        readings = download_readings(measure)
        readings.to_csv(RAW / f"{name}.csv", index=False)
        metadata[name] = {"station": station, "measure": measure, "rows": len(readings)}
        print(f"  saved {len(readings)} rows")

    metadata["start_date"], metadata["end_date"] = START_DATE, END_DATE
    metadata["river_property"] = RIVER_PROPERTY
    (RAW / "metadata.json").write_text(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
