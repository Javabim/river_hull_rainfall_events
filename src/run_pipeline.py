"""Run the whole pipeline in order.

    python src/run_pipeline.py                 download data, then run every stage
    python src/run_pipeline.py --skip-download reuse the data already in data/raw
"""
import sys

import download_data
import event_stats
import events
import make_figures
import quality_checks

if __name__ == "__main__":
    if "--skip-download" not in sys.argv:
        print("Stage 2: downloading data")
        download_data.main()
    print("Stage 3: quality assurance")
    quality_checks.main()
    print("Stage 4: event separation")
    events.main()
    print("Stage 5: event statistics")
    event_stats.main()
    print("Stage 6: figures and summary")
    make_figures.main()
    print("Done.")
