# Promises the book makes about the companion site

| Where | What the book promises | File | Status |
|---|---|---|---|
| Preface | The Kestrel dataset | `data/*.csv`, `make_data.py` | built |
| Preface | The spreadsheets behind each worked example | `sheets/claim-rebuild-template.xlsx` (ch. 7 to 10), `sheets/working-score-sheet.xlsx` (ch. 4), `sheets/pilot-lines.xlsx` (ch. 11 and 12) | built with a note: chapters 5, 6 and 12.4 have their worked sums in notebooks, not workbooks |
| Preface | A notebook for each "With code" exercise | `notebooks/` | built |
| Preface, Back Matter | A page of errata | none | not built: the lead adds it with the site |
| Ch. 1.3 | Notebook turns a claim into a table of its missing parts | `notebooks/ch02-claim-parts.ipynb` | built with a note: one notebook serves chapters 1 and 2 |
| Ch. 1.3 | The spreadsheets sit on the companion site | `sheets/` | built |
| Ch. 2.5 | Notebook flags which of the five words never appear | `notebooks/ch02-claim-parts.ipynb` | built |
| Ch. 3.6 | Notebook holds the anonymised count table to add a shortlist | `notebooks/ch03-count-table.ipynb`, `data/vendor_counts.csv` | built: counts only, no vendor names or identifying rows |
| Ch. 4.5 | Notebook reads a CSV of scores and flags where two scorers differ by more than one point | `notebooks/ch04-score-sheet.ipynb`, `data/ch04_scores.csv` | built with a note: a single question scores 0 or 1, so it flags claims whose totals differ by more than one point and lists the questions split on; the ch. 4.5 sentence was reworded to match |
| Ch. 5 | Notebook holds a test template for each type: seeded packs, coded stops, a question set, a held out period | `notebooks/ch05-test-templates.ipynb`, `data/ch05_*.csv` | built |
| Ch. 6 | Notebook turns the answers into a flag count for each vendor | `notebooks/ch06-flag-count.ipynb`, `data/ch06_first_call.csv` | built |
| Ch. 7.5 | Notebook `claim-rebuild` runs the sums on Kestrel's synthetic CSV and plots the waterfall | `notebooks/ch07-claim-rebuild.ipynb` | built |
| Ch. 7 footnote 2 | Kestrel Brewing synthetic dataset | `data/kestrel_monthly_loss.csv`, `data/kestrel_inputs.csv` | built |
| Ch. 8 | Notebook `scenarios` draws Figures 8.1 and 8.2 | `notebooks/ch08-scenarios.ipynb` | built |
| Ch. 9 | Notebook `whole-cost` adds the years and the exit | `notebooks/ch09-whole-cost.ipynb` | built |
| Ch. 10 | Notebook prices the same quote fixed and outcome linked | `notebooks/ch10-pricing.ipynb` | built |
| Ch. 11 | Notebook works out the break even, the margin and the sample size | `notebooks/ch11-pilot.ipynb`, `sheets/pilot-lines.xlsx` | built |
| Ch. 11 (front matter) | Fill records to check the 0.6 and 0.4 spreads | `data/fill_records.csv` | built: 0.58 and 0.41, both round to the printed figures |
| Ch. 12 | Notebook reads a pilot result against the lines and simulates how often the rule errs | `notebooks/ch12-decide.ipynb`, `data/pilot_pair_gaps.csv` | built |
| Ch. 12 footnote 1 | The simulation on the synthetic dataset | `notebooks/ch12-decide.ipynb` | built: 5.9, 33 and 94 in 100 at 0.48; 2 in 100 at 0.15; 26 in 100 at 0.27 |
| Back Matter B | The spreadsheet behind Appendix B with the check values | `sheets/claim-rebuild-template.xlsx` | built: cells B1 to B29 as printed |
| Back Matter B | Payback months in the `scenarios` notebook | `notebooks/ch08-scenarios.ipynb` | built: months 22 and 13 |
| Back Matter | The fill records and the weekly loss sheet | `data/fill_records.csv`, `data/weekly_loss_sheet.csv` | built |

No notebook needs a library that is not installed here; every one ran top to bottom.
