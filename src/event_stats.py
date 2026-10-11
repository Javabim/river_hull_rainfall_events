"""Stage 5: measure how the river responded to each rainfall event."""
import pandas as pd

from config import PROCESSED, REPORTS, RESPONSE_WINDOW_H
from events import load_clean

SEASONS = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
           6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}
HOUR = pd.Timedelta(hours=1)


def load_events():
    events = pd.read_csv(PROCESSED / "events.csv")
    for col in ("start", "end", "peak_rain_time", "rain_centroid"):
        events[col] = pd.to_datetime(events[col], utc=True, format="ISO8601")
    return events


def river_response(events, river, window_h=RESPONSE_WINDOW_H):
    next_start = events["start"].shift(-1)
    results = []
    for i, event in events.iterrows():
        window_end = event["end"] + pd.Timedelta(hours=window_h)
        if pd.notna(next_start[i]):
            window_end = min(window_end, next_start[i])  # stop before the next event begins

        baseline = river[event["start"] - HOUR:event["start"]].mean()
        window = river[event["start"]:window_end]
        complete = window.notna().mean() if len(window) else 0

        result = {"event_id": event["event_id"], "river_complete_pct": round(100 * complete, 1)}
        if complete >= 0.8 and pd.notna(baseline):
            peak_time = window.idxmax()
            rise = window.max() - baseline
            result.update({
                "baseline": round(baseline, 3),
                "peak": round(window.max(), 3),
                "rise": round(rise, 3),
                "rise_pct": round(100 * rise / baseline, 1) if baseline > 0 else None,
                "peak_time": peak_time,
                "lag_from_peak_rain_h": round((peak_time - event["peak_rain_time"]) / HOUR, 2),
                "lag_from_centroid_h": round((peak_time - event["rain_centroid"]) / HOUR, 2),
            })
        results.append(result)

    table = events.merge(pd.DataFrame(results), on="event_id")
    table["season"] = table["start"].dt.month.map(SEASONS)
    table["usable"] = table["rise"].notna() & (table["rain_missing_pct"] < 5)
    return table


def main():
    table = river_response(load_events(), load_clean("river"))
    table.to_csv(PROCESSED / "event_table.csv", index=False)
    table.to_csv(REPORTS / "event_table.csv", index=False)
    print(f"{int(table['usable'].sum())} of {len(table)} events usable for analysis")


if __name__ == "__main__":
    main()
