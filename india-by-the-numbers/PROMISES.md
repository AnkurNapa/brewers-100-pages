# Promises the book makes about this companion

Every place *Brewing in India by the Numbers* says a file sits on the companion site, with the file that meets it. All data is synthetic: Kestrel Brewing and State S match no real brewery or state.

| Ch. | Where | What the book promises | File | Status |
|---|---|---|---|---|
| 1 | 1.4 Try it | the calculator runs the walk from DMC to MRP; change one input and watch the waterfall move | `sheets/duty-mrp-calculator.xlsx` (Walk sheet, waterfall table); `notebooks/ch05-duty-calculator.ipynb` | built |
| 1 to 15 | footnotes | the Kestrel Brewing synthetic dataset | `data/*.csv` from `make_data.py` | built |
| 2 | 2.6 Try it | a notebook that splits revenue growth into volume and price mix on synthetic Kestrel data and plots the bands of 2.2 | `notebooks/ch02-volume-price-mix.ipynb`, `data/volume_by_year.csv` | built with a note: the bible sets no brand mix, so FY2026 uses lager 70, pale ale 10 and stout 20 percent, the mix that gives the bible's blended INR 13,500 a hL |
| 3 | 3.4 Try it | a notebook that takes a dispatch plan and plots cash tied up in duty by week for 30 and 60 day payment | `notebooks/ch03-duty-cash-by-week.ipynb`, `data/dispatch_plan_weekly.csv` | built with a note: the 60 day line counts from dispatch; transit days to the depot are left out |
| 4 | 4.4 Try it | a notebook that builds the star schema from the synthetic State S files and flags rows where the stored duty differs from the rate table | `notebooks/ch04-star-schema.ipynb`, `data/dispatches_state_s.csv`, `data/skus.csv`, `data/rate_table_state_s.csv` | built: two planted rows are flagged |
| 5 | 5.6 Try it | the calculator reads the table, picks the row in force on a given date and returns duty for designs A, B, B2 and C | `calculator.py`, `notebooks/ch05-duty-calculator.ipynb`, `sheets/duty-mrp-calculator.xlsx` (Walk and Designs sheets) | built |
| 5 | 5.6, Appendix B.4 | the rate table template with its fields | `sheets/rate-table-template.xlsx`, `data/rate_table_state_s.csv` | built |
| 6 | 6.5 Try it | a notebook that does the walk in about 20 lines and loops over a range of DMC values | `notebooks/ch06-mrp-in-20-lines.ipynb`; also the DMC loop sheet of the calculator workbook | built |
| 9 | 9.6 Try it | a notebook that rebuilds the three SKU columns from five inputs and asserts each SKU ties to its ex works a hL | `notebooks/ch09-cost-per-case.ipynb` | built |
| 10 | 10.6 Try it | a notebook that reruns the brewpub table with every line open to change | `notebooks/ch10-brewpub.ipynb` | built |
| 11 | 11.5 Try it | the SKU table and the tornado from a notebook | `notebooks/ch11-sku-case.ipynb` | built |
| 12 | 12.4 Try it | the ladder notebook reruns the walk for each SKU | `notebooks/ch12-price-ladder.ipynb` | built |
| 13 | 13.4 Try it | the rate table notebook runs the five checks | `notebooks/ch13-rate-table-checks.ipynb`, `data/rate_table_state_s_oct_change.csv` | built |
| 14 | 14.6 Try it | the retrieval notebook indexes five synthetic circulars | `notebooks/ch14-retrieval.ipynb`, `data/circulars/*.txt` | built with a note: TF-IDF from scikit-learn stands in for a search service; all five circulars are in English, so the language row of 14.6 is not built |
| 14 | 14.5, Appendix D | the duty assistant eval: 20 questions with calculator answers, scored as passes out of 20 with traps on their own line | `eval/duty-eval-20.csv` (written by `make_data.py` from the calculator), `eval/score_eval.py` | built with a note: the question set and the scorer are built; no model has been run against it, so there is no score |
| Appendix B | B.2 | real state rates as the book prints them, with source and date | `data/rate_table_real_states.csv`; the Real states sheet of the template | built with a note: copied only where the book prints a rate with its source and date; every printed row is "to verify"; rates the book could not find are rows marked "not found" with no figure. The Kerala Bevco margin is a 2022 proposal, not a rate, so it has no row. None is used by the calculator |
| Appendix D | | live rates and errata | none | not built: the build day exchange rate and corrections are for the lead to add when the site goes live |

The No code boxes ask readers to build their own sheets; they are not companion promises.
