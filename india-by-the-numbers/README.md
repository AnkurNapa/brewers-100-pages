# Brewing in India by the Numbers: companion files

The calculator, the rate table template, the synthetic Kestrel India dataset and one notebook for each With code box in the book. Every Kestrel figure is synthetic and so is State S: neither matches a real brewery or a real state. Money is in rupees with Indian digit grouping (10,00,000 is ten lakh); the book rate is USD 1 = INR 90 and the cost of capital is 12 percent.

Nothing here is legal or tax advice. Confirm every rate with the state excise office before you sign a price.

## Run it

```
pip install -r requirements.txt
python3 make_data.py        # writes data/*.csv, data/circulars/ and eval/duty-eval-20.csv from fixed seeds
python3 make_sheets.py      # writes sheets/*.xlsx with live formulas
python3 check_numbers.py    # runs every notebook and checks the numbers the book prints
python3 calculator.py       # a quick self-check of the calculator
```

Open the notebooks from the `notebooks/` folder; they read `../data/` and import `../calculator.py`.

## The core pieces

- **`calculator.py`**: the duty and MRP calculator of Appendix D. It reads a rate table, picks the row in force for a state, strength and date (and refuses when there is none, or two), returns duty for designs A, B, B2 and C and runs the walk from declared manufacturing cost to MRP. It also holds the five rate table checks of chapter 13.4.
- **`sheets/duty-mrp-calculator.xlsx`**: the same calculator as a workbook. Yellow cells are inputs; every other cell is a formula. Sheets: Walk (rate lookup by date and strength, the walk, the waterfall, the reverse formula), Designs (A, B, B2, C and the strength cliff), DMC loop (chapter 6.5), Rates (State S).
- **`sheets/rate-table-template.xlsx`**: the Appendix B.4 template. One row for one rule, one state, one band and one period, with the chapter 5.6 and 13.1 fields. Sheets: Template, Checks, State S (synthetic), State S with the chapter 13.1 change, Real states (as printed).

## Chapter by chapter

| Ch. | File | What it does |
|---|---|---|
| 1, 5, 6 | `notebooks/ch05-duty-calculator.ipynb` | duty under the four designs, the floor, the strength cliff, the walk and its waterfall, a refusal |
| 2 | `notebooks/ch02-volume-price-mix.ipynb` | volume and price mix by route over two years; the price bands |
| 3 | `notebooks/ch03-duty-cash-by-week.ipynb` | cash tied up in duty by week at 30 and 60 days |
| 4 | `notebooks/ch04-star-schema.ipynb` | the star schema; flags rows where stored duty differs from the rate table |
| 6 | `notebooks/ch06-mrp-in-20-lines.ipynb` | the walk in about 20 lines, looped over DMC values |
| 9 | `notebooks/ch09-cost-per-case.ipynb` | three SKU columns from five inputs, tied to ex works a hL; the malt stress |
| 10 | `notebooks/ch10-brewpub.ipynb` | the brewpub P&L and its break-even table, every line open to change |
| 11 | `notebooks/ch11-sku-case.ipynb` | the 36 month SKU case, NPV, worst cash and the tornado |
| 12 | `notebooks/ch12-price-ladder.ipynb` | the walk for each SKU, bands, contribution and trade up |
| 13 | `notebooks/ch13-rate-table-checks.ipynb` | a rule change on 1 October 2026 and the five checks on clean and broken tables |
| 14 | `notebooks/ch14-retrieval.ipynb` | five synthetic circulars split by clause; answers quote the clause or say none was found |
| 14 | `eval/duty-eval-20.csv`, `eval/score_eval.py` | the 20 question duty assistant eval with calculator answers and its scorer; not yet scored |

## The data

| File | What is in it |
|---|---|
| `data/kestrel_india_params.csv` | Kestrel in INR at the book rate: costs a hL, margins, rates of the walk |
| `data/skus.csv` | five packs: lager in three packs, stout and pale ale in 12 x 650 ml; DMC a case |
| `data/rate_table_state_s.csv` | State S duty and fee rows, plus teaching rows for designs A, B and B2 |
| `data/rate_table_state_s_oct_change.csv` | the same table with the chapter 13.1 change to 120 percent from 1 October 2026 |
| `data/rate_table_real_states.csv` | real rates exactly as Appendix B.2 prints them, with source and date; "to verify" on every row, "not found" where the book found nothing; never used by the calculator |
| `data/volume_by_year.csv` | FY2026 and FY2027 volume and revenue by route and beer |
| `data/dispatches_state_s.csv` | 136 transport passes, April to September 2026, with two planted errors |
| `data/dispatch_plan_weekly.csv` | a 26 week dispatch plan for SKU 1 |
| `data/circulars/*.txt` | five synthetic State S circulars |

## Licence

Copyright 2026 Ankur Napa. All rights reserved. You may use these files for your own learning; do not republish or redistribute them. Synthetic data only; no real brewery's numbers.
