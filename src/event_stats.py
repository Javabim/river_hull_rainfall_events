"""Stage 5: measure how the river responded to each rainfall event.

For each storm two responses are measured:
  quick response   the highest flow within QUICK_WINDOW_H hours after the rain ends
                   (runoff from nearby surfaces and rain near the channel)
  delayed response the highest flow within RESPONSE_WINDOW_H hours after the rain ends
                   (includes the slower groundwater contribution typical of chalk)
Lag time is only reported for responsive storms, where the quick rise is at least
RESPONSE_THRESHOLD_PCT percent of the starting flow. For storms with no clear response
the "peak" would just be random noise, so a lag time would be meaningless.
"""
import pandas as pd

from config import (PROCESSED, QUICK_WINDOW_H, REPORTS, RESPONSE_THRESHOLD_PCT,
                    RESPONSE_WINDOW_H)
from events import load_clean

SEASONS = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Spring", 4: "Spring", 5: "Spring",
           6: "Summer", 7: "Summer", 8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn"}
HOUR = pd.Timedelta(hours=1)


def load_events():
    events = pd.read_csv(PROCESSED / "events.csv")
    for col in ("start", "end", "peak_rain_time", "rain_centroid"):
        events[col] = pd.to_datetime(events[col], utc=True, format="ISO8601")
    return events


def window_end(event, hours, next_start):
    end = event["end"] + pd.Timedelta(hours=hours)
    return min(end, next_start) if pd.notna(next_start) else end  # stop before the next storm


def river_response(events, river):
    next_starts = events["start"].shift(-1)
    results = []
    for i, event in events.iterrows():
        quick = river[event["start"]:window_end(event, QUICK_WINDOW_H, next_starts[i])]
        full = river[event["start"]:window_end(event, RESPONSE_WINDOW_H, next_starts[i])]
        baseline = river[event["start"] - HOUR:event["start"]].mean()
        complete = full.notna().mean() if len(full) else 0

        result = {"event_id": event["event_id"], "river_complete_pct": round(100 * complete, 1)}
        if complete >= 0.8 and pd.notna(baseline) and baseline > 0 and quick.notna().any():
            peak_time = quick.idxmax()
            rise = quick.max() - baseline
            rise_pct = 100 * rise / baseline
            responsive = rise_pct >= RESPONSE_THRESHOLD_PCT
            result.update({
                "baseline": round(baseline, 4),
                "peak": round(quick.max(), 4),
                "rise": round(rise, 4),
                "rise_pct": round(rise_pct, 1),
                "max_rise_72h": round(full.max() - baseline, 4),
                "max_rise_72h_pct": round(100 * (full.max() - baseline) / baseline, 1),
                "responsive": responsive,
                "peak_time": peak_time if responsive else pd.NaT,
                "lag_from_peak_rain_h":
                    round((peak_time - event["peak_rain_time"]) / HOUR, 2) if responsive else None,
                "lag_from_centroid_h":
                    round((peak_time - event["rain_centroid"]) / HOUR, 2) if responsive else None,
            })
        results.append(result)

    table = events.merge(pd.DataFrame(results), on="event_id")
    table["season"] = table["start"].dt.month.map(SEASONS)
    table["usable"] = table["rise"].notna() & (table["rain_missing_pct"] < 5)
    table["responsive"] = table["responsive"].fillna(False).astype(bool) & table["usable"]
    return table


def main():
    table = river_response(load_events(), load_clean("river"))
    table.to_csv(PROCESSED / "event_table.csv", index=False)
    table.to_csv(REPORTS / "event_table.csv", index=False)
    print(f"{int(table['usable'].sum())} of {len(table)} events usable for analysis")
    print(f"{int(table['responsive'].sum())} of those produced a clear river response "
          f"(rise of {RESPONSE_THRESHOLD_PCT}% or more)")


if __name__ == "__main__":
    main()
