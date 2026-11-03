# From Grain to GenAI: companion files

Datasets, notebooks and one spreadsheet for *From Grain to GenAI: The Brewer's 100 Pages of AI*. Every file is synthetic. The numbers the chapters print come out of this data; `check_numbers.py` proves it.

Copyright 2026 Ankur Napa. All rights reserved. You may use these files for your own learning; do not republish or redistribute them. Synthetic data only; no real brewery's numbers.

## How to run

```
pip install -r requirements.txt
python3 make_data.py       # writes data/*.csv from fixed seeds
python3 make_sheets.py     # writes sheets/ch11-pilot-payback.xlsx
python3 check_numbers.py   # asserts every printed number
```

Open any notebook in `notebooks/` with Jupyter, or upload it with the `data` folder to a browser notebook. Notebooks read `../data/`.

## Chapter by chapter

| Chapter | Files | What it shows |
|---|---|---|
| 4 Brewery data | `plant_brews`, `plant_historian`, `plant_lab`, `plant_lots`, `plant_sales`, `plant_losses`; `ch04-four-source-join` | Four sources joined on batch ID with typed IDs, a historian gap, barrels in a hectolitre column and the 13.2 against 12.9 degrees Plato batch (B24-118) |
| 5 Predicting | `rdf_batches`, `stuck_ferments`, `outlets`; `ch05-predict-number-and-class` | RDF from wort sugars against a baseline; stuck fermentation risk with its confusion matrix at 0.5 and 0.3; the outlet reorder list |
| 6 Patterns and time | `outlets`, `recipes`, `ferm_healthy`, `ferm_new`, `ferm_new_inspection`, `monthly_volume`; `ch06-outlet-clusters`, `ch06-fermentation-anomalies`, `ch06-seasonal-forecast` | k-means groups; a normal band from 200 curves that flags three of 40; a 24 plus 12 month backtest |
| 7 Deep learning | `kernels`, `filler_head7`; `ch07-kernels-and-filler` | A small neural network on 400 kernel pictures drawn with numpy; a control chart on a filling head drifting 0.5 ml an hour |
| 8 NLP | `complaints`, `lab_notes`; `ch08-complaint-sorter`, `ch08-lab-note-search` | Five defect classes with precision and recall; search by meaning over lab notes |
| 9 Generative AI | `golden_set`, `sop_snippets`; `ch09-tools-and-evals` | ABV, attenuation and IBU tools; a numeric scorer; a ten question golden set scored by category |
| 10 The business | `radar_extract`; `ch10-radar-extract` | Counts by theme and grade from an anonymised radar extract |
| 11 Pilot to money | `sheets/ch11-pilot-payback.xlsx` | The 11.1 payback with live formulas on Kestrel Brewing synthetic figures |
| 14 and 15 Projects | `plant_*`, `stuck_ferments`, `sop_snippets`, `golden_set` | Extract efficiency by brew, the stuck flag, an SOP assistant, the lot genealogy, the loss waterfall (B24-150: 500 hl out, 490 hl packed) and a lab against line register |

## Notes

- Where the book prints a result, `make_data.py` searches seeds in a fixed order or picks test rows from a seeded pool until that result comes out. The results show how a method behaves, not what a real plant would find.
- The radar extract carries no company names. Its grade totals and its shipping and no claim counts by theme match the author's published analysis of 15 September 2026; the pilot, research and ungraded split inside each theme is allocated for this extract.
- The lab note search uses latent semantic analysis as a small stand-in for an embedding model.
- The chapter 9 notebook scores canned answers from two assistant versions. Replace `ask` with your own model. Figure 9.3 in the book stays illustrative.
- The STL step in `ch06-seasonal-forecast` needs statsmodels. Everything else needs only the libraries in `requirements.txt` without it.
- The book's figures were drawn by their own scripts. They match the printed numbers, not every dot in these files.
