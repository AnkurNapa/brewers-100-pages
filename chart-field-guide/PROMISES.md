# Promises the book makes about the companion site

Every place *The Brewer's Chart Field Guide* says a file sits on the companion site, with the file that meets it.

| # | Where | What the book promises | File | Status |
|---|---|---|---|---|
| 1 | Preface, The companion site | The Kestrel tables | `data/*.csv` from `make_data.py` | built |
| 2 | Ch 2, 2.5 With code | A notebook that draws one Kestrel question three ways with open source plotting libraries | `notebooks/ch02-three-ways.ipynb` | built with a note: matplotlib and pandas plotting are the two libraries |
| 3 | Ch 3, 3.4 With code | A notebook that draws each of the seven lies on Kestrel data, then redraws them | `notebooks/ch03-seven-lies.ipynb` | built with a note: lies 2, 4 and 5 use the chapter's worked numbers, since the dataset holds no such series |
| 4 | Ch 4, 4.4 With code | A notebook that loads the Kestrel tables and prints the row count and key uniqueness of each | `notebooks/ch04-row-counts.ipynb` | built |
| 5 | Ch 4 footnote 1 | Kestrel defined in the companion dataset | `data/`, `README.md` | built |
| 6 | Ch 5, 5.3 and B.2 | Eleven healthy pale ale fills plus one stall; band 3.30 to 3.86 at hour 72 | `data/Fill.csv`, `data/HourlyGravity.csv` | built |
| 7 | Ch 6, 6.6 With code | A notebook that builds the chart, CUSUM and EWMA on the forty Kestrel fills | `notebooks/ch06-control-chart.ipynb`, `data/Batch.csv` | built |
| 8 | Ch 7, 7.6 With code | A notebook that builds the stage table, waterfall and reconcile check | `notebooks/ch07-loss-waterfall.ipynb`, `data/Stage.csv` | built; the Preface list now names it too |
| 9 | Ch 7 footnote 1 | Loss shares, hL a month and replacement cost by stage | `data/Stage.csv`, `data/Volume.csv` | built |
| 10 | Ch 8 footnote 2 | Can line 500 cans a minute, 330 ml | `data/Run.csv`, `data/Stop.csv` | built |
| 11 | Ch 9 footnote 2 | Brand volumes, pack split, net prices and contribution | `data/Sales.csv`, `data/Sku.csv`, `data/Depletions.csv` | built |
| 12 | Ch 13, 13.3 With code | A notebook that builds the limits and the reconcile check | `notebooks/ch13-limits-reconcile.ipynb` | built |
| 13 | Ch 14, 14.5 With code | A notebook that reads a report's definition and lists visuals without a title or an axis unit | `notebooks/ch14-visual-lint.ipynb`, `report/Kestrel Cellar.Report/` | built with a note: reads the PBIR folder format only; the sample report is synthetic and hand written, not a Power BI Desktop export |
| 14 | Ch 15, 15.4 With code | A notebook that runs the four Kestrel checks and prints pass or fail | `notebooks/ch15-trust-checks.ipynb` | built; the sensor check fails on purpose for the F11 dropout |
| 15 | Ch 15 footnote 1 | Kestrel synthetic dataset for the chapter | `data/Readings.csv`, `data/Fill.csv` | built |
| 16 | Appendix B, B.2 to B.11 | Ten DAX patterns, ready to copy | `dax/pattern-01-*.dax` to `dax/pattern-10-*.dax` | built with a note: text exactly as printed; not run in Power BI here, known answers checked in pandas |
| 17 | Appendix B, B.12 and B.13 | Two KQL queries | `kql/kql-1-golden-band.kql`, `kql/kql-2-live-tile.kql` | built with a note: text exactly as printed; not run in an Eventhouse here, the band is checked in pandas |
| 18 | Appendix B, B.1 | The Kestrel model uses these table and column names | `data/*.csv` | built; B.1 now lists the Brew table pattern 4 needs |
| 19 | Preface | No downloadable Power BI template is promised | none | not built: a PBIX or PBIP file cannot be built here; `README.md` says how to load the CSVs, DAX and KQL |
| 20 | Ch 6 and 13 | A Fabric notebook or Eventhouse item | none | not built: Fabric items cannot be built here; the README covers loading the CSVs into a lakehouse and an Eventhouse |

## Book sentences changed to match the files

- Preface, The companion site: the list of notebooks now includes chapter 7 (the stage table, waterfall and reconcile check).
- Appendix B.1: adds the Brew table that pattern 4 reads.
- Appendix B.4: the known answer now says Cpk is about 1.01 from the unrounded moving range, 1.02 with sigma rounded to 0.129 as in chapter 6. The DAX does not round.

## Tests run

- `python3 make_data.py` then `python3 check_numbers.py`: 110 checks pass.
- Every notebook run top to bottom as a script with `MPLBACKEND=Agg`: all eight pass.
