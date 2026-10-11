"""Stage 4: separate the rainfall record into individual events.

A new event starts whenever there has been no rain for at least MIN_DRY_GAP_H hours.
Events with less than MIN_EVENT_DEPTH_MM of rain are discarded.
"""
import pandas as pd

from config import MIN_DRY_GAP_H, MIN_EVENT_DEPTH_MM, PROCESSED

STEP = pd.Timedelta(minutes=15)


def load_clean(name):
    df = pd.read_csv(PROCESSED / f"{name}_clean.csv", parse_dates=["dateTime"])
    df["dateTime"] = pd.to_datetime(df["dateTime"], utc=True)
    return df.set_index("dateTime")["value"]


def separate_events(rain, min_dry_gap_h=MIN_DRY_GAP_H, min_depth_mm=MIN_EVENT_DEPTH_MM):
    wet = rain[rain > 0]
    gaps = wet.index.to_series().diff() > pd.Timedelta(hours=min_dry_gap_h)
    group = gaps.cumsum().to_numpy()

    rows = []
    previous_end = None
    for _, block in wet.groupby(group):
        start, end = block.index[0], block.index[-1] + STEP
        dry_before_h = None if previous_end is None else (start - previous_end) / pd.Timedelta(hours=1)
        previous_end = end

        depth = float(block.sum())
        if depth < min_depth_mm:
            continue

        window = rain[start:end - STEP]
        weights = block / depth
        centroid = block.index[0] + ((block.index - block.index[0]) * weights.to_numpy()).sum()
        rows.append({
            "start": start,
            "end": end,
            "depth_mm": round(depth, 2),
            "duration_h": (end - start) / pd.Timedelta(hours=1),
            "peak_intensity_mm_h": round(float(block.max()) * 4, 2),
            "peak_rain_time": block.idxmax(),
            "rain_centroid": centroid.round("min"),
            "antecedent_dry_h": None if dry_before_h is None else round(dry_before_h, 2),
            "antecedent_7d_rain_mm": round(float(rain[start - pd.Timedelta(days=7):start - STEP].sum()), 2),
            "rain_missing_pct": round(100 * window.isna().mean(), 1),
        })

    events = pd.DataFrame(rows)
    events.insert(0, "event_id", range(1, len(events) + 1))
    return events


def main():
    events = separate_events(load_clean("rainfall"))
    events.to_csv(PROCESSED / "events.csv", index=False)
    print(f"{len(events)} rainfall events found")


if __name__ == "__main__":
    main()
