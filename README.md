# Rainfall Event Analysis for the River Hull Catchment

Status: work in progress (October 2026)

## Question

How does the river respond to individual rainfall events, and how do rainfall depth, intensity, season and antecedent wetness change that response?

## Data

Open 15 minute rainfall and river data from the Environment Agency [Hydrology API](https://environment.data.gov.uk/hydrology/doc/reference), published under the Open Government Licence v3.0. Raw data is downloaded by script and is not stored in this repository.

## Pipeline

| Stage | Script | What it does |
|---|---|---|
| 0 | `src/find_stations.py` | Lists rainfall and river stations near the study area |
| 2 | `src/download_data.py` | Downloads the chosen 15 minute series, one year at a time |
| 3 | `src/quality_checks.py` | Removes duplicates, regularises to a 15 minute grid, applies EA quality flags, removes impossible values and spikes, flags flat lines, fills only short gaps, writes `reports/qa_report.md` |
| 4 | `src/events.py` | Separates rainfall into events using a minimum dry gap and minimum depth |
| 5 | `src/event_stats.py` | Measures each event's river response: baseline, peak, rise and lag time |
| 6 | `src/make_figures.py` | Produces figures and `reports/summary.md` |

All settings (stations, dates, thresholds) live in `src/config.py`.

## How to run

```
pip install -r requirements.txt
python src/find_stations.py
# paste your chosen station ids into src/config.py
python src/run_pipeline.py
```

## Findings

To be added.

## Limitations

To be added.

## Relevance to SuDS monitoring

To be added.
