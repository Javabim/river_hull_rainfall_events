# Rainfall Event Analysis for the River Hull Catchment

Status: work in progress (October 2026)

## Question

How does the River Hull respond to individual rainfall events, and how do rainfall depth, season and antecedent wetness change that response?

## Data

Open rainfall and river data from the Environment Agency Hydrology Data Explorer, at 15 minute resolution. Raw data is downloaded by script and is not stored in this repository.

## Pipeline

1. Data acquisition (`src/download_data.py`)
2. Quality assurance: gaps, quality flags, spikes, flat lines, timestamp alignment (`src/quality_checks.py`)
3. Rainfall event separation using a minimum dry gap and minimum event depth (`src/events.py`)
4. Event statistics: depth, duration, peak intensity, antecedent dry period, peak river response, lag time (`src/event_stats.py`)
5. Analysis and figures (`notebooks/`)

## Findings

To be added.

## Limitations

To be added.

## Relevance to SuDS monitoring

To be added.

## How to run

```
pip install -r requirements.txt
python src/download_data.py
```
