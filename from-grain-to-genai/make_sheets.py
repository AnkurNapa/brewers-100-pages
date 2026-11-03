"""Write sheets/ch11-pilot-payback.xlsx: the 11.1 arithmetic as live formulas.

Kestrel Brewing synthetic figures. Change a blue input and every result moves.
Run: python3 make_sheets.py
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

OUT = Path(__file__).resolve().parent / "sheets" / "ch11-pilot-payback.xlsx"

INPUTS = [
    ("Beer made (hl a year)", 100000),
    ("Loss brewhouse to filler", 0.02),
    ("Value of a lost hl, replacement (USD)", 30),
    ("Value of a lost hl, peak upper bound (USD)", 110),
    ("Loss cut by the pilot (points)", 0.003),
    ("Chance the saving is banked", 0.45),
    ("Licence (USD a year)", 16800),
    ("Cloud (USD a year)", 3000),
    ("People time (USD a year)", 2080),
    ("Pilot budget (USD)", 30000),
]
# label, formula; B2 to B11 hold the inputs above
RESULTS = [
    ("Loss today (hl)", "=B2*B3"),
    ("Loss today, replacement (USD a year)", "=B12*B4"),
    ("Loss today, upper bound (USD a year)", "=B12*B5"),
    ("Saving aimed at (hl)", "=B2*B6"),
    ("Saving, replacement (USD a year)", "=B15*B4"),
    ("Saving, upper bound (USD a year)", "=B15*B5"),
    ("Banked, replacement (USD a year)", "=B16*B7"),
    ("Banked, upper bound (USD a year)", "=B17*B7"),
    ("Running cost, bought tool (USD a year)", "=B8+B9+B10"),
    ("Net, bought (USD a year)", "=B18-B20"),
    ("Net, bought, upper bound (USD a year)", "=B19-B20"),
    ("Running cost, built in a spreadsheet (USD a year)", "=B10"),
    ("Net, built (USD a year)", "=B18-B23"),
    ("Payback, built (years)", '=IF(B24>0,B11/B24,"never")'),
    ("Net, built, upper bound (USD a year)", "=B19-B23"),
    ("Payback, built, upper bound (years)", '=IF(B26>0,B11/B26,"never")'),
]


def main():
    wb = Workbook()
    ws = wb.active
    ws.title = "Payback"
    ws.append(["Item", "Value"])
    ws["A1"].font = ws["B1"].font = Font(bold=True)
    for label, value in INPUTS:
        ws.append([label, value])
        ws.cell(ws.max_row, 2).font = Font(color="0000CC")
    for label, formula in RESULTS:
        ws.append([label, formula])
    ws.append([])
    ws.append(["Synthetic Kestrel Brewing figures. Blue cells are inputs."])
    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 14
    wb.properties.creator = "Ankur Napa"
    wb.properties.title = "Pilot payback, chapter 11"
    OUT.parent.mkdir(exist_ok=True)
    wb.save(OUT)


if __name__ == "__main__":
    main()
