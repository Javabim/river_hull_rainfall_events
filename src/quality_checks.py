"""Stage 3: quality assurance of the raw time series.

Checks: duplicate timestamps, gaps, Environment Agency quality flags, impossible values,
single point spikes and flat lines. Produces clean series plus a written QA report.
"""
import pandas as pd

from config import (FLATLINE_HOURS, PROCESSED, RAIN_MAX_15MIN_MM, RAW, REPORTS,
                    RIVER_GAP_FILL_STEPS)

STEP = pd.Timedelta(minutes=15)
REJECTED_QUALITY = {"Suspect", "Missing"}


def load_raw(name):
    df = pd.read_csv(RAW / f"{name}.csv")
    df["dateTime"] = pd.to_datetime(df["dateTime"], utc=True)
    return df


def regularise(df, report):
    """Remove duplicates and put the series on a complete 15 minute grid."""
    report["raw rows"] = len(df)
    report["duplicate timestamps removed"] = int(df.duplicated("dateTime").sum())
    df = df.drop_duplicates("dateTime").sort_values("dateTime").set_index("dateTime")

    grid = pd.date_range(df.index.min().floor("15min"), df.index.max().ceil("15min"),
                         freq="15min", tz="UTC")
    df = df.reindex(grid)
    df["quality"] = df["quality"].fillna("Absent")
    report["expected 15 minute steps"] = len(grid)
    report["steps absent from the download"] = int((df["quality"] == "Absent").sum())
    for label, count in df["quality"].value_counts().items():
        report[f"quality flag: {label}"] = int(count)
    return df


def flag_runs(mask):
    """Label consecutive True values so each run can be measured."""
    return (mask != mask.shift()).cumsum()[mask]


def qa_rainfall(df):
    report = {}
    df = regularise(df, report)
    value = df["value"].astype(float)
    flag = pd.Series("ok", index=df.index)

    rejected = df["quality"].isin(REJECTED_QUALITY | {"Absent"})
    flag[rejected] = "rejected_quality"
    negative = value < 0
    flag[negative] = "negative"
    too_high = value > RAIN_MAX_15MIN_MM
    flag[too_high] = "implausible_high"

    value[rejected | negative | too_high] = float("nan")
    report["negative values removed"] = int(negative.sum())
    report[f"values above {RAIN_MAX_15MIN_MM} mm in 15 min removed"] = int(too_high.sum())
    report["usable steps (%)"] = round(100 * value.notna().mean(), 2)
    report["total rainfall in usable data (mm)"] = round(float(value.sum()), 1)
    return pd.DataFrame({"value": value, "flag": flag}), report


def qa_river(df):
    report = {}
    df = regularise(df, report)
    value = df["value"].astype(float)
    flag = pd.Series("ok", index=df.index)

    rejected = df["quality"].isin(REJECTED_QUALITY | {"Absent"})
    flag[rejected] = "rejected_quality"
    value[rejected] = float("nan")

    # Single point spikes: a reading far from the median of its neighbours.
    # Real flood rises build over hours, so they stay close to the rolling median.
    rolling_median = value.rolling(5, center=True, min_periods=3).median()
    step_sd = value.diff().std()
    spike = (value - rolling_median).abs() > 5 * step_sd
    flag[spike] = "spike"
    value[spike] = float("nan")
    report["spikes removed"] = int(spike.sum())

    # Flat lines: identical readings for a long time often mean a stuck sensor.
    same_as_before = value.diff().eq(0)
    runs = flag_runs(same_as_before)
    run_lengths = runs.value_counts()
    long_runs = run_lengths[run_lengths * STEP >= pd.Timedelta(hours=FLATLINE_HOURS)]
    flat = runs.isin(long_runs.index).reindex(value.index, fill_value=False)
    flag[flat] = "flatline_suspected"
    report[f"flat line periods of {FLATLINE_HOURS} h or more (flagged, kept)"] = len(long_runs)

    # Fill short gaps only; longer gaps stay missing so they cannot create false results.
    was_missing = value.isna()
    value = value.interpolate(limit=RIVER_GAP_FILL_STEPS, limit_area="inside")
    filled = was_missing & value.notna()
    flag[filled] = flag[filled] + "_filled"
    report[f"short gaps filled (up to {RIVER_GAP_FILL_STEPS} steps)"] = int(filled.sum())
    report["usable steps (%)"] = round(100 * value.notna().mean(), 2)
    return pd.DataFrame({"value": value, "flag": flag}), report


def write_report(reports):
    lines = ["# Data quality assurance report", "",
             "Generated automatically by `src/quality_checks.py`.", ""]
    for name, report in reports.items():
        lines += [f"## {name.capitalize()}", "", "| Check | Result |", "|---|---|"]
        lines += [f"| {k} | {v} |" for k, v in report.items()]
        lines.append("")
    (REPORTS / "qa_report.md").write_text("\n".join(lines))


def main():
    rain, rain_report = qa_rainfall(load_raw("rainfall"))
    river, river_report = qa_river(load_raw("river"))
    rain.to_csv(PROCESSED / "rainfall_clean.csv", index_label="dateTime")
    river.to_csv(PROCESSED / "river_clean.csv", index_label="dateTime")
    write_report({"rainfall": rain_report, "river": river_report})
    print("QA complete. See reports/qa_report.md")


if __name__ == "__main__":
    main()
