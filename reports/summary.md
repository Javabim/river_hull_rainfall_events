# Results summary

Generated automatically by `src/make_figures.py`.

Rainfall series: `7ec3f61f-e348-4dfe-a001-35593471d690-rainfall-t-900-mm-qualified`  
River series: `a18743e3-9809-4f93-b046-79977b9707d3-flow-i-900-m3s-qualified`

Storms found: 130. Usable: 109. Clear quick response (rise of 5% or more): 42.

Median storm depth: 4.2 mm  
Median lag from peak rain to quick peak (responsive storms): 2.5 h

## What controls the size of the response?

Spearman correlation with the quick rise in flow (% of flow before the storm), all usable storms.

| Factor | Spearman rho |
|---|---|
| Event rainfall depth | 0.49 |
| Peak rainfall intensity | 0.33 |
| Rain in previous 7 days | 0.23 |
| Flow before the storm | -0.24 |

## By season

| Season | Usable storms | Responsive storms | Median flow before storm (m³/s) | Median quick rise (%) | Median lag, responsive storms (h) |
|---|---|---|---|---|---|
| Autumn | 34 | 25 (74%) | 0.088 | 10.9 | 3.8 |
| Winter | 22 | 8 (36%) | 1.536 | 3.9 | 2.4 |
| Spring | 24 | 2 (8%) | 1.214 | 2.2 | 4.1 |
| Summer | 29 | 7 (24%) | 0.186 | 1.9 | 0.8 |
