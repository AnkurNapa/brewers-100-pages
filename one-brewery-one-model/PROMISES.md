# Promises the book makes about companion files

Status: built, built with a note or not built. Tested on 3 November 2026: `make_data.py`, `check_numbers.py`
(125 printed numbers), `pipeline.py` (run twice) and all 14 notebooks run top to bottom.

| Where | Promise | File | Status |
|---|---|---|---|
| Preface, companion site | A slice of the Kestrel dataset: three brew days, six fermenters, two packaging lines, about 40 lots | `data/`, `make_data.py` | Built: 3 brew days, 6 fermenters, 2 lines, 36 lots |
| Preface; 1.4 | One notebook for each With code tier | `notebooks/` | Built: 14 notebooks, chapters 2 to 15 (chapters 1 and 9 have no With code tier) |
| Preface; 9.5.1 | The loop and notebook forms of the lineage query | `sql/lineage_forward_loop.sql`, `notebooks/ch09-lineage.ipynb` | Built with a note: the T-SQL loop is not run here (SQLite has no WHILE); its Python twin is tested equal to the CTE |
| Preface; 11.1; Appendix D | The KPI dictionary as a CSV file | `data/kpi_dictionary.csv` | Built: 20 entries, Appendix D text, Appendix C columns |
| Preface | The errata | `README.md`, Errata | Built: none yet |
| Footnotes, ch. 4 to 12 | Kestrel Brewing synthetic dataset | `data/` | Built |
| 2.6 | Builds the six brew week; counts by brew, fill and date code; 24 hour window changed to 12 | `notebooks/ch02-batch-count.ipynb` | Built: 6, 3, 4; 12 hours gives 4 fills |
| 3.7 | Synthetic week with three gravity sources; precedence table; rank 1; gap band; efficiency under each source | `notebooks/ch03-precedence.ipynb` | Built |
| 4.4 | Cuts one synthetic trace into events and prints the unmatched ones | `notebooks/ch04-tag-events.ipynb` | Built: FV07, one unmatched restarted transfer |
| 5.5 | Runs the three joins on the sample table and reports the share matched by each | `notebooks/ch05-sample-joins.ipynb` | Built with a note: a bright tank holds a fill for up to six days, a working value chosen here |
| 6.5 | Planned against actual per brew; flags missing movements | `notebooks/ch06-planned-actual.ipynb` | Built with a note: the 5,340 kg backflush example of 6.3 is worked arithmetic; the slice's variance is on B26-0073 |
| 7.4 | Builds the cross reference table and counts unmatched keys | `notebooks/ch07-xref.ipynb` | Built: 4 unmatched codes |
| 8.6 | Builds all 14 tables from the Kestrel extract; runs the share check | `notebooks/ch08-model-tables.ipynb` | Built |
| 9.5.1 | The CTE run on SQLite returns 23 pallets at 0.783; the loop gives the same; backward gives 0.783 and 0.217 | `sql/lineage_forward.sql`, `sql/lineage_backward.sql`, `check_numbers.py` | Built |
| 10.5 | Builds the stage table from vessel events; prints the closure gap per month | `notebooks/ch10-mass-balance.ipynb` | Built with a note: the year is held as vessel event volumes summed by month and stage, not one row per event |
| 11.5; 14.2 | Each entry reproduces its check value on the synthetic dataset | `check_numbers.py`, `notebooks/ch14-measures.ipynb` | Built: all 18 stated check values pass; 17 and 20 wait for a hold record and the drill log |
| 11.6 | Reads a dictionary CSV; fails a missing field, a formula naming a column the model lacks, a blank owner | `notebooks/ch11-dictionary-check.ipynb` | Built with a note: names in backticks in the formula or source fields are checked; Appendix D formulas are prose, so the notebook breaks a copy to show the failure |
| 12.4 | Runs the five checks on the Kestrel week; writes a quarantine table | `notebooks/ch12-quality-checks.ipynb` | Built: 7 rows, one or more per check |
| 13.3 | Builds `silver_vessel_event` for the slice; prints the quarantine table | `notebooks/ch13-silver-vessel-event.ipynb` | Built with a note: only FV07 has a historian trace in the slice; other fills come from typed logs |
| 13.5 | The companion pipeline runs the slice twice and proves the second run changes no rows | `pipeline.py` | Built with a note: SQLite stands in for the lakehouse and warehouse |
| 14.2 | Loads the gold tables, evaluates the first 20 measures, prints the test table | `notebooks/ch14-measures.ipynb` | Built with a note: entry 17 (hold rate) is blank because `batch` has no hold column; entry 20 is blank until QA fills `drill_log.csv` |
| 15.5 | Clone the repository, build the slice through bronze, silver and gold, run the forward trace on one malt lot | `pipeline.py`, `notebooks/ch15-first-week.ipynb` | Built |
| Appendix B.2; 3.2.3 | The precedence table the pipeline reads | `data/precedence.csv` | Built |
| Appendix C | Model tables with these column names | `data/*.csv`, `sql/views.sql`, `pipeline.py` | Built: 14 core and 9 reference tables as CSV; `quarantine`, views, `lineage_path`, `source_comparison` and the five KPI tables built by the pipeline |
| Appendix C.3 | A small drill log that QA fills in | `data/drill_log.csv` | Built: header only |
| Appendix C.5 | The lineage query and the WHILE loop | `sql/` | Built: character for character |

## Slice values printed in Appendix D

OEE 67.6 percent over all line shifts; reject rate 0.27 percent; right first time 66.7 percent (F08-26-035 failed
bitterness on first test); spec compliance 100.0 percent on current results; complaints per million packs 5.44
for April 2026. Appendix D prints these five as check values, labelled as slice values. They are teaching values from a three day slice, not plant figures.
