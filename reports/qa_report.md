# Data quality assurance report

Generated automatically by `src/quality_checks.py`.

## Rainfall

| Check | Result |
|---|---|
| raw rows | 70152 |
| duplicate timestamps removed | 0 |
| expected 15 minute steps | 70176 |
| steps absent from the download | 24 |
| quality flag: Unchecked | 36766 |
| quality flag: Good | 24508 |
| quality flag: Suspect | 8878 |
| quality flag: Absent | 24 |
| negative values removed | 0 |
| values above 25.0 mm in 15 min removed | 0 |
| usable steps (%) | 87.31 |
| total rainfall in usable data (mm) | 1084.2 |

## River

| Check | Result |
|---|---|
| raw rows | 70176 |
| duplicate timestamps removed | 0 |
| expected 15 minute steps | 70176 |
| steps absent from the download | 0 |
| quality flag: Good | 61996 |
| quality flag: Suspect | 8180 |
| spikes removed | 171 |
| flat line periods of 24 h or more (flagged, kept) | 77 |
| short gaps filled (up to 4 steps) | 478 |
| usable steps (%) | 88.78 |
