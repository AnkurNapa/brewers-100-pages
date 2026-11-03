"""Writes the three workbooks in sheets/ with live formulas (Appendices A to C).

Run: python3 make_sheets.py
"""
import csv
import os

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.join(HERE, "sheets")
BOLD, CLAIM = Font(bold=True), Font(color="C27C0E", bold=True)
INPUT = PatternFill("solid", fgColor="F4F8F7")

# Appendix B: (row, item, value or formula, Kestrel check value, number format)
REBUILD = [
    (1, "Volume, hL a year", 100000, 100000, "#,##0"),
    (2, "Cellar loss rate, twelve months", 0.024, 0.024, "0.000"),
    (3, "Share recovered, the claim", 0.20, 0.20, "0.00"),
    (4, "Value of a lost hL, replacement cost", 30, 30, "#,##0"),
    (5, "Licence, USD a month", 1400, 1400, "#,##0"),
    (6, "Cloud bill, USD a month", 250, 250, "#,##0"),
    (7, "Saving a year", "=B1*B2*B3*B4", 14400, "#,##0"),
    (8, "Net of licence and cloud bill", "=B7-12*(B5+B6)", -5400, "#,##0"),
    (9, "Value of a lost hL, peak season upper bound", 110, 110, "#,##0"),
    (10, "Saving at the upper bound", "=B1*B2*B3*B9", 52800, "#,##0"),
    (11, "Net at the upper bound", "=B10-12*(B5+B6)", 33000, "#,##0"),
    (12, "Excess cellar loss rate", 0.005, 0.005, "0.000"),
    (13, "Largest share any tool can recover", "=B12/B2", 0.208, "0.000"),
    (14, "Claim inside the ceiling?", '=IF(B3<=B13,"YES","NO")', "YES", "General"),
    (15, "p, the chance a found saving is banked (0.25, 0.45 or 0.70)", 0.45, 0.45, "0.00"),
    (16, "Share of a full year earned in year one", "=(0*3+0.5*3+1*6)/12", 0.625, "0.000"),
    (17, "Full years earned over three years", "=B16+2", 2.625, "0.000"),
    (18, "Install, one off", 6000, 6000, "#,##0"),
    (19, "Data preparation, one off", "=120*50", 6000, "#,##0"),
    (20, "People time, year one", "=(13*4+39*1)*40", 3640, "#,##0"),
    (21, "People time, each later year", "=52*1*40", 2080, "#,##0"),
    (22, "Whole cost, year one", "=12*(B5+B6)+B18+B19+B20", 35440, "#,##0"),
    (23, "Whole cost, each later year", "=12*(B5+B6)+B21", 21880, "#,##0"),
    (24, "Whole cost, three years", "=B22+2*B23", 79200, "#,##0"),
    (25, "Exit, in the year the contract ends", "=30*50", 1500, "#,##0"),
    (26, "Steady net at the upper bound", "=B10*B15-B23", 1880, "#,##0"),
    (27, "Cash at month 36 at the upper bound", "=B10*B15*B17-B24", -16830, "#,##0"),
    (28, "Break even share, steady", "=B23/B10", 0.41, "0%"),
    (29, "Break even share, three years", "=B24/(B10*B17)", 0.57, "0%"),
    (31, "B8 in rupees, book rate 90", "=B8*90", -486000, "#,##0"),
    (32, "B8 in euros, book rate 1.10", "=ROUND(B8/1.1,-2)", -4900, "#,##0"),
]
CHECKS = [("Conservative", 0.25, -18280, -8680, -44550), ("Base", 0.45, -15400, 1880, -16830),
          ("Stretch", 0.70, -11800, 15080, 17820), ("Everything banked", 1.00, -7480, 30920, 59400)]


def rebuild():
    wb = Workbook()
    ws = wb.active
    ws.title = "Rebuild"
    ws["D1"], ws["E1"] = "Kestrel check", "Formula (Appendix B)"
    ws["D1"].font = ws["E1"].font = BOLD
    for row, item, val, check, fmt in REBUILD:
        ws.cell(row, 1, item)
        c = ws.cell(row, 2, val)
        c.number_format = fmt
        if not str(val).startswith("="):
            c.fill = INPUT
        ws.cell(row, 4, check).number_format = fmt
        ws.cell(row, 5, str(val) if str(val).startswith("=") else "input")
    ws["B3"].font = CLAIM
    ws["A34"] = "Synthetic Kestrel Brewing figures, USD. B3 is the vendor's promise; everything else is yours."
    ws["A35"] = "Payback months need the monthly model in the scenarios notebook. This sheet works in years."
    ws.column_dimensions["A"].width = 58
    ws.column_dimensions["E"].width = 30

    cv = wb.create_sheet("Check values")
    for i, h in enumerate(["Case", "p", "Steady net at USD 30", "Steady net at USD 110",
                           "Cash at month 36, USD 110", "Book: USD 30", "Book: USD 110", "Book: month 36"]):
        cv.cell(1, i + 1, h).font = BOLD
    for r, (name, p, a, b, c) in enumerate(CHECKS, start=2):
        cv.cell(r, 1, name)
        cv.cell(r, 2, p)
        cv.cell(r, 3, f"=Rebuild!B7*B{r}-Rebuild!B23").number_format = "#,##0"
        cv.cell(r, 4, f"=Rebuild!B10*B{r}-Rebuild!B23").number_format = "#,##0"
        cv.cell(r, 5, f"=Rebuild!B10*B{r}*Rebuild!B17-Rebuild!B24").number_format = "#,##0"
        for j, v in enumerate((a, b, c)):
            cv.cell(r, 6 + j, v).number_format = "#,##0"
    cv.column_dimensions["A"].width = 20

    pr = wb.create_sheet("Pricing")
    rows = [("Monthly price, one year term", 1400), ("Monthly price, three year term", 1190),
            ("One year", "=B1*12"), ("Three one year terms", "=B3*3"), ("Three year deal", "=B2*36"),
            ("Saved by the three year deal", "=B4-B5"), ("Owed if you stop after month 12", "=B2*24"),
            ("Outcome fee share of verified saving", 0.33), ("Agreed value of a recovered hL", 110)]
    for r, (item, val) in enumerate(rows, start=1):
        pr.cell(r, 1, item)
        pr.cell(r, 2, val)
    pr["A11"], pr["B11"], pr["C11"], pr["D11"], pr["E11"] = "Verified hL", "Saving", "Fixed fee: net", "Outcome fee", "Outcome fee: net"
    for r, hl in zip((12, 13, 14), (100, 300, 480)):
        pr.cell(r, 1, hl)
        pr.cell(r, 2, f"=A{r}*$B$9")
        pr.cell(r, 3, f"=B{r}-$B$3")
        pr.cell(r, 4, f"=ROUND(B{r}*$B$8,0)")
        pr.cell(r, 5, f"=B{r}-D{r}")
    pr.column_dimensions["A"].width = 38
    wb.save(os.path.join(SHEETS, "claim-rebuild-template.xlsx"))


QUESTIONS = [
    "Is the baseline named and dated?", "Is the formula shown?", "Are the inputs the buyer's own?",
    "Is the fee deducted?", "Is there a conservative case?", "Is the ramp up time modelled?",
    "Is the result measured by someone other than the seller?", "Is price tied to result in any way?"]


def score_sheet():
    wb = Workbook()
    ws = wb.active
    ws.title = "Working Score"
    for i, h in enumerate(["#", "Question", "Scorer 1 point", "Scorer 1 source", "Scorer 2 point", "Scorer 2 source"]):
        ws.cell(1, i + 1, h).font = BOLD
    example = [1, 1, 1, 1, 1, 1, 0, 0]  # claim C of chapter 4.4
    for i, q in enumerate(QUESTIONS):
        ws.cell(i + 2, 1, i + 1)
        ws.cell(i + 2, 2, q)
        ws.cell(i + 2, 3, example[i]).fill = INPUT
        ws.cell(i + 2, 5, example[i] if i != 5 else 0).fill = INPUT
    ws["B10"], ws["C10"], ws["E10"] = "Score, 0 to 8", "=SUM(C2:C9)", "=SUM(E2:E9)"
    ws["B11"] = "Read it as"
    for col in "CE":
        ws[f"{col}11"] = f'=IF({col}10<=2,"Discount to zero",IF({col}10<=5,"Ask for working","Worth a pilot"))'
    ws["B12"], ws["C12"] = "Totals differ by more than one point?", '=IF(ABS(C10-E10)>1,"Read the page together","No")'
    ws["B14"] = "One point only for a full yes; a half answer scores zero. Example: claim C of chapter 4.4, constructed."
    ws.column_dimensions["B"].width = 58
    wb.save(os.path.join(SHEETS, "working-score-sheet.xlsx"))


def pilot_lines():
    wb = Workbook()
    ws = wb.active
    ws.title = "Lines"
    rows = [
        ("Value of a recovered hL, signed by the planner", 110, 110),
        ("Volume, hL a year", 100000, 100000),
        ("Whole cost, three years", 79200, 79200),
        ("Full years earned over three years", 2.625, 2.625),
        ("Matched pairs", 6, 6),
        ("Spread of pair gaps, points", 0.4, 0.4),
        ("Fills a tank in the measured period", 2, 2),
        ("t value, one sided 5 percent, six pairs", 2.0, 2.0),
        ("Saving per point a year", "=B2/100*B1", 110000),
        ("Three year break even, points", "=B3/(B9*B4)", 0.27),
        ("Kill line X, points", "=ROUNDUP(B10,1)", 0.3),
        ("Spread of each pair figure", "=B6/SQRT(B7)", 0.28),
        ("Standard error of the average", "=B12/SQRT(B5)", 0.115),
        ("Noise margin", "=B8*B13", 0.23),
        ("Pass line Z, points", "=B11+ROUND(B14,2)", 0.53),
        ("Pair gaps to show the full claim against zero (Lehr)", "=8*B6^2/0.48^2", 5.6),
        ("Pair gaps to show it clears the kill line (Lehr)", "=8*B6^2/(0.48-B11)^2", 40),
    ]
    ws["C1"].value = None
    for r, (item, val, check) in enumerate(rows, start=1):
        ws.cell(r, 1, item)
        c = ws.cell(r, 2, val)
        if not str(val).startswith("="):
            c.fill = INPUT
        ws.cell(r, 3, check)
    ws["D1"] = "Column C: the Kestrel figure from chapter 11.5 and Appendix C"
    ws.column_dimensions["A"].width = 52

    rd = wb.create_sheet("Read the result")
    rd["A1"], rd["B1"] = "Pair", "Pair figure, first look (average of its gaps)"
    with open(os.path.join(HERE, "data", "pilot_pair_gaps.csv")) as f:
        gaps = [r for r in csv.DictReader(f) if r["phase"] == "first_look"]
    for p in range(1, 7):
        rd.cell(p + 1, 1, p)
        rd.cell(p + 1, 2, round(sum(float(r["gap_points"]) for r in gaps if int(r["pair"]) == p) / 2, 3))
    rd["A9"], rd["B9"] = "Result", "=AVERAGE(B2:B7)"
    rd["A10"], rd["B10"] = "STDEV.S / SQRT(6)", "=_xlfn.STDEV.S(B2:B7)/SQRT(6)"
    rd["A11"], rd["B11"] = "Reading", '=IF(B9<Lines!B11,"Stop",IF(B9>=Lines!B15,"Pass, if the route to cash holds","Extend once"))'
    rd.column_dimensions["A"].width = 20
    wb.save(os.path.join(SHEETS, "pilot-lines.xlsx"))


if __name__ == "__main__":
    os.makedirs(SHEETS, exist_ok=True)
    rebuild()
    score_sheet()
    pilot_lines()
    print("wrote", ", ".join(sorted(os.listdir(SHEETS))))
