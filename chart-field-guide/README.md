# The Brewer's Chart Field Guide: companion files

The working files for *The Brewer's Chart Field Guide*. Every figure is Kestrel Brewing, the synthetic brewery of the series. No real plant numbers, no client names and no vendor prices appear.

## How to run it

```
pip install -r requirements.txt
python3 make_data.py
python3 check_numbers.py
```

`make_data.py` writes every CSV in `data/` from fixed seeds. `check_numbers.py` asserts the numbers the book prints from this data (110 checks); it also rebuilds the DAX known answers of Appendix B and the KQL golden band in pandas.

Open the notebooks in Jupyter from the `notebooks/` folder; they read `../data/`.

## Chapter by chapter

| Chapter | File | What it does |
|---|---|---|
| 2 | `notebooks/ch02-three-ways.ipynb` | "Is tank F07 behaving?" drawn by calendar date, by batch hour and as small multiples (matplotlib and pandas plotting) |
| 3 | `notebooks/ch03-seven-lies.ipynb` | The seven lies drawn before and after |
| 4 | `notebooks/ch04-row-counts.ipynb` | Row count, key and key check of every table, then a repeat made on purpose |
| 5, B.2, B.12 | `data/Fill.csv`, `data/HourlyGravity.csv`, `data/Readings.csv` | The twelve pale ale fills: the band at hour 72 is 3.30 to 3.86 with a median of 3.60 |
| 6 | `notebooks/ch06-control-chart.ipynb` | The individuals chart, CUSUM and EWMA on the forty lager fills, plus Cp, Cpk, Pp and Ppk |
| 7 | `notebooks/ch07-loss-waterfall.ipynb` | The stage table, the waterfall from cast to dispatch, the reconcile check, the Pareto and brewhouse yield |
| 8, B.6 | `data/Run.csv`, `data/Stop.csv` | Ten four hour runs on the can line: OEE 73.7 percent; small stops by hour into the run |
| 9, B.9 | `data/Sales.csv`, `data/Sku.csv`, `data/Depletions.csv` | March and April by SKU, account and channel; the margin bridge from 666,300 to 667,200 |
| 11, 15 | `data/Fill.csv` | The 2026 fill schedule: 174 fills, 4,653 of 5,475 tank days (85 percent) |
| 12, B.10 | `data/Link.csv`, `data/Lab.csv` | The genealogy of F07-26-034 and F09-26-036 into two bright tanks and two pack lots |
| 13 | `notebooks/ch13-limits-reconcile.ipynb` | Mean FG at fill 5 and fill 35, the flat limits and the 370 hL reconcile |
| 14 | `notebooks/ch14-visual-lint.ipynb` | Reads a report definition and lists visuals without a title or an axis unit |
| 15 | `notebooks/ch15-trust-checks.ipynb` | The four Kestrel trust checks, printed PASS or FAIL; the F11 dropout fails on purpose |
| Appendix B | `dax/*.dax`, `kql/*.kql` | The ten DAX patterns and two KQL queries, exactly as the book prints them |

## The tables

Names follow Appendix B.1. Chapter 12 calls the same data by role; the map is below.

| File | One row is | Chapter 12 role |
|---|---|---|
| `Readings.csv` | one tag reading on one tank (gravity every 10 minutes on the reference fills; temperature every minute on 14 April 2026) | fact_sensor |
| `Lab.csv` | one result for one analyte on one sample | fact_lab |
| `Brew.csv`, `Fill.csv`, `Link.csv` | one brew, one fill, one parent to child link | fact_batch_step |
| `Run.csv`, `Stop.csv` | one packaging run, one stop | fact_pack |
| `Sales.csv` | one SKU, account and month | fact_sales |
| `Batch.csv`, `BatchAfterFix.csv` | one lager fill on the chapter 6 chart, then 20 fills after the fix | quality view of fill |
| `HourlyGravity.csv` | one fill, one whole hour from hour zero | resampled sensor fact |
| `Volume.csv`, `Stage.csv`, `Daily.csv` | one month of cast and dispatch, one loss stage in one month, one day of dispatch | summaries |
| `Depletions.csv` | one distributor month of the chapter 9 soft quarter | distributor feed |
| `Tank.csv`, `Sku.csv`, `Date.csv`, `AsOf.csv` | one fermenter, one SKU, one day, one moment | dimensions |

A few choices to know:

- March 2026 is "the Kestrel month": 8,700 hL cast, 8,330 dispatched, stage losses of 209, 52, 87 and 22 hL. Other months vary around it. February carries the 2.2 percent cellar loss of chapter 3.
- The twelve fills of chapter 5 ran in October 2025 (IDs such as F07-25-302), so they sit outside the 2026 schedule. F09 holds the stalled fill.
- Fill IDs in 2026 count plant wide: fill 34 is F07-26-034 and holds brews B26-0067 and B26-0068.
- The bright tank IDs (BT03-26-071, BT04-26-072) follow the fill pattern; the series fixes no format for them. The chain's pack lots are L260416-C1-1 and L260416-C1-2, because F09-26-036 ends its 30 days on 14 April. The book's L260412-C1-1 is an example of the format.
- `Lab.csv` holds more than one analyte. Filter `Analyte` before pattern 9 or pattern 10, or the average mixes pH with gravity.
- Lies 2, 4 and 5 of chapter 3 use the chapter's own worked numbers inside the notebook. The dataset holds no sales against temperature series and no week of filler oxygen.
- The chapter 14 sample report in `report/` is synthetic and hand written in the PBIR folder format (one `visual.json` per visual). It was not exported from Power BI Desktop, so check the notebook against one of your own exports.

## Loading it into Power BI, Fabric or an Eventhouse

No Power BI file (PBIX or PBIP) ships here; the book does not promise one. To build the model yourself:

1. **Power BI Desktop.** Use Get data then Text/CSV to load every file in `data/` except `Readings.csv` and `Depletions.csv`. Set `HourZero`, `FillEnd`, `SampledAt`, `EnteredAt` and `Moment` to Date/Time and every `Date` or `Month` column to Date.
2. **Relationships**, all many to one, single direction: `HourlyGravity[FillId]` to `Fill[FillId]`; `Fill[Tank]` to `Tank[Tank]`; `Batch[FillId]` to `Fill[FillId]`; `Sales[Sku]` to `Sku[Sku]`; `Sales[Date]`, `Daily[Date]`, `Volume[Month]` and `Stage[Month]` to `Date[Date]`. Mark `Date` as the date table. Leave `Link`, `Lab`, `Run` and `AsOf` unrelated; patterns 9 and 10 use TREATAS and a disconnected table.
3. **Measures.** Paste each `dax/pattern-NN-*.dax` file into a measures table. Pattern 4 reads `Brew[ExtractKg]` and `Brew[TheoreticalKg]`.
4. **Known answers.** Check each pattern against the line printed in Appendix B. `check_numbers.py` prints the same values from pandas, so a mismatch points at the model, not the data.
5. **Fabric lakehouse.** Upload the CSVs to the Files area, load each to a Delta table with the same name and build a Direct Lake or import model on top with the steps above.
6. **Eventhouse.** Create two tables, `Readings (Tank:string, Tag:string, Time:datetime, Value:real)` and `Fills (FillId:string, Tank:string, Brand:string, HourZero:datetime, FillEnd:datetime, IsReference:bool)`. Ingest `Readings.csv` into the first. Ingest `Fill.csv` into the second, keeping those six columns. Run `kql/kql-1-golden-band.kql`: hour 72 reads 3.30, 3.60 and 3.86. With eleven fills the Eventhouse percentile and the DAX one give the same values. `kql-2-live-tile.kql` looks back 15 minutes from now, so on this static data it returns rows only if you shift `Time` to the present.

None of the DAX, the KQL or the PBIR sample has been run inside Power BI, Fabric or an Eventhouse for this release; the pandas twins in `check_numbers.py` have.

## Licence

Copyright 2026 Ankur Napa. All rights reserved. You may use these files for your own learning; do not republish or redistribute them. Synthetic data only; no real brewery's numbers.
