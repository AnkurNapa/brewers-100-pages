# Companion promises: From Grain to GenAI

Every place the book promises a companion file, the file that meets it and its status.

| Where | Promise | File | Status |
|---|---|---|---|
| Preface | Notebooks and datasets on the companion site | whole folder | built |
| 1.3.3 | Datasets, notebooks and updates on the companion site | whole folder | built |
| 4.6 With code | Synthetic four source plant extract; notebook joins on batch ID and counts batches that fail to match | `data/plant_*.csv`, `notebooks/ch04-four-source-join.ipynb` | built |
| 4.2, 4.3 | 13.2 against 12.9 degrees Plato; three unit conversions | `plant_lab`, `plant_historian` (B24-118); `check_numbers.py` | built |
| 5.6 With code | Notebook that builds both models in the chapter with scikit-learn | `notebooks/ch05-predict-number-and-class.ipynb` | built |
| 5.2.1 | 180 batches, 144 and 36, baseline 66.5, rows T01 to T05, MAE 0.9 and 2.1 on five, 1.0 and 2.1 on 36 | `data/rdf_batches.csv` | built |
| 5.3 | 480 batches, 32 stuck, 120 test with 8 stuck, confusion 6, 5, 2, 107, precision 55, recall 75, threshold 0.3 | `data/stuck_ferments.csv` | built |
| 5.5 | 600 outlets, 372 reordered, 78 of the top 100 lapsed | `data/outlets.csv` | built |
| 5 front matter | Companion notebook must reproduce 5.2, 5.3 and 5.5 | `check_numbers.py` | built |
| 6.6 With code | k-means on the outlet table | `notebooks/ch06-outlet-clusters.ipynb`, `data/outlets.csv`, `data/recipes.csv` | built |
| 6.6 With code | Anomaly detector on the fermentation curves | `notebooks/ch06-fermentation-anomalies.ipynb`, `data/ferm_*.csv` | built |
| 6.6 With code | Seasonal forecast with a backtest, scikit-learn and statsmodels | `notebooks/ch06-seasonal-forecast.ipynb`, `data/monthly_volume.csv` | built with a note: the STL cell uses statsmodels, not installed here, so that cell was not run here; the backtest runs on scikit-learn and is checked |
| 6.2 to 6.5 | 270, 210 and 120 outlets; 576 and 115,200 readings; 3 of 40 flagged with their causes; 1,200 and 850 hl; MAPE 9 and 7 | `check_numbers.py` | built |
| 7.7 With code | Small image classifier on synthetic kernel pictures | `notebooks/ch07-kernels-and-filler.ipynb`, `data/kernels.csv` | built with a note: 400 pictures of 24 by 24 pixels drawn with numpy; the classifier is a one layer neural network from scikit-learn |
| 7.7 With code | Control chart for a drifting filler | same notebook, `data/filler_head7.csv` | built: 10 hours to the limit; the chart signals at 1.75 hours with every pack in spec |
| 8.7 With code | Sorts 300 synthetic complaints into five classes, reports precision and recall | `notebooks/ch08-complaint-sorter.ipynb`, `data/complaints.csv` | built: diacetyl 8 true, 9 flagged, 6 right |
| 8.7 With code | Search by meaning over synthetic lab notes | `notebooks/ch08-lab-note-search.ipynb`, `data/lab_notes.csv` | built with a note: latent semantic analysis stands in for an embedding model, which is not installed here |
| 9.8 With code | ABV and attenuation tools, a numeric scorer and a ten question golden set | `notebooks/ch09-tools-and-evals.ipynb`, `data/golden_set.csv` | built with a note: canned answers from two versions stand in for a model call |
| 9.5, 9.6 | 4.77, 4.27, 2.95, 1.0115, 5.46, 77.3; Tinseth 34, Rager 46, 35 percent; 5.5 passes, 5.4 fails | `check_numbers.py` | built |
| 9 front matter, Figure 9.3 | Replace the illustrative scorecard with the real notebook run | none | not built: the notebook scores ten questions, not the six category percentages in the figure; the figure stays labelled illustrative |
| 10 Try it | Radar extract; count by theme and grade | `notebooks/ch10-radar-extract.ipynb`, `data/radar_extract.csv` | built with a note: anonymised, no company names; pilot, research and ungraded counts inside each theme are allocated |
| 11.1 footnote 5 | Kestrel Brewing synthetic dataset, value of a lost hl and running costs | `sheets/ch11-pilot-payback.xlsx` | built: live formulas, checked |
| 14.4 | Three portfolio projects on the book's synthetic brewery dataset | `plant_brews` (efficiency), `stuck_ferments`, `sop_snippets` and `golden_set` | built (data only; the book promises no notebook) |
| 14 and 15 front matter | Companion dataset names for 14.4 and 15.5 | names in appendix D and this table | built |
| 15.5 | Dictionary, loss waterfall (500 out, 490 packed, 2 percent), lab against line register | `plant_lots`, `plant_losses` (B24-150), `plant_lab`, `plant_historian` | built |
| Appendix D | Dataset and notebooks list | appendix D rewritten to list these files | built |
| Appendix D | Errata and updated tool notes | none | not built: site pages the lead adds once the site is live |
