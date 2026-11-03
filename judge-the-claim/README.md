# Judge the Claim: companion files

The working files for *Judge the Claim: Buying AI for a Brewery*. Every figure is Kestrel Brewing, the synthetic brewery of the series. No real plant numbers and no vendor names appear.

## How to run it

```
pip install -r requirements.txt
python3 make_data.py
python3 make_sheets.py
python3 check_numbers.py
```

`make_data.py` writes every CSV in `data/` from fixed seeds. `make_sheets.py` writes the three workbooks in `sheets/` with live formulas. `check_numbers.py` asserts the numbers the book prints.

Open the notebooks in Jupyter from the `notebooks/` folder; they read `../data/`.

## Chapter by chapter

| Chapter | File | What it does |
|---|---|---|
| 1 and 2 | `notebooks/ch02-claim-parts.ipynb` | Reads a pasted claim, flags the five words and prints the five part table with "missing" rows |
| 3 | `notebooks/ch03-count-table.ipynb` | The anonymised count table, Figure 3.2 and a place for your own shortlist |
| 4 | `notebooks/ch04-score-sheet.ipynb` | Reads two scorers' points and flags claims whose totals differ by more than one point |
| 4, Appendix A | `sheets/working-score-sheet.xlsx` | The Working Score with the total and the band as formulas |
| 5 | `notebooks/ch05-test-templates.ipynb` | Seeded packs, coded stops, a fifty question set and a held out period |
| 6 | `notebooks/ch06-flag-count.ipynb` | Turns first call answers into a red and green flag count for each vendor |
| 7 | `notebooks/ch07-claim-rebuild.ipynb` | `claim-rebuild`: the sums on the loss CSV, three currencies and the waterfall |
| 7 to 10, Appendix B | `sheets/claim-rebuild-template.xlsx` | Cells B1 to B29 as printed, the check values and the chapter 10 pricing |
| 8 | `notebooks/ch08-scenarios.ipynb` | `scenarios`: the monthly model, payback months, Figures 8.1 and 8.2 plus the 8.5 table |
| 9 | `notebooks/ch09-whole-cost.ipynb` | `whole-cost`: adds the years and the exit |
| 10 | `notebooks/ch10-pricing.ipynb` | Prices one quote fixed and outcome linked; Figure 10.1 |
| 11, Appendix C | `notebooks/ch11-pilot.ipynb`, `sheets/pilot-lines.xlsx` | Break even, kill line, noise margin, pass line and sample size |
| 12 | `notebooks/ch12-decide.ipynb` | Reads the pilot against the lines, simulates how often the rule errs and tracks the two monthly lines |

## The data

| File | What it holds | Seed |
|---|---|---|
| `kestrel_inputs.csv` | The vendor case inputs of Appendix B | fixed |
| `kestrel_monthly_loss.csv` | Twelve months of cellar loss to October 2026: 104,500 hL cast at 2.4 percent | fixed |
| `weekly_loss_sheet.csv` | The same year by week, with the 3.6 percent bad week | 2401 |
| `fill_records.csv` | 144 lager fills on twelve 600 hL fermenters in six matched pairs | 32 |
| `pilot_pair_gaps.csv` | The chapter 12 pilot: 12 pair gaps at the first look then 12 more | 1105 |
| `vendor_counts.csv` | Counts only from the author's review of 116 vendors, 24 September 2026 | none |
| `ch04_scores.csv` | Claims A to C scored by two people | fixed |
| `ch05_*.csv` | The four test templates | 505 |
| `ch06_first_call.csv` | Two constructed vendors' first call answers | fixed |

The 2.4 percent is a share of wort cast. The book applies it to the 100,000 hL dispatched to keep the sums round, as chapter 7.2 says.

## Licence

Copyright 2026 Ankur Napa. All rights reserved. You may use these files for your own learning; do not republish or redistribute them. Synthetic data only; no real brewery's numbers.
