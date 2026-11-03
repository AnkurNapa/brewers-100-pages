# The Lab Knows More Than It Says: companion files

The datasets, notebooks and workbooks that the book says "sit on the companion site". Every number belongs to Kestrel Brewing, an invented plant. No real brewery's figures appear.

## How to run

```
pip install -r requirements.txt
python3 make_data.py        # writes data/ and sheets/ from fixed seeds, about 15 seconds
python3 check_numbers.py    # recomputes every number the book prints from this data
```

Open any notebook in `notebooks/` with Jupyter. Each one reads `../data/`. Each opens with the no code tier as a spreadsheet recipe.

## Chapter by chapter

| Chapter | Notebook | Data | Seed |
|---|---|---|---|
| 1 What the lab throws away | ch01-lab-week | week_*.csv: the synthetic week, 420 samples in five tables | 1103 |
| 2 The instruments and their numbers | ch02-rdf-uncertainty | none: RDF propagation, Figure 2.3, Poisson intervals | 2 (simulation) |
| 3 LIMS basics | ch03-orphans | week_*.csv, with planted orphans | 1103 |
| 4 A clean lab dataset | ch04-ten-checks | ch04_haze_export_raw.csv (63 rows), ch04_planted_faults.csv | 41 |
| 5 Control charts that work | ch05-haze-chart | ch05_haze.csv (120 results) | 5 |
| 6 Small shifts and real margin | ch06-cusum-ewma; sheets/ch06-cusum.xlsx | ch06_ph.csv (150 results) | 9; run test 44 |
| 7 Is the instrument lying? | ch07-instrument-checks; sheets/ch07-gauge-study.xlsx | ch07_checks.csv, ch07_gauge_study.csv | 71; 72 |
| 8 Prediction: soft sensors | ch08-soft-sensor | ch08_fills.csv (300 fills), ch08_do_filler_run.csv | 42 |
| 9 Early warning: micro risk triage | ch09-micro-triage | ch09_micro.csv (14,222 results) | 7 |
| 10 Panel design and statistics | ch10-panel-stats; sheets/ch10-triangle.xlsx | ch10_scores.csv (144 scores) | 1011 |
| 11 The panel as data | ch11-panel-as-data | ch11_tasting_records.csv (400), ch11_lots.csv (50), ch11_spikes.csv, ch11_descriptor_map.csv, ch11_raw_comments.csv | 1102; lots 2081 |
| 12 What AI must never decide | ch12-sop-assistant-score | ch12_sop_testset.csv (10 questions) | none |
| 13 Validation, drift and audit | ch13-validation-drift | ch08_fills.csv, ch13_live_fills.csv (44 live fills) | 42 |
| 14 The first 90 days in the lab | ch14-do-chart | week_*.csv, ch14_do_release.csv (305 results) | 14 |

`ch11_tpo_lots.py` builds the chapter 11 lot set on its own; `make_data.py` imports it.

## What the generators plant

Several sets are built to reproduce the chapter exactly, so they search for a fit from their seed. The haze, pH and lot TPO sets are plain draws. The fills set redraws its 75 test labels until the error table in 8.2.2 comes back. The micro set moves test window positives inside their cell until the top five a day find 94. The scoring panel and the tasting records are fitted to the ANOVA table and the taster offsets. That is why they are teaching sets, not evidence about real beer.

`check_numbers.py` passes when every printed number comes back. It also lists two chapter 13 sums that use no data and round differently from the text.

## Licence

Copyright 2026 Ankur Napa. All rights reserved. You may use these files for your own learning; do not republish or redistribute them. Synthetic data only; no real brewery's numbers.
