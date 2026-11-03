# Promises in The Money in the Tank and the files that meet them

| # | Where | What the book promises | File | Status |
|---|---|---|---|---|
| 1 | Preface, synthetic data section | The Kestrel dataset on the companion site | `data/*.csv`, `make_data.py` | Built |
| 2 | Preface | One notebook for each "With code" exercise | `notebooks/` (ten notebooks) | Built |
| 3 | Preface; Appendix C | The workbook described in Appendix C | `sheets/kestrel-loss-workbook.xlsx` | Built with a note: a True COGS sheet is added for the chapter 10 brand split (the chapter 10 to_verify asks for it); Appendix C now lists it |
| 4 | Preface | The live rates | Appendix B in the book | Not built: the rates are dated in Appendix B; the site page is for the lead to add at publish |
| 5 | Preface | The errata | none | Not built: there are no errata before publication |
| 6 | Ch 1.4 | The datasets sit on the companion site | `data/` | Built |
| 7 | Ch 3.5 | Notebook builds the stage table from the Kestrel dataset (one row per batch per stage) and flags any stage where the balance does not close | `notebooks/ch03-mass-balance.ipynb` | Built |
| 8 | Ch 4.3; Appendix C | The minimum dataset, one row per batch per stage | `data/minimum_dataset.csv` | Built with a note: adds a `dispatch` stage, a `heel_hl` column and the `counter` measure source; Appendix C updated to match |
| 9 | Ch 5.6 | Notebook reads 60 brews, splits conversion from lauter and draws Figure 5.2 | `notebooks/ch05-extract-loss.ipynb`, `data/brewhouse_brews.csv` | Built |
| 10 | Ch 6.6 | Notebook builds the Kestrel quarter table and Figure 6.1 from the synthetic dataset | `notebooks/ch06-cellar-loss.ipynb` | Built |
| 11 | Ch 7.6 | Notebook reads a fill-weight file, plots mean and spread by shift, prices the giveaway | `notebooks/ch07-giveaway.ipynb`, `data/fill_weights.csv` | Built |
| 12 | Ch 8.5 | Notebook turns a daily COD series and production volume into spike days and the hL each implies | `notebooks/ch08-cod-spikes.ipynb`, `data/effluent_daily.csv` | Built |
| 13 | Ch 9.5 | Notebook reads a tank occupancy file, finds overlapping intervals, prints contribution per tank day | `notebooks/ch09-tank-days.ipynb`, `data/tank_occupancy.csv` | Built |
| 14 | Ch 10.5 | Notebook reads the minimum dataset and the cost ledger and draws the grid for every brand | `notebooks/ch10-true-cogs.ipynb`, `data/cost_ledger_march.csv` | Built with a note: the minimum dataset carries no brand, so the notebook reads the month's volumes by brand and pack; the chapter sentence and Appendix C are reworded to say so |
| 15 | Ch 11.4 | Notebook builds the table and both waterfalls from the minimum dataset and flags any row that lacks a sum | `notebooks/ch11-loss-ledger.ipynb`, `data/loss_drivers.csv` | Built with a note: only the cellar row comes from the minimum dataset; the other rows come from a file of loss drivers; the chapter sentence and Appendix C are reworded to say so |
| 16 | Ch 12.6 | Notebook does the sums, reruns the ranking when a probability changes, draws the effort map | `notebooks/ch12-fix-ranking.ipynb`, `data/fixes.csv` | Built |
| 17 | Ch 13.4 | Notebook rebuilds the table from the synthetic ledger and draws both figures | `notebooks/ch13-shocks.ipynb`, `data/shock_inputs.csv` | Built |
| 18 | Appendix C | Ten notebooks, one per code tier | `notebooks/` | Built |
| 19 | Appendix C | Workbook sheets: Definitions, Minimum dataset, Mass balance, Gate, Vessel balance, Ledger, Owner page, Fix ranking, Gates, Fix card, Review | `sheets/kestrel-loss-workbook.xlsx` | Built; 207 live formulas, recalculated in LibreOffice and checked against the book |

## Notes on the numbers

- `check_numbers.py` asserts 255 printed numbers from chapters 3 to 15 against the data.
- Chapter 5.1 prints a specific gravity of 1.0484 at 12.0 degrees Plato. The polynomial gives 1.04838, which rounds to 1.0484 (corrected from 1.0483 on 3 November 2026). The extract (12.56 kg a hL, 3,767 kg a brew) did not move. The check compares to four places.
- Chapter 6.6 speaks of "about 43 fills" a quarter. The dataset has 45: 42 fills of two brews and 3 of one brew, 87 brews in all.
- Chapter 10.5 rounds lager packaging to 27.33 a hL. The ledger books 164,000 to the bottle and keg store, which is 27.333; the printed March margin of 343,566 needs the unrounded figure, so the notebook uses the ledger.
- Two transfers (one in January, one in February) lose more than 0.7 percent of the fill; the chapter 3 notebook flags both, which is the point of the flag.
