# One Brewery, One Model: companion files

The data, notebooks and SQL behind *One Brewery, One Model: Data Foundations for Brewers, from Grain Lot to Pallet*.
Every row describes Kestrel Brewing, the synthetic brewery of the series. Nothing here comes from a real plant.

Copyright 2026 Ankur Napa. All rights reserved. You may use these files for your own learning; do not republish or redistribute them. Synthetic data only; no real brewery's numbers.

## Run it

```
pip install -r requirements.txt
python3 make_data.py        # writes every CSV in data/ (fixed seed 26)
python3 check_numbers.py    # asserts the numbers the book prints
python3 pipeline.py         # bronze, silver and gold in out/kestrel.db, run twice, second run changes nothing
```

Open the notebooks from the `notebooks/` folder in Jupyter. Each one adds the companion folder to its path and
imports `kestrel.py`, where the rules shared by several chapters live (gravity and extract, event detection,
the lineage loop, the five checks, the KPI tables).

## The Kestrel slice

Three brew days (12 to 14 March 2026), six brews, six fermenters (FV07 to FV12, three of them filled), three
bright tank fills, two packaging lines (can line C1, bottle line B1), 36 lots and 83 pallets. The year 2026 is
held as stage totals by month in `data/vessel_event_month.csv`; March is the book's typical month.

## Chapter by chapter

| Chapter | File | What it does |
|---|---|---|
| 2 | `notebooks/ch02-batch-count.ipynb` | Counts the six brew week by brew, fill and date code (6, 3, 4); a 12 hour window gives 4 fills |
| 3 | `notebooks/ch03-precedence.ipynb` | Three gravity sources, the precedence table, the 0.0 to 0.2 gap band, efficiency under each source |
| 4 | `notebooks/ch04-tag-events.ipynb` | Cuts the FV07 trace into fill, transfer and CIP events and prints the unmatched one |
| 5 | `notebooks/ch05-sample-joins.ipynb` | The three sample joins (label, vessel and time, vessel and date) and the share matched by each |
| 6 | `notebooks/ch06-planned-actual.ipynb` | Planned against actual per brew and the movements that are missing |
| 7 | `notebooks/ch07-xref.ipynb` | The cross reference table, unmatched codes, the unit factors and the brew day |
| 8 | `notebooks/ch08-model-tables.ipynb` | Loads the 14 tables and runs the bridge share check |
| 9 | `notebooks/ch09-lineage.ipynb`, `sql/` | Forward and backward traces; the CTE on SQLite against the loop in Python |
| 10 | `notebooks/ch10-mass-balance.ipynb` | The stage table, the closure gap per month and the cost per tank day |
| 11 | `notebooks/ch11-dictionary-check.ipynb`, `data/kpi_dictionary.csv` | Fails any entry with a missing field, a blank owner or a name the model lacks |
| 12 | `notebooks/ch12-quality-checks.ipynb` | The five checks and the quarantine table (written to `out/quarantine.csv`) |
| 13 | `notebooks/ch13-silver-vessel-event.ipynb`, `pipeline.py` | `silver_vessel_event`, its quarantine and the run twice proof |
| 14 | `notebooks/ch14-measures.ipynb` | The 20 dictionary measures beside their hand check values |
| 15 | `notebooks/ch15-first-week.ipynb` | Builds the slice through bronze, silver and gold and times the forward trace |

## The SQL

`sql/lineage_forward.sql` and `sql/lineage_forward_loop.sql` are the two queries of chapter 9.5.1 and Appendix C.5,
character for character. `sql/lineage_backward.sql` swaps `from_node` and `to_node` and starts from one can
pallet. `sql/views.sql` builds the `node` and `edge` views of Appendix C.3.

| Engine | Recursive CTE | Tested here |
|---|---|---|
| SQLite | Runs as printed | Yes: 23 pallets at 0.783; backward 0.783 and 0.217 |
| PostgreSQL | Runs as printed | No |
| SQL database in Fabric | Runs with the word RECURSIVE dropped | No |
| Fabric Warehouse, SQL analytics endpoint | Cannot run it; use the WHILE loop | No: SQLite has no `#temp` tables, `DECLARE` or `WHILE` |

The Python loop in `kestrel.trace_loop` follows the WHILE loop one level per pass. The notebook asserts that it
returns the same shares as the CTE.

## Data

`data/` holds the Appendix C tables with their exact column names (`item.csv` to `kpi_dictionary.csv`), the
source extracts named `bronze_<source>_<table>.csv` as chapter 13 names bronze tables and three small inputs:
`vessel_event_month.csv`, `stage_cost.csv` and `drill_log.csv` (blank: QA fills it at each mock recall).
Times end `_utc`. SSCCs use GS1's own example company prefix 0614141, so none belongs to a real company.

## Errata

None yet.
