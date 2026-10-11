"""Stage 6: figures and a short written summary of the findings."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import FIGURES, PROCESSED, RAW, REPORTS, RESPONSE_WINDOW_H, RIVER_PROPERTY
from events import load_clean

RIVER_LABEL = "River flow (m³/s)" if RIVER_PROPERTY == "waterFlow" else "River level (m)"
SEASON_ORDER = ["Autumn", "Winter", "Spring", "Summer"]


def load_table():
    table = pd.read_csv(PROCESSED / "event_table.csv")
    for col in ("start", "end", "peak_rain_time", "peak_time"):
        table[col] = pd.to_datetime(table[col], utc=True, format="ISO8601")
    return table[table["usable"]]


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
        ax.axvline(e["peak_time"], color="tab:blue", linestyle=":", linewidth=1)
        ax.set_ylabel(RIVER_LABEL)

        ax_rain = ax.twinx()
        r = rain[t0:t1]
        ax_rain.bar(r.index, r.values, width=pd.Timedelta(minutes=15), color="tab:grey")
        ax_rain.invert_yaxis()
        ax_rain.set_ylim(max(r.max() * 3, 1), 0)
        ax_rain.set_ylabel("Rain (mm per 15 min)")
        ax.set_title(f"Event {e['event_id']}: {e['start']:%d %b %Y}, {e['depth_mm']:.1f} mm, "
                     f"lag {e['lag_from_peak_rain_h']:.1f} h")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig1_largest_events.png", dpi=150)
    plt.close(fig)


def plot_depth_vs_rise(table):
    fig, ax = plt.subplots(figsize=(7, 5))
    points = ax.scatter(table["depth_mm"], table["rise"], c=table["antecedent_7d_rain_mm"],
                        cmap="viridis", s=30)
    fig.colorbar(points, label="Rain in previous 7 days (mm)")
    ax.set_xlabel("Event rainfall depth (mm)")
    ax.set_ylabel(f"Rise in {RIVER_LABEL.lower()}")
    ax.set_title("Bigger and wetter: river response by event depth and antecedent rain")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig2_depth_vs_rise.png", dpi=150)
    plt.close(fig)


def plot_by_season(table):
    seasons = [s for s in SEASON_ORDER if s in set(table["season"])]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, col, label in [(axes[0], "rise", f"Rise in {RIVER_LABEL.lower()}"),
                           (axes[1], "lag_from_peak_rain_h", "Lag time (h)")]:
        ax.boxplot([table.loc[table["season"] == s, col].dropna() for s in seasons])
        ax.set_xticks(range(1, len(seasons) + 1), seasons)
        ax.set_ylabel(label)
    axes[0].set_title("River response by season")
    axes[1].set_title("Lag time by season")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig3_seasonal_response.png", dpi=150)
    plt.close(fig)


def write_summary(table, all_events):
    rho_depth = table["depth_mm"].corr(table["rise"], method="spearman")
    rho_ante = table["antecedent_7d_rain_mm"].corr(table["rise"], method="spearman")
    rho_peak = table["peak_intensity_mm_h"].corr(table["rise"], method="spearman")
    by_season = (table.groupby("season")[["depth_mm", "rise", "lag_from_peak_rain_h"]]
                 .median().reindex([s for s in SEASON_ORDER if s in set(table["season"])]).round(2))
    meta = json.loads((RAW / "metadata.json").read_text()) if (RAW / "metadata.json").exists() else {}

    lines = [
        "# Results summary", "",
        "Generated automatically by `src/make_figures.py`.", "",
        f"Rainfall series: `{meta.get('rainfall', {}).get('measure', 'n/a')}`  ",
        f"River series: `{meta.get('river', {}).get('measure', 'n/a')}`", "",
        f"Events found: {len(all_events)}; usable for analysis: {len(table)}", "",
        f"Median event depth: {table['depth_mm'].median():.1f} mm  ",
        f"Median lag from peak rainfall to river peak: {table['lag_from_peak_rain_h'].median():.1f} h", "",
        "## What drives the size of the river response? (Spearman correlation with rise)", "",
        "| Factor | Spearman ρ |", "|---|---|",
        f"| Event rainfall depth | {rho_depth:.2f} |",
        f"| Peak rainfall intensity | {rho_peak:.2f} |",
        f"| Rain in previous 7 days | {rho_ante:.2f} |", "",
        "## Medians by season", "",
        by_season.to_markdown() if hasattr(by_season, "to_markdown") else by_season.to_string(), "",
    ]
    (REPORTS / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    all_events = pd.read_csv(PROCESSED / "event_table.csv")
    table = load_table()
    rain, river = load_clean("rainfall"), load_clean("river")
    plot_top_events(table, rain, river)
    plot_depth_vs_rise(table)
    plot_by_season(table)
    write_summary(table, all_events)
    print("Figures saved in figures/, summary in reports/summary.md")


if __name__ == "__main__":
    main()
