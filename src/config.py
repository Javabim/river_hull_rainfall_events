"""Project settings. Edit this file, then run the pipeline.

Step 1: run  python src/find_stations.py  to list nearby stations.
Step 2: paste the station IDs you choose into RAIN_STATION and RIVER_STATION below.
"""
from pathlib import Path

# Where to search for stations (default: middle of the River Hull catchment, near Beverley)
CENTRE_LAT = 53.90
CENTRE_LONG = -0.42
SEARCH_RADIUS_KM = 20

# Station IDs (the "id" column printed by find_stations.py)
RAIN_STATION = "7ec3f61f-e348-4dfe-a001-35593471d690"
RIVER_STATION = "a18743e3-9809-4f93-b046-79977b9707d3"

# "waterFlow" if the river station measures flow, otherwise "waterLevel"
RIVER_PROPERTY = "waterFlow"

# Study period: two hydrological years (UK water years run October to September)
START_DATE = "2023-10-01"
END_DATE = "2025-10-01"

# Event separation settings
MIN_DRY_GAP_H = 6          # hours without rain that separate two events
MIN_EVENT_DEPTH_MM = 2.0   # events smaller than this are ignored
RESPONSE_WINDOW_H = 72     # hours after an event in which to look for the river peak

# Quality assurance settings
RAIN_MAX_15MIN_MM = 25.0   # 15 minute totals above this are treated as implausible
RIVER_GAP_FILL_STEPS = 4   # river gaps up to 4 steps (1 hour) are filled by interpolation
FLATLINE_HOURS = 24        # identical river readings for this long are flagged

# Folders
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"
REPORTS = ROOT / "reports"
for folder in (RAW, PROCESSED, FIGURES, REPORTS):
    folder.mkdir(parents=True, exist_ok=True)
