# Promises the book makes about the companion site

Every place *The Lab Knows More Than It Says* says a file sits on the companion site, with the file that meets it. Checked 3 November 2026.

| # | Where | What the book promises | File | Status |
|---|---|---|---|---|
| 1 | Preface | Datasets, notebooks and generator scripts with seeds, listed in Appendix E | make_data.py, data/, notebooks/ | built |
| 2 | Ch 1.4, footnotes 1 and 2 | The synthetic week as a CSV and a notebook that counts results per stream | data/week_*.csv, notebooks/ch01-lab-week.ipynb | built with a note: the week comes as the five CSV files chapter 3 describes, not one |
| 3 | Ch 2.6 | A notebook that propagates OG and AE sd into RDF by simulation and plots Figure 2.3 | notebooks/ch02-rdf-uncertainty.ipynb | built |
| 4 | Ch 3.6 | The week (7 x 60 = 420 samples) as five CSV files; a notebook that checks every result points at a real sample, test and spec and lists the orphans | data/week_*.csv, notebooks/ch03-orphans.ipynb | built |
| 5 | Ch 4.4 and 4.5 | A dirty export with the planted faults; a notebook that runs all ten checks and writes a clean table with a fault log | data/ch04_haze_export_raw.csv, data/ch04_planted_faults.csv, notebooks/ch04-ten-checks.ipynb | built |
| 6 | Ch 5.6 | A notebook that builds the chart on the 120 synthetic results | data/ch05_haze.csv, notebooks/ch05-haze-chart.ipynb | built |
| 7 | Ch 6.4 | A notebook that runs CUSUM and EWMA on the 150 results and repeats the 3,000 run test | data/ch06_ph.csv, notebooks/ch06-cusum-ewma.ipynb, sheets/ch06-cusum.xlsx | built; the workbook adds the no code CUSUM recipe |
| 8 | Ch 7.2 and 7.5 | The gauge study in a spreadsheet or the notebook; the water check and the beer chart side by side | data/ch07_checks.csv, data/ch07_gauge_study.csv, notebooks/ch07-instrument-checks.ipynb, sheets/ch07-gauge-study.xlsx | built |
| 9 | Ch 8.6 and 8.2 | A notebook that rebuilds the 300 fill table with seed 42, fits the linear model and gradient boosting on a time split and draws the agreement plot | data/ch08_fills.csv, notebooks/ch08-soft-sensor.ipynb | built with a note: make_data.py builds the table from seed 42; the notebook reads it |
| 10 | Ch 8.4 | The hourly DO run at the filler | data/ch08_do_filler_run.csv | built: the 13 readings printed in 8.4 |
| 11 | Ch 9.6, 9.2 | A notebook that rebuilds the 14,222 results with seed 7, trains on a time split and draws the ranked list; the generator plants 5 hard points and a CIP slip | data/ch09_micro.csv, notebooks/ch09-micro-triage.ipynb | built with a note: make_data.py builds the set from seed 7; the notebook reads it and says what is planted |
| 12 | Ch 10.2 | The duo trio and paired working | notebooks/ch10-panel-stats.ipynb | built |
| 13 | Ch 10.4 and 10.5, footnote 4 | Seed 1011 data; the per taster table; the full power table | data/ch10_scores.csv, notebooks/ch10-panel-stats.ipynb | built |
| 14 | Ch 10.6 | A notebook that rebuilds the ANOVA and per taster tables, draws Figure 10.3 and lets you change tasters and sessions; the triangle in one spreadsheet cell | notebooks/ch10-panel-stats.ipynb, sheets/ch10-triangle.xlsx | built |
| 15 | Ch 11.6, footnote 1 | The record file; a notebook that rebuilds 11.1 to 11.5 from the 400 records, shows the mapping table and runs a fact sheet check; seeds 1102 and 2081 | data/ch11_*.csv, ch11_tpo_lots.py, notebooks/ch11-panel-as-data.ipynb | built |
| 16 | Ch 12.5 | A notebook that scores an assistant on a test set and counts answers with no source | data/ch12_sop_testset.csv, notebooks/ch12-sop-assistant-score.ipynb | built with a note: no language model is called; the citations are synthetic and a reader swaps in their own |
| 17 | Ch 12 footnotes 1 and 3 | Release rule, sample plan, method precision and micro results | data/week_spec_limit.csv, data/week_disposition.csv, data/ch09_micro.csv | built |
| 18 | Ch 13.5 | A notebook that builds the validation summary and the error chart from the 300 fill table | notebooks/ch13-validation-drift.ipynb, data/ch13_live_fills.csv | built; the live fills file carries the malt change at M-26-0188 |
| 19 | Ch 14.5 | A notebook that loads the synthetic week, sets limits from a stable run and draws the chart with CUSUM beneath it | notebooks/ch14-do-chart.ipynb, data/ch14_do_release.csv | built with a note: one week holds about 7 release DO results, too few for a stable run of 60, so the notebook adds a 15 month release DO series. The chapter sentence now names that series |
| 20 | Appendix E table | Each dataset with its generator and seed | make_data.py | built; the "set on the site" seeds are now filled in |
| 21 | Appendix E | One notebook per exercise, with the no code tier as a spreadsheet recipe | notebooks/*.ipynb, sheets/*.xlsx | built with a note: each notebook opens with its spreadsheet recipe; three exercises get a workbook with live formulas |
| 22 | Appendix E | Errata with the page and the fix; tool notes that keep Appendix C current | none | not built: these are site pages the lead writes once the site is live and the book is printed |

Notebooks that are not run here: none. Every notebook ran top to bottom with MPLBACKEND=Agg on 3 November 2026.
