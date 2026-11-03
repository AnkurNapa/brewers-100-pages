"""Build sheets/kestrel-loss-workbook.xlsx: the shared workbook of Appendix C, one sheet per step of the ninety days.

Every computed cell is a live formula. Synthetic Kestrel data only.
Run from the companion folder after make_data.py: python3 sheets/make_workbook.py
"""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sheets" / "kestrel-loss-workbook.xlsx"
HEAD = Font(bold=True, color="FFFFFF")
FILL = PatternFill("solid", fgColor="0B4F45")
INPUT = PatternFill("solid", fgColor="FFF4D6")
NOTE = "Synthetic Kestrel Brewing data. No real brewery's numbers. Book rates: USD 1 = INR 90; EUR 1 = USD 1.10."
USD, PCT, HL = "#,##0", "0.00%", "#,##0.0"


def header(ws, row, names):
    for c, n in enumerate(names, start=1):
        cell = ws.cell(row=row, column=c, value=n)
        cell.font, cell.fill = HEAD, FILL


def widths(ws, w):
    for i, x in enumerate(w, start=1):
        ws.column_dimensions[get_column_letter(i)].width = x


def put(ws, ref, value, fmt=None, inp=False):
    ws[ref] = value
    if fmt:
        ws[ref].number_format = fmt
    if inp:
        ws[ref].fill = INPUT


def definitions(wb):
    ws = wb.create_sheet("Definitions")
    ws["A1"] = "Definitions (chapter 15.1): one definition, one source, one owner for each number"
    ws["A1"].font = Font(bold=True)
    header(ws, 3, ["Number", "Definition", "Unit", "Source", "Owner"])
    rows = [
        ("Kettle volume", "Wort at the end of boil, corrected to 20 degrees C", "hL", "Brewhouse log", "Head brewer"),
        ("Cast volume", "Cold wort into the fermenter, without interface water", "hL", "Fermenter fill", "Head brewer"),
        ("Tank in and tank out", "Volume into and out of each fermenter and bright beer tank", "hL", "Cellar log", "Cellar manager"),
        ("Filter out", "Beer leaving the filter for the bright beer tank", "hL", "Bright beer tank record", "Filtration lead"),
        ("Packaged volume", "Filler count times pack size, plus kegs", "hL", "Filler counter", "Packaging manager"),
        ("Dispatched volume", "Beer leaving the gate", "hL", "Despatch note", "Logistics lead"),
    ]
    for r, row in enumerate(rows, start=4):
        for c, v in enumerate(row, start=1):
            ws.cell(row=r, column=c, value=v)
    ws["A11"] = "Which meaning of batch"
    ws["B11"] = "One fermenter fill (two brews); brew_id keeps each brew as a parent key"
    ws["A12"] = "Gate tolerance"
    put(ws, "B12", "=SQRT(0.5^2+0.5^2)/100", PCT)
    ws["C12"] = "two readings each good to 0.5 percent (chapter 4.4); replace with your own meter checks"
    ws["A14"] = NOTE
    widths(ws, [24, 60, 8, 24, 20])


def dataset(wb):
    ws = wb.create_sheet("Minimum dataset")
    df = pd.read_csv(ROOT / "data" / "minimum_dataset.csv")
    cast_month = df[df.stage == "fermentation"].set_index("batch_id")["date_in"].str[:7]
    df["cast_month"] = df.batch_id.map(cast_month)
    header(ws, 1, list(df.columns))
    for r, row in enumerate(df.itertuples(index=False), start=2):
        for c, v in enumerate(row, start=1):
            ws.cell(row=r, column=c, value=None if pd.isna(v) else v)
    ws.freeze_panes = "A2"
    widths(ws, [12, 20, 13, 9, 11, 11, 13, 14, 8, 13, 12, 13, 14, 14, 11])
    return len(df) + 1


def rng(col, last):
    return f"'Minimum dataset'!${col}$2:${col}${last}"


def mass_balance(wb, last):
    ws = wb.create_sheet("Mass balance")
    ws["A1"] = "Mass balance for the beer cast in one month (chapter 3.2)"
    ws["A1"].font = Font(bold=True)
    ws["A2"] = "Cast month"
    put(ws, "B2", "2026-01", inp=True)
    vin, vout, stg, mon = rng("G", last), rng("H", last), rng("C", last), rng("O", last)
    s = lambda col, stage: f'SUMIFS({col},{stg},"{stage}",{mon},$B$2)'
    header(ws, 4, ["Stage", "In (hL)", "Out (hL)", "Loss (hL)", "Loss, % of cast"])
    rows = [
        ("Cellar: fermentation, maturation, transfers, dry hop", s(vin, "fermentation"), s(vin, "filter")),
        ("Filtration and bright beer tanks", s(vin, "filter"), s(vout, "filter")),
        ("Packaging: fill giveaway, rejects, line flush", s(vin, "package"), s(vout, "package")),
        ("Not explained (packed less dispatched)", s(vin, "dispatch"), s(vout, "dispatch")),
    ]
    for r, (name, a, b) in enumerate(rows, start=5):
        ws[f"A{r}"] = name
        put(ws, f"B{r}", "=" + a, USD)
        put(ws, f"C{r}", "=" + b, USD)
        put(ws, f"D{r}", f"=B{r}-C{r}", USD)
        put(ws, f"E{r}", f"=D{r}/$B$9", PCT)
    ws["A9"] = "Total"
    put(ws, "B9", "=B5", USD)
    put(ws, "C9", "=C8", USD)
    put(ws, "D9", "=SUM(D5:D8)", USD)
    put(ws, "E9", "=D9/B9", PCT)
    ws["A11"] = "Replacement cost, USD (cellar at 30, after the filter at 32)"
    put(ws, "B11", "=D5*30+SUM(D6:D8)*32", USD)
    ws["A12"] = "Peak season upper bound, USD (110 and 112); never add it to the line above"
    put(ws, "B12", "=D5*110+SUM(D6:D8)*112", USD)
    ws["A13"] = "Filtration normal, hL (0.45 percent of cast)"
    put(ws, "B13", "=ROUND(0.0045*B9,0)", USD)
    ws["A14"] = "Filtration excess, hL"
    put(ws, "B14", "=D6-B13", USD)
    ws["A15"] = "Excess at replacement cost, USD (upper bound in C)"
    put(ws, "B15", "=B14*32", USD)
    put(ws, "C15", "=B14*112", USD)
    ws["A17"] = NOTE
    widths(ws, [62, 12, 12, 12, 16])


def gate(wb):
    ws = wb.create_sheet("Gate")
    ws["A1"] = "The gate before money (chapters 4.4 and 15.1): cast less logged losses less packaged"
    ws["A1"].font = Font(bold=True)
    header(ws, 3, ["Item", "Before the meters were checked", "After two weeks of tracing"])
    put(ws, "A4", "Cast (hL)")
    put(ws, "B4", "='Mass balance'!B9", USD)
    put(ws, "C4", "='Mass balance'!B9", USD)
    ws["A5"] = "Logged losses (hL), from the operators' log"
    put(ws, "B5", 240, USD, inp=True)
    put(ws, "C5", 313, USD, inp=True)
    ws["A6"] = "Packaged (hL)"
    put(ws, "B6", "='Mass balance'!C7", USD)
    put(ws, "C6", "='Mass balance'!C7", USD)
    ws["A7"] = "Gap (hL)"
    put(ws, "B7", "=B4-B5-B6", USD)
    put(ws, "C7", "=C4-C5-C6", USD)
    ws["A8"] = "Gap as % of cast"
    put(ws, "B8", "=B7/B4", PCT)
    put(ws, "C8", "=C7/C4", PCT)
    ws["A9"] = "Tolerance"
    put(ws, "B9", "=Definitions!B12", PCT)
    put(ws, "C9", "=Definitions!B12", PCT)
    ws["A10"] = "Result"
    ws["B10"] = '=IF(ABS(B8)<=B9,"Open: price the losses","Shut: fix the measurement first")'
    ws["C10"] = '=IF(ABS(C8)<=C9,"Open: price the losses","Shut: fix the measurement first")'
    ws["A12"] = "This gap is not the closure gap of chapter 3.2, which is packed less dispatched."
    ws["A13"] = NOTE
    widths(ws, [44, 32, 30])


def vessel_balance(wb, last):
    ws = wb.create_sheet("Vessel balance")
    ws["A1"] = "Cellar quarter, step by step (chapter 6.2). Unitanks, so the steps sit in one vessel."
    ws["A1"].font = Font(bold=True)
    vin, vout, heel, stg = rng("G", last), rng("H", last), rng("I", last), rng("C", last)
    s = lambda col, stage: f'SUMIFS({col},{stg},"{stage}")'
    header(ws, 3, ["Step", "Volume in (hL)", "Loss (hL)", "Loss", "Normal", "Excess (hL)"])
    steps = [
        ("Fermentation: crop, cone dumps", f"={s(vin, 'fermentation')}-{s(vout, 'fermentation')}", 0.0100),
        ("Cold conditioning: cone dumps, dry hop slurry", f"={s(vin, 'conditioning')}-{s(vout, 'conditioning')}-{s(heel, 'conditioning')}", 0.0032),
        ("Heel left when the tank is emptied", f"={s(heel, 'conditioning')}", 0.0030),
        ("Transfer to filter", f"={s(vout, 'conditioning')}-{s(vin, 'filter')}", 0.0030),
    ]
    for r, (name, loss, normal) in enumerate(steps, start=4):
        ws[f"A{r}"] = name
        put(ws, f"B{r}", f"={s(vin, 'fermentation')}" if r == 4 else f"=B{r - 1}-C{r - 1}", USD)
        put(ws, f"C{r}", loss, USD)
        put(ws, f"D{r}", f"=C{r}/$B$8", PCT)
        put(ws, f"E{r}", normal, PCT, inp=True)
        put(ws, f"F{r}", f"=MAX(0,ROUND(C{r}-E{r}*$B$8,0))", USD)
    ws["A8"] = "Total"
    put(ws, "B8", "=B4", USD)
    put(ws, "C8", "=SUM(C4:C7)", USD)
    put(ws, "D8", "=C8/B8", PCT)
    put(ws, "E8", "=SUM(E4:E7)", PCT)
    put(ws, "F8", "=SUM(F4:F7)", USD)
    ws["A10"] = "Reached the filter (hL)"
    put(ws, "B10", "=B8-C8", USD)
    ws["A11"] = "Excess, % of cast"
    put(ws, "B11", "=F8/B8", PCT)
    ws["A12"] = "Wort cost per good hL at the filter (24.00 carried)"
    put(ws, "B12", "=24/(B10/B8)", "0.00")
    ws["A13"] = "Excess a year (hL)"
    put(ws, "B13", "=4*F8", USD)
    ws["A14"] = "Replacement cost a year, USD (30 a hL)"
    put(ws, "B14", "=B13*30", USD)
    ws["A15"] = "Peak season upper bound a year, USD (110 a hL)"
    put(ws, "B15", "=B13*110", USD)
    ws["A17"] = NOTE
    widths(ws, [48, 15, 12, 10, 10, 12])


LEDGER_ROWS = [
    # name, quantity, unit, replacement per unit, upper per unit, material, chapter
    ("Extract (scenario)", "=ROUND(5300*104500/300*(0.926/0.92-1),0)", "kg of malt", 0.90, 0.90, 0, "5.5"),
    ("Cellar", "='Vessel balance'!B13", "hL excess", 30, 110, 0, "6.5"),
    ("Filtration", 157, "hL excess", 32, 112, 0, "7.1"),
    ("Fill giveaway", "=ROUND(10.6*10^6*4/100000,0)", "hL (4 ml on 10.6 million cans)", 32, 112, 0, "7.5"),
    ("Packaging rejects (can line)", 280, "hL in 84,848 cans plus the cans", 32, 143, "=ROUND(84848*0.14,0)", "7.3"),
    ("Beer to drain", None, "inside rows 2, 3 and 5", None, None, None, "8.1"),
    ("Water and effluent", 100000, "hL; ratio 4.5 against a target of 4.0", "=0.05*1.2+0.04*1.8", "=0.05*1.2+0.04*1.8", 0, "8.2"),
    ("Line minutes", 6000, "minutes of utilities at USD 1.00", 1, 1, 0, "7.4"),
    ("Tank days, cash held", 290, "overrun tank days at 12 percent", "=600*27*0.12/365", "=600*27*0.12/365", 0, "9.4"),
]


def ledger(wb):
    ws = wb.create_sheet("Ledger")
    ws["A1"] = "One page of losses (chapter 11.1). USD a year. The two money columns are never added."
    ws["A1"].font = Font(bold=True)
    header(ws, 3, ["#", "Loss", "Quantity", "Unit", "Replacement USD a unit", "Upper bound USD a unit", "Material USD",
                   "Replacement cost", "Peak season upper bound", "From"])
    for i, (name, q, unit, rep, ub, mat, ch) in enumerate(LEDGER_ROWS, start=1):
        r = i + 3
        ws[f"A{r}"], ws[f"B{r}"], ws[f"D{r}"], ws[f"J{r}"] = i, name, unit, ch
        if q is None:
            ws[f"H{r}"] = "no sum: counted where lost"
            continue
        put(ws, f"C{r}", q, USD, inp=not str(q).startswith("="))
        put(ws, f"E{r}", rep, "0.000")
        put(ws, f"F{r}", ub, "0.000")
        put(ws, f"G{r}", mat, USD)
        put(ws, f"H{r}", f"=ROUND(C{r}*E{r}+G{r},0)", USD)
        put(ws, f"I{r}", f"=ROUND(C{r}*F{r},0)", USD)
    ws["B13"] = "Total"
    put(ws, "H13", "=SUM(H4:H12)", USD)
    put(ws, "I13", "=SUM(I4:I12)", USD)
    ws["B14"] = "Total in INR (book rate 90)"
    put(ws, "H14", "=H13*90", USD)
    ws["B15"] = "Total in EUR (book rate 1.10)"
    put(ws, "H15", "=H13/1.1", USD)
    ws["B16"] = "USD a hL dispatched"
    put(ws, "H16", "=H13/100000", "0.00")
    ws["B18"] = "Check against finance (chapter 11.3)"
    ws["B18"].font = Font(bold=True)
    ws["B19"] = "Material and beer rows 1 to 5, replacement cost"
    put(ws, "H19", "=SUM(H4:H8)", USD)
    ws["B20"] = "Finance yield and usage variance"
    put(ws, "H20", 128000, USD, inp=True)
    ws["B21"] = "Not yet explained"
    put(ws, "H21", "=H20-H19", USD)
    ws["B22"] = "Share not yet explained (send under 10 percent)"
    put(ws, "H22", "=H21/H20", PCT)
    ws["B24"] = NOTE
    widths(ws, [4, 30, 12, 36, 14, 14, 12, 16, 20, 7])


def owner_page(wb):
    ws = wb.create_sheet("Owner page")
    ws["A1"] = "The owner page (chapter 11.4): three numbers, one chart, one ask"
    ws["A1"].font = Font(bold=True)
    ws["A3"] = "Losses a year, replacement cost, USD"
    put(ws, "B3", "=Ledger!H13", USD)
    ws["C3"] = "Upper bound, labelled, never added"
    put(ws, "D3", "=Ledger!I13", USD)
    ws["A4"] = "Held by the top three, USD"
    put(ws, "B4", "=LARGE(Ledger!H4:H12,1)+LARGE(Ledger!H4:H12,2)+LARGE(Ledger!H4:H12,3)", USD)
    ws["C4"] = "Share"
    put(ws, "D4", "=B4/B3", "0.0%")
    ws["A5"] = "Not yet explained, USD"
    put(ws, "B5", "=Ledger!H21", USD)
    ws["A7"] = "Chart: the ledger waterfall sorted by size, the gap as a grey bar labelled not yet explained."
    ws["A9"] = "The ask"
    ws["B9"] = "A schedule rule so beer stops waiting in the fermenter for a bright tank. USD 3,000, owner: the planner."
    ws["A11"] = "Basis: replacement cost, USD a year. Date: write the issue date here."
    ws["A12"] = NOTE
    widths(ws, [40, 14, 34, 14])


FIXES = [
    ("A. Cellar", 15000, 0.60, 6000, "Yes, minimum dataset", "One SOP", "Low", "Yes"),
    ("B. Giveaway", 6784, 0.70, 2500, "Yes, check weigher", "One SOP", "Low", "Yes"),
    ("C. Water", 13200, 0.45, 18000, "Partly, no meter on pushes", "One instrument", "Low", "Next quarter"),
    ("D. Line minutes", 6000, 0.35, 40000, "No, stops are not coded", "Three: counter, plant link, reason screen", "Medium", "No"),
    ("E. Waiting days", 59752, 0.40, 3000, "Yes, occupancy table and brew plan", "One schedule rule", "Low, the beer is unchanged", "Yes"),
    ("F. Lager price", 73200, 0.30, 3000, "Yes", "None", "High, customers", "Owner's call"),
]


def fix_ranking(wb):
    ws = wb.create_sheet("Fix ranking")
    ws["A1"] = "Ranking six fixes (chapters 12.2 and 12.3). Change a probability in column C and the ranks move."
    ws["A1"].font = Font(bold=True)
    ws["A2"] = "Cost of capital"
    put(ws, "B2", 0.12, "0%", inp=True)
    ws["C2"] = "Annuity factor, 3 years"
    put(ws, "D2", "=1/(1+B2)+1/(1+B2)^2+1/(1+B2)^3", "0.0000")
    header(ws, 4, ["Fix", "Value", "P", "Cost", "Expected a year", "Payback, months", "NPV over 3 years",
                   "Net, year one", "Rank by NPV", "Rank by payback"])
    for r, (name, v, p, c, *_rest) in enumerate(FIXES, start=5):
        ws[f"A{r}"] = name
        put(ws, f"B{r}", v, USD, inp=True)
        put(ws, f"C{r}", p, "0.00", inp=True)
        put(ws, f"D{r}", c, USD, inp=True)
        put(ws, f"E{r}", f"=B{r}*C{r}", USD)
        put(ws, f"F{r}", f"=D{r}/(E{r}/12)", "0.0")
        put(ws, f"G{r}", f"=E{r}*$D$2-D{r}", USD)
        put(ws, f"H{r}", f"=E{r}-D{r}", USD)
        put(ws, f"I{r}", f"=RANK(G{r},$G$5:$G$10,0)")
        put(ws, f"J{r}", f"=RANK(F{r},$F$5:$F$10,1)")
    ws["A12"] = "Fix A at the peak season upper bound: value 55,000"
    put(ws, "E12", "=55000*C5", USD)
    put(ws, "F12", "=D5/(E12/12)", "0.0")
    put(ws, "G12", "=E12*$D$2-D5", USD)
    ws["A14"] = "F is a price move and the owner's call: list it apart from savings. Never put savings in the revenue column."
    ws["A15"] = NOTE
    widths(ws, [20, 10, 6, 10, 15, 15, 16, 14, 12, 15])


def gates(wb):
    ws = wb.create_sheet("Gates")
    ws["A1"] = "Gates (chapter 12.4): a fix that fails a gate waits; it is not dead"
    ws["A1"].font = Font(bold=True)
    header(ws, 3, ["Fix", "Data ready", "Change load", "Blast radius", "This quarter?"])
    for r, (name, _v, _p, _c, data, load, blast, now) in enumerate(FIXES, start=4):
        for c, val in enumerate([name, data, load, blast, now], start=1):
            ws.cell(row=r, column=c, value=val)
    ws["A11"] = NOTE
    widths(ws, [18, 34, 40, 26, 14])


def fix_card(wb):
    ws = wb.create_sheet("Fix card")
    ws["A1"] = "Fix card (chapter 14.1): one owner, one changed SOP, one check date"
    ws["A1"].font = Font(bold=True)
    header(ws, 3, ["Field", "Entry"])
    rows = [
        ("Loss", "Cellar loss above normal (chapter 6.5)"),
        ("Excess a year (hL)", "='Vessel balance'!B13"),
        ("Share of cast", "='Vessel balance'!B13/(4*'Vessel balance'!B8)"),
        ("Owner", "The cellar lead, by name"),
        ("Changed SOP", "After every transfer the operator records the heel left in the vessel. Any heel above that vessel's normal gets a reason code"),
        ("Baseline (hL a month)", "=ROUND(B5/12,1)"),
        ("Target", "Back to each vessel's normal within two quarters: 0 hL excess"),
        ("Value at replacement cost, USD a year (30 a hL)", "=B5*30"),
        ("Peak season upper bound, USD a year (110 a hL), labelled", "=B5*110"),
        ("Check date", "The second monthly review after the SOP starts"),
        ("Stop rule", "Under half of target at the check: stop and write down why"),
    ]
    for r, (k, v) in enumerate(rows, start=4):
        ws[f"A{r}"] = k
        ws[f"B{r}"] = v
    ws["B6"].number_format = PCT
    for ref in ("B5", "B11", "B12"):
        ws[ref].number_format = USD
    ws["A16"] = NOTE
    widths(ws, [54, 100])


def review(wb):
    ws = wb.create_sheet("Review")
    ws["A1"] = "The monthly loss review (chapter 14.2): one hour, one page, the same order each month"
    ws["A1"].font = Font(bold=True)
    header(ws, 3, ["Minutes", "Item", "Question", "Notes this month"])
    items = [(5, "The gate", "Does the mass balance close?"), (10, "The ledger", "Does the sum of losses match finance's gap?"),
             (15, "The three largest losses", "In money, against baseline and band"), (15, "Open fixes", "Owner reports; check dates due"),
             (10, "One new item", "Only one"), (5, "Read back", "Owner, change and date for each decision")]
    for r, (m, item, q) in enumerate(items, start=4):
        ws[f"A{r}"], ws[f"B{r}"], ws[f"C{r}"] = m, item, q
    put(ws, "A10", "=SUM(A4:A9)")
    ws["B10"] = "minutes in all"
    header(ws, 12, ["Line", "Baseline a month", "This month", "Saving", "Value, USD", "Status"])
    ws["A13"] = "Cellar excess, hL (30 USD a hL)"
    put(ws, "B13", "='Fix card'!B9", HL)
    put(ws, "C13", 29.2, HL, inp=True)
    put(ws, "D13", "=B13-C13", HL)
    put(ws, "E13", "=D13*30", USD)
    ws["F13"] = "indicated"
    ws["A14"] = "Tank day overrun, days (one in five sold at 1,717)"
    put(ws, "B14", "=ROUND(290/12,1)", HL)
    put(ws, "C14", 15.0, HL, inp=True)
    put(ws, "D14", "=B14-C14", HL)
    put(ws, "E14", "=D14*0.2*1717", USD)
    ws["F14"] = "indicated"
    ws["A15"] = "Three months below the band before a saving reads banked. Keep savings out of the revenue column."
    ws["A16"] = NOTE
    widths(ws, [46, 26, 46, 18, 12, 12])


def true_cogs(wb):
    ws = wb.create_sheet("True COGS")
    ws["A1"] = "True COGS per hL, March (chapter 10): the brand split from the chapter"
    ws["A1"].font = Font(bold=True)
    header(ws, 3, ["Line", "USD, March", "Per hL sold"])
    lines = [("Materials", 152000), ("Packaging", 248000), ("Direct labour", 48000), ("Utilities", 56000), ("Overhead", 176000)]
    for r, (k, v) in enumerate(lines, start=4):
        ws[f"A{r}"] = k
        put(ws, f"B{r}", v, USD, inp=True)
        put(ws, f"C{r}", f"=B{r}/$B$12", "0.00")
    ws["A9"] = "COGS before duty"
    put(ws, "B9", "=SUM(B4:B8)", USD)
    put(ws, "C9", "=B9/$B$12", "0.00")
    ws["A10"] = "Freight (not in COGS: cost to serve)"
    put(ws, "B10", 56000, USD, inp=True)
    ws["A12"] = "hL sold"
    put(ws, "B12", "=B16+B17", USD)
    ws["A13"] = "Divided by hL cast instead (1.045 x sold)"
    put(ws, "C13", "=B9/(1.045*B12)", "0.00")

    header(ws, 15, ["Brand", "hL sold", "Brews", "Tank days a fill", "hL-days", "Volume", "Brew", "Tank day", "Net price"])
    for r, (b, hl, brews, td, price) in enumerate([("Lager", 6000, 20, 30, 140), ("Pale ale", 2000, 7, 16, 180)], start=16):
        ws[f"A{r}"] = b
        put(ws, f"B{r}", hl, USD, inp=True)
        put(ws, f"C{r}", brews, inp=True)
        put(ws, f"D{r}", td, inp=True)
        put(ws, f"E{r}", f"=B{r}*D{r}", USD)
        put(ws, f"F{r}", "=$B$8/$B$12", "0.00")
        put(ws, f"G{r}", f"=$B$8/($C$16+$C$17)*C{r}/B{r}", "0.00")
        put(ws, f"H{r}", f"=$B$8/($E$16+$E$17)*D{r}", "0.00")
        put(ws, f"I{r}", price, "0.00", inp=True)

    header(ws, 19, ["Brand by pack", "hL sold", "Materials", "Packaging", "Labour and utilities", "Overhead by tank day", "True cost"])
    ws["J19"] = "Packaging standard"
    packs = [("Lager bottle", 4470, "=105000/B16", 36, 16), ("Lager keg", 1530, "=105000/B16", 2, 16), ("Pale ale can", 2000, "=47000/B17", 42, 17)]
    for r, (name, hl, mat, std, brand_row) in enumerate(packs, start=20):
        ws[f"A{r}"] = name
        put(ws, f"B{r}", hl, USD, inp=True)
        put(ws, f"C{r}", mat, "0.00")
        put(ws, f"J{r}", std, "0.00", inp=True)
        if "can" in name:
            put(ws, f"D{r}", "=84000/B22", "0.0000")
        else:
            put(ws, f"D{r}", f"=164000*J{r}/($J$20*$B$20+$J$21*$B$21)", "0.0000")
        put(ws, f"E{r}", "=($B$6+$B$7)/$B$12", "0.00")
        put(ws, f"F{r}", f"=H{brand_row}", "0.00")
        put(ws, f"G{r}", f"=SUM(C{r}:F{r})", "0.00")
    ws["A23"] = "Packaging ledger: can line store 84,000; bottle and keg store 164,000, split by standard cost."

    header(ws, 25, ["USD per hL", "Lager", "Pale ale"])
    rows = [
        ("Cost on paper", "=$C$9", "=$C$9"),
        ("Margin on paper", "=I16-B26", "=I17-C26"),
        ("True cost", "=(G20*B20+G21*B21)/B16", "=G22"),
        ("Overhead by tank day", "=H16", "=H17"),
        ("Direct cost", "=B28-B29", "=C28-C29"),
        ("True margin", "=I16-B28", "=I17-C28"),
        ("March margin, USD", "=B31*B16", "=C31*B17"),
    ]
    for r, (k, a, b) in enumerate(rows, start=26):
        ws[f"A{r}"] = k
        put(ws, f"B{r}", a, USD if r == 32 else "0.00")
        put(ws, f"C{r}", b, USD if r == 32 else "0.00")
    ws["A33"] = "Total margin, USD (allocation moves cost between brands and creates none)"
    put(ws, "B33", "=B32+C32", USD)

    header(ws, 35, ["Variance (standard 83.00, actual 85.00)", "USD, month", "USD per hL", "Owner"])
    for r, (k, v, o) in enumerate([("Price", 2000, "Purchasing"), ("Yield", 10400, "Plant manager"), ("Mix", 3600, "Sales planning")], start=36):
        ws[f"A{r}"] = k
        put(ws, f"B{r}", v, USD, inp=True)
        put(ws, f"C{r}", f"=B{r}/$B$12", "0.00")
        ws[f"D{r}"] = o
    ws["A39"] = "Total"
    put(ws, "B39", "=SUM(B36:B38)", USD)
    put(ws, "C39", "=B39/$B$12", "0.00")
    ws["A41"] = NOTE
    widths(ws, [44, 12, 12, 14, 18, 18, 12, 10, 10, 18])


def main():
    wb = Workbook()
    wb.remove(wb.active)
    definitions(wb)
    last = dataset(wb)
    mass_balance(wb, last)
    gate(wb)
    vessel_balance(wb, last)
    ledger(wb)
    owner_page(wb)
    fix_ranking(wb)
    gates(wb)
    fix_card(wb)
    review(wb)
    true_cogs(wb)
    wb.properties.creator = "Ankur Napa"
    wb.properties.title = "The Money in the Tank: Kestrel loss workbook"
    wb.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
