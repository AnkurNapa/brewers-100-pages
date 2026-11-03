# The Money in the Tank: companion files

Data, notebooks and a workbook for *The Money in the Tank: Brewery Losses in Rupees, Dollars and Euros*, part of The Brewer's 100 Pages. Every file runs on Kestrel Brewing, the synthetic plant used throughout the book. The numbers the book prints come out of these files; `check_numbers.py` proves it.

Copyright 2026 Ankur Napa. All rights reserved. You may use these files for your own learning; do not republish or redistribute them. Synthetic data only; no real brewery's numbers.

## How to run

```
pip install -r requirements.txt
python3 make_data.py          # writes every CSV in data/ from fixed seeds
python3 check_numbers.py      # asserts the book's numbers come out of the data
python3 sheets/make_workbook.py
```

Open the notebooks in Jupyter from the `notebooks` folder; they read `../data/`. Load your own rows into the same columns and each notebook runs unchanged. Point them at real plant data only after your IT team agrees what may leave the site (chapter 14.4).

## Chapter by chapter

| Chapter | File | What it does |
|---|---|---|
| 3 | `notebooks/ch03-mass-balance.ipynb` | Builds the stage table from the minimum dataset and flags any stage where the balance does not close |
| 4 | `data/minimum_dataset.csv` | One row per batch per stage for one quarter: 45 fills, 26,100 hL cast |
| 5 | `notebooks/ch05-extract-loss.ipynb` | Reads 60 brews, splits conversion from lauter and draws Figure 5.2 |
| 6 | `notebooks/ch06-cellar-loss.ipynb` | Builds the quarter vessel table and Figure 6.1 |
| 7 | `notebooks/ch07-giveaway.ipynb` | Reads a week of fill weights, plots mean and spread by shift and prices the giveaway |
| 8 | `notebooks/ch08-cod-spikes.ipynb` | Turns a daily COD series into spike days and the beer each implies |
| 9 | `notebooks/ch09-tank-days.ipynb` | Finds overlapping tank intervals and prints contribution per tank day |
| 10 | `notebooks/ch10-true-cogs.ipynb` | Reads the March volumes by brand and pack with the cost ledger and draws the brand by pack grid |
| 11 | `notebooks/ch11-loss-ledger.ipynb` | Builds the ledger and both waterfalls and flags any row without a sum |
| 12 | `notebooks/ch12-fix-ranking.ipynb` | Ranks the fixes, reruns the order when a probability changes and draws the effort map |
| 13 | `notebooks/ch13-shocks.ipynb` | Rebuilds the shock table and draws both figures |
| Appendix C | `sheets/kestrel-loss-workbook.xlsx` | The shared workbook, sheet by sheet, with live formulas |

## Data files

| File | Rows | Used in |
|---|---|---|
| `minimum_dataset.csv` | 312 | Chapters 3, 4, 6, 11 and the workbook |
| `brewhouse_brews.csv` | 60 | Chapter 5 |
| `fill_weights.csv` | 840 | Chapter 7 |
| `effluent_daily.csv` | 90 | Chapter 8 |
| `tank_occupancy.csv`, `beers.csv` | 175, 3 | Chapter 9 |
| `cost_ledger_march.csv`, `march_brands.csv`, `march_brand_pack.csv` | 8, 2, 3 | Chapter 10 |
| `loss_drivers.csv` | 9 | Chapter 11 |
| `fixes.csv` | 6 | Chapter 12 |
| `shock_inputs.csv`, `shock_scenarios.csv` | 5, 3 | Chapter 13 |

In the minimum dataset a month is the beer cast that month, followed to dispatch. `batch_id` is the fermenter fill; `brew_id` keeps each brew as a parent key (two brews in a fill are joined with a bar). Kestrel uses unitanks, so the heel left when a tank is emptied sits in `heel_hl` on the conditioning row. The transfer loss is the gap between the conditioning row's `volume_out_hl` and the filter row's `volume_in_hl`.

Money is in US dollars at Kestrel's synthetic costs. Book rates, not market rates: USD 1 = INR 90; EUR 1 = USD 1.10. INR figures use western digit grouping, as the book does.
