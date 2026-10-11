"""Stage 6: figures and a short written summary of the findings."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LogNorm

from config import (FIGURES, PROCESSED, QUICK_WINDOW_H, RAW, REPORTS,
                    RESPONSE_THRESHOLD_PCT, RESPONSE_WINDOW_H, RIVER_PROPERTY)
from events import load_clean

UNIT = "m³/s" if RIVER_PROPERTY == "waterFlow" else "m"
RIVER_LABEL = f"River flow ({UNIT})" if RIVER_PROPERTY == "waterFlow" else f"River level ({UNIT})"
SEASON_ORDER = ["Autumn", "Winter", "Spring", "Summer"]


def load_table():
    table = pd.read_csv(PROCESSED / "event_table.csv")
    for col in ("start", "end", "peak_rain_time", "peak_time"):
        table[col] = pd.to_datetime(table[col], utc=True, format="ISO8601")
    table["responsive"] = table["responsive"].astype(str).str.lower() == "true"
    table["usable"] = table["usable"].astype(str).str.lower() == "true"
    return table


def seasons_present(table):
    return [s for s in SEASON_ORDER if s in set(table["season"])]


def plot_top_events(table, rain, river, n=5):
    top = table.nlargest(n, "depth_mm")
    fig, axes = plt.subplots(len(top), 1, figsize=(10, 3 * len(top)))
    if len(top) == 1:
        axes = [axes]
    for ax, (_, e) in zip(axes, top.iterrows()):
        t0 = e["start"] - pd.Timedelta(hours=12)
        t1 = e["end"] + pd.Timedelta(hours=RESPONSE_WINDOW_H)
        q = river[t0:t1]
        ax.plot(q.index, q.values, color="tab:blue")
        ax.axvspan(e["end"], e["end"] + pd.Timedelta(hours=QUICK_WINDOW_H),
                   color="tab:orange", alpha=0.08)
        if e["responsive"]:
            ax.axvline(e["peak_time"], color="tab:orange", linestyle=":", linewidth=1.5)
            response = f"quick rise {e['rise_pct']:.0f}%, lag {e['lag_from_peak_rain_h']:.1f} h"
        else:
            response = "no clear quick response"
        ax.set_ylabel(RIVER_LABEL)

        ax_rain = ax.twinx()
        r = rain[t0:t1]
        ax_rain.bar(r.index, r.values, width=pd.Timedelta(minutes=15), color="tab:grey")
        ax_rain.set_ylim(max(r.max() * 3, 1), 0)
        ax_rain.set_ylabel("Rain (mm per 15 min)")
        ax.set_title(f"Event {e['event_id']}: {e['start']:%d %b %Y}, {e['depth_mm']:.1f} mm, {response}")
    fig.text(0.01, 0.002, f"Shaded band: {QUICK_WINDOW_H} h window used for the quick response. "
             "Dotted line: quick peak.", fontsize=8)
    fig.tight_layout(rect=(0, 0.01, 1, 1))
    fig.savefig(FIGURES / "fig1_largest_events.png", dpi=150)
    plt.close(fig)


def plot_depth_vs_rise(table):
    fig, ax = plt.subplots(figsize=(7.5, 5))
    points = ax.scatter(table["depth_mm"], table["rise_pct"], c=table["baseline"],
                        norm=LogNorm(), cmap="viridis", s=30)
    fig.colorbar(points, label=f"Flow before the storm ({UNIT}, log scale)")
    ax.axhline(RESPONSE_THRESHOLD_PCT, color="grey", linestyle="--", linewidth=1)
    ax.text(ax.get_xlim()[1], RESPONSE_THRESHOLD_PCT, " responsive threshold",
            va="bottom", ha="right", fontsize=8, color="grey")
    ax.set_xlabel("Event rainfall depth (mm)")
    ax.set_ylabel("Quick rise in flow (% of flow before the storm)")
    ax.set_title("River response by storm size and catchment wetness")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig2_depth_vs_rise.png", dpi=150)
    plt.close(fig)


def plot_by_season(table):
    seasons = seasons_present(table)
    responsive = table[table["responsive"]]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].boxplot([table.loc[table["season"] == s, "rise_pct"].dropna() for s in seasons])
    axes[0].set_ylabel("Quick rise (% of flow before the storm)")
    axes[0].set_title("Size of response by season (all usable storms)")
    axes[1].boxplot([responsive.loc[responsive["season"] == s, "lag_from_peak_rain_h"].dropna()
                     for s in seasons])
    axes[1].set_ylabel("Lag from peak rain to quick peak (h)")
    axes[1].set_title("Lag time by season (responsive storms only)")
    for ax in axes:
        ax.set_xticks(range(1, len(seasons) + 1), seasons)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig3_seasonal_response.png", dpi=150)
    plt.close(fig)


def plot_state_and_response(table, river):
    daily = river.resample("D").mean()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(daily.index, daily.values, color="tab:blue", linewidth=1, label="Daily mean flow")
    usable = table[table["usable"]]
    flow_at_start = usable["baseline"]
    resp = usable["responsive"]
    ax.scatter(usable.loc[resp, "start"], flow_at_start[resp], color="tab:orange", s=30,
               zorder=3, label="Storm with clear response")
    ax.scatter(usable.loc[~resp, "start"], flow_at_start[~resp], facecolors="none",
               edgecolors="grey", s=30, zorder=3, label="Storm with no clear response")
    ax.set_yscale("log")
    ax.set_ylabel(f"{RIVER_LABEL}, log scale")
    ax.set_title("Catchment state through the year and which storms produced a response")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "fig4_state_and_response.png", dpi=150)
    plt.close(fig)


def write_summary(table):
    usable = table[table["usable"]]
    responsive = usable[usable["responsive"]]
    meta = json.loads((RAW / "metadata.json").read_text()) if (RAW / "metadata.json").exists() else {}

    factors = {
        "Event rainfall depth": "depth_mm",
        "Peak rainfall intensity": "peak_intensity_mm_h",
        "Rain in previous 7 days": "antecedent_7d_rain_mm",
        "Flow before the storm": "baseline",
    }
    corr_rows = [f"| {label} | {usable[col].corr(usable['rise_pct'], method='spearman'):.2f} |"
                 for label, col in factors.items()]

    seasons = seasons_present(usable)
    season_rows = []
    for s in seasons:
        all_s, resp_s = usable[usable["season"] == s], responsive[responsive["season"] == s]
        season_rows.append(
            f"| {s} | {len(all_s)} | {len(resp_s)} ({100 * len(resp_s) / len(all_s):.0f}%) | "
            f"{all_s['baseline'].median():.3f} | {all_s['rise_pct'].median():.1f} | "
            f"{resp_s['lag_from_peak_rain_h'].median():.1f} |"
        )

    lines = [
        "# Results summary", "",
        "Generated automatically by `src/make_figures.py`.", "",
        f"Rainfall series: `{meta.get('rainfall', {}).get('measure', 'n/a')}`  ",
        f"River series: `{meta.get('river', {}).get('measure', 'n/a')}`", "",
        f"Storms found: {len(table)}. Usable: {len(usable)}. "
        f"Clear quick response (rise of {RESPONSE_THRESHOLD_PCT}% or more): {len(responsive)}.", "",
        f"Median storm depth: {usable['depth_mm'].median():.1f} mm  ",
        f"Median lag from peak rain to quick peak (responsive storms): "
        f"{responsive['lag_from_peak_rain_h'].median():.1f} h", "",
        "## What controls the size of the response?", "",
        "Spearman correlation with the quick rise in flow (% of flow before the storm), all usable storms.", "",
        "| Factor | Spearman rho |", "|---|---|", *corr_rows, "",
        "## By season", "",
        f"| Season | Usable storms | Responsive storms | Median flow before storm ({UNIT}) "
        "| Median quick rise (%) | Median lag, responsive storms (h) |",
        "|---|---|---|---|---|---|", *season_rows, "",
    ]
    (REPORTS / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    table = load_table()
    rain, river = load_clean("rainfall"), load_clean("river")
    usable = table[table["usable"]]
    plot_top_events(usable, rain, river)
    plot_depth_vs_rise(usable)
    plot_by_season(usable)
    plot_state_and_response(table, river)
    write_summary(table)
    print("Figures saved in figures/, summary in reports/summary.md")


if __name__ == "__main__":
    main()
