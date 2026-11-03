"""Builds the two workbooks in sheets/ with live formulas (openpyxl).

sheets/duty-mrp-calculator.xlsx  the calculator: rate lookup by date and strength,
                                 designs A, B, B2 and C, the walk to MRP, the reverse
                                 formula and a loop over DMC values
sheets/rate-table-template.xlsx  the Appendix B.4 template with the State S rows,
                                 the chapter 13.1 change, the real rows as printed
                                 and the five checks
Synthetic State S only in the calculator. Rupees use Indian digit grouping.
Run make_data.py first, then: python3 make_sheets.py
"""
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
DATA, OUT = HERE / "data", HERE / "sheets"
INR = r'[>=10000000]##\,##\,##\,##0.00;[>=100000]##\,##\,##0.00;##,##0.00'
INR0 = r'[>=10000000]##\,##\,##\,##0;[>=100000]##\,##\,##0;##,##0'
DATE = "d mmm yyyy"
PCT = "0.00%"
BOLD = Font(bold=True)
HEAD = PatternFill("solid", fgColor="CFE6E1")
INPUT = PatternFill("solid", fgColor="FFF2CC")
NOTE = Font(italic=True, color="6B6B6B")
OPEN = datetime(2099, 12, 31)
AUTHOR = "Ankur Napa"

RATE_FIELDS = ["row_id", "state", "kind", "item", "band", "abv_min", "abv_max", "design", "share",
               "floor_per_bl", "rate_per_bl", "rate_per_lal", "fee_amount", "fee_unit",
               "effective_from", "effective_to", "to_or_open", "row_no", "notification", "link",
               "source_fetch_date", "checked_by", "checked_on", "status", "note"]


def widths(ws, w):
    for i, x in enumerate(w, 1):
        ws.column_dimensions[get_column_letter(i)].width = x


def header(ws, row, names):
    for j, n in enumerate(names, 1):
        c = ws.cell(row, j, n)
        c.font, c.fill = BOLD, HEAD
        c.alignment = Alignment(wrap_text=True, vertical="top")


def as_date(v):
    return None if pd.isna(v) or v == "" else datetime.strptime(str(v)[:10], "%Y-%m-%d")


def write_rates(ws, table, first=2, with_checks=False):
    """One row per rule. to_or_open and row_no are formulas so lookups work on open rows."""
    header(ws, first - 1, RATE_FIELDS + (["overlaps", "days since check", "expiry check"] if with_checks else []))
    n = len(table)
    last = first + n - 1
    for i, r in enumerate(table.to_dict("records")):
        x = first + i
        for j, f in enumerate(RATE_FIELDS, 1):
            if f == "to_or_open":
                ws.cell(x, j, f'=IF(P{x}="",DATE(2099,12,31),P{x})').number_format = DATE
            elif f == "row_no":
                ws.cell(x, j, f"=ROW()")
            elif f in ("effective_from", "effective_to", "source_fetch_date", "checked_on"):
                c = ws.cell(x, j, as_date(r.get(f)))
                c.number_format = DATE
            else:
                v = r.get(f)
                ws.cell(x, j, None if pd.isna(v) else v)
        if with_checks:
            rng = lambda col: f"${col}${first}:${col}${last}"
            ws.cell(x, 26, (f'=IF(O{x}="","",COUNTIFS({rng("B")},B{x},{rng("C")},C{x},{rng("D")},D{x},{rng("E")},E{x},'
                            f'{rng("O")},"<="&Q{x},{rng("Q")},">="&O{x}))'))
            ws.cell(x, 27, f'=IF(W{x}="","",Checks!$B$3-W{x})')
            ws.cell(x, 28, f'=IF(AA{x}="","no check recorded",IF(AA{x}>90,"FAIL","pass"))')
    widths(ws, [20, 12, 7, 18, 30, 8, 8, 7, 7, 8, 8, 8, 11, 22, 12, 12, 12, 7, 50, 40, 12, 20, 12, 12, 60, 9, 9, 16])
    ws.freeze_panes = ws.cell(first, 2)
    return last


def calculator():
    rates = pd.read_csv(DATA / "rate_table_state_s.csv")
    wb = Workbook()
    wb.properties.creator = AUTHOR
    wb.properties.title = "Duty and MRP calculator, State S (synthetic)"
    wb.properties.created = wb.properties.modified = datetime(2026, 11, 3)
    w = wb.active
    w.title = "Walk"
    ws = wb.create_sheet("Rates")
    last = write_rates(ws, rates)
    R = lambda col: f"Rates!${col}$2:${col}${last}"

    w["A1"] = "Duty and MRP calculator, synthetic State S (Brewing in India by the Numbers, chapters 1.4, 5 and 6)"
    w["A1"].font = Font(bold=True, size=12)
    w["A2"] = "Yellow cells are inputs. Every other cell is a formula. State S matches no real state. Not legal or tax advice."
    w["A2"].font = NOTE
    inputs = [("Net price a hL (DMC basis), INR", 12600, "#,##0"), ("Bottles a case", 12, "0"),
              ("Litres a bottle", 0.65, "0.000"), ("ABV, percent", 5.3, "0.0"),
              ("Dispatch date", datetime(2026, 7, 15), DATE), ("State", "S", "@"),
              ("Buyer margin (0.08 wholesaler, 0.10 corporation)", 0.08, PCT), ("Retailer margin", 0.15, PCT),
              ("Rounding step, INR a bottle", 5, "0"), ("Target MRP a bottle, for the reverse formula", 220, "0")]
    for i, (label, val, fmt) in enumerate(inputs, 4):
        w.cell(i, 1, label)
        c = w.cell(i, 2, val)
        c.fill, c.number_format = INPUT, fmt
    crit = (f'{R("B")},$B$9,{R("C")},"duty",{R("F")},"<"&$B$7,{R("G")},">="&$B$7,'
            f'{R("O")},"<="&$B$8,{R("Q")},">="&$B$8')
    fee_crit = (f'{R("B")},$B$9,{R("C")},"fee",{R("D")},"transport pass",'
                f'{R("O")},"<="&$B$8,{R("Q")},">="&$B$8')
    calc = [
        ("hL a case", "=B5*B6/100", "0.0000"),
        ("Bulk litres a case", "=B5*B6", "0.00"),
        ("DMC a case", "=ROUND(B4*B15,2)", INR),
        ("Duty rows in force for this state, strength and date", f"=COUNTIFS({crit})", "0"),
        ("Rate check", '=IF(B18=1,"one row in force","REFUSE: "&B18&" rows in force; name the gap")', "@"),
        ("Rate version", f'=IF(B18=1,INDEX(Rates!$A:$A,SUMIFS({R("R")},{crit})),"none")', "@"),
        ("Design", f'=IF(B18=1,INDEX(Rates!$H:$H,SUMIFS({R("R")},{crit})),"none")', "@"),
        ("Share of DMC", f"=SUMIFS({R('I')},{crit})", PCT),
        ("Floor, INR a bulk litre", f"=SUMIFS({R('J')},{crit})", "0.00"),
        ("Rate, INR a bulk litre (design B)", f"=SUMIFS({R('K')},{crit})", "0.00"),
        ("Rate, INR a litre of alcohol (design B2)", f"=SUMIFS({R('L')},{crit})", "0.00"),
        ("Transport pass fee, INR a bulk litre", f"=SUMIFS({R('M')},{fee_crit})", "0.00"),
        ("Excise a case", ('=IF(B18<>1,NA(),ROUND(IF(B21="A",B22*B17,IF(B21="B",B24*B16,'
                           'IF(B21="B2",B16*B7/100*B25,MAX(B22*B17,B23*B16)))),2))'), INR),
        ("Transport pass fee a case", "=ROUND(B26*B16,2)", INR),
        ("Landed price a case", "=ROUND(B17+B27+B28,2)", INR),
        ("Buyer margin a case", "=ROUND(B10*B29,2)", INR),
        ("Buyer's price a case", "=ROUND(B29+B30,2)", INR),
        ("Retailer margin a case", "=ROUND(B11*B31,2)", INR),
        ("Price before rounding a case", "=ROUND(B31+B32,2)", INR),
        ("Price before rounding a bottle", "=ROUND(B33/B5,2)", INR),
        ("MRP a bottle", "=CEILING(ROUND(B33/B5,6),B12)", INR),
        ("MRP a case", "=ROUND(B35*B5,2)", INR),
        ("Rounding kept by the retailer a case", "=ROUND(B36-B33,2)", INR),
        ("State share of MRP (excise and fee)", "=(B27+B28)/B36", "0.0%"),
        ("Floor bites below this DMC a case", '=IF(B22>0,ROUND(B23*B16/B22,2),"no share")', INR),
        ("Highest DMC a case for the target MRP", "=ROUND((B13*B5/((1+B10)*(1+B11))-B26*B16)/(1+B22),2)", INR),
        ("DMC a case at which the MRP drops one step (exclusive)", "=ROUND(((B13-B12)*B5/((1+B10)*(1+B11))-B26*B16)/(1+B22),2)", INR),
    ]
    for i, (label, f, fmt) in enumerate(calc, 15):
        w.cell(i, 1, label)
        c = w.cell(i, 2, f)
        c.number_format = fmt
    for r in (27, 35, 36):
        w.cell(r, 1).font = w.cell(r, 2).font = BOLD

    # The waterfall table of chapter 1.4
    w["D3"] = "Waterfall"
    w["D3"].font = BOLD
    for j, n in enumerate(["Step", "INR a case", "INR a bottle", "Share of MRP"], 4):
        cell = w.cell(4, j, n)
        cell.font, cell.fill = BOLD, HEAD
    steps = [("DMC", "=B17"), ("Excise", "=B27"), ("Transport pass fee", "=B28"), ("Buyer margin", "=B30"),
             ("Retailer margin", "=B32"), ("Rounding, kept by the retailer", "=B37"), ("MRP", "=SUM(E5:E10)")]
    for i, (s, f) in enumerate(steps, 5):
        w.cell(i, 4, s)
        w.cell(i, 5, f).number_format = INR
        w.cell(i, 6, f"=ROUND(E{i}/$B$5,2)").number_format = INR
        w.cell(i, 7, f"=E{i}/$E$11").number_format = PCT
    for c in "DEFG":
        w[f"{c}11"].font = BOLD
    w["D13"] = "Check: MRP from the waterfall equals MRP a case"
    w["E13"] = '=IF(ROUND(E11-B36,2)=0,"pass","FAIL")'
    widths(w, [52, 18, 3, 30, 14, 14, 13])
    w.freeze_panes = "A4"

    # Designs (chapter 5.2)
    d = wb.create_sheet("Designs", 1)
    d["A1"] = "The same beer under the four duty designs (chapter 5.2). Inputs come from the Walk sheet."
    d["A1"].font = BOLD
    header(d, 3, ["Design", "Rate version", "Rule", "Duty a case"])
    look = lambda rid, col: f'INDEX(Rates!${col}:${col},MATCH("{rid}",Rates!$A:$A,0))'
    rows = [("A: multiple of DMC", "SA-2026-04", "110 percent of DMC", f"=ROUND({look('SA-2026-04', 'I')}*Walk!B17,2)"),
            ("B: per bulk litre", "SB-2026-04", "INR 140 a bulk litre", f"=ROUND({look('SB-2026-04', 'K')}*Walk!B16,2)"),
            ("B2: per litre of alcohol", "SB2-2026-04", "INR 2,650 a litre of alcohol",
             f"=ROUND(Walk!B16*Walk!B7/100*{look('SB2-2026-04', 'L')},2)"),
            ("C: hybrid (State S)", "S-STRONG-2026-04", "larger of 110 percent of DMC and INR 50 a bulk litre",
             f"=ROUND(MAX({look('S-STRONG-2026-04', 'I')}*Walk!B17,{look('S-STRONG-2026-04', 'J')}*Walk!B16),2)")]
    for i, r in enumerate(rows, 4):
        for j, v in enumerate(r, 1):
            d.cell(i, j, v)
        d.cell(i, 4).number_format = INR
    d["A9"] = "Mild beer at the same DMC (S-MILD-2026-04)"
    d["D9"] = f"=ROUND(MAX({look('S-MILD-2026-04', 'I')}*Walk!B17,{look('S-MILD-2026-04', 'J')}*Walk!B16),2)"
    d["A10"] = "Strength cliff a case: strong less mild"
    d["D10"] = "=D7-D9"
    for c in ("D9", "D10"):
        d[c].number_format = INR
    widths(d, [40, 18, 50, 14])

    # DMC loop (chapter 6.5)
    lp = wb.create_sheet("DMC loop", 2)
    lp["A1"] = "MRP across a range of DMC values, same rules as the Walk sheet (chapter 6.5). Find the step: that is your cliff."
    lp["A1"].font = BOLD
    header(lp, 3, ["DMC a case", "Excise", "Landed", "Buyer's price", "Before rounding a case", "A bottle", "MRP a bottle"])
    for i, dmc in enumerate(range(940, 1061, 10), 4):
        lp.cell(i, 1, dmc).fill = INPUT
        lp.cell(i, 2, f"=ROUND(MAX(Walk!$B$22*A{i},Walk!$B$23*Walk!$B$16),2)")
        lp.cell(i, 3, f"=ROUND(A{i}+B{i}+Walk!$B$28,2)")
        lp.cell(i, 4, f"=ROUND(C{i}*(1+Walk!$B$10),2)")
        lp.cell(i, 5, f"=ROUND(D{i}*(1+Walk!$B$11),2)")
        lp.cell(i, 6, f"=ROUND(E{i}/Walk!$B$5,2)")
        lp.cell(i, 7, f"=CEILING(ROUND(E{i}/Walk!$B$5,6),Walk!$B$12)")
        for j in range(1, 8):
            lp.cell(i, j).number_format = INR
    lp["A18"] = "The loop uses design C (the State S rule) with the share, floor and fee the Walk sheet found."
    lp["A18"].font = NOTE
    widths(lp, [12, 12, 12, 14, 20, 10, 12])
    OUT.mkdir(exist_ok=True)
    wb.save(OUT / "duty-mrp-calculator.xlsx")


def template():
    wb = Workbook()
    wb.properties.creator = AUTHOR
    wb.properties.title = "Rate table template (Appendix B.4)"
    wb.properties.created = wb.properties.modified = datetime(2026, 11, 3)
    t = wb.active
    t.title = "Template"
    t["A1"] = "Rate table template: one row for one rule, one state, one band and one period (chapters 5.6, 13.1; Appendix B.4)"
    t["A1"].font = Font(bold=True, size=12)
    header(t, 3, ["Field", "What goes in it", "Example (State S, synthetic)", "Column in the data sheets"])
    fields = [
        ("state", "the state", "S", "state"),
        ("band", "strength band", "strong, above 5.0 up to 8.0 percent ABV", "band, abv_min, abv_max"),
        ("design", "duty design A, B, B2 or C", "C, hybrid: share of DMC or floor per bulk litre, higher wins", "design"),
        ("share", "share of DMC", "110 percent", "share"),
        ("floor", "floor per bulk litre", "INR 50", "floor_per_bl"),
        ("effective from", "the date the rule starts", "1 April 2026", "effective_from"),
        ("effective to", "the date it ends", "open until superseded", "effective_to (blank = open)"),
        ("notification", "number and date", "the public document", "notification"),
        ("link", "where the file sits; keep the file, its fetch date and its hash", "", "link"),
        ("source fetch date", "the date you read it", "", "source_fetch_date"),
        ("checked by, on", "a named person and a date", "", "checked_by, checked_on"),
        ("status", "confirmed, or to verify", "", "status"),
    ]
    for i, r in enumerate(fields, 4):
        for j, v in enumerate(r, 1):
            t.cell(i, j, v)
    notes = ["Fees get rows of their own: the fee, its amount and its unit (per bulk litre, per case, per consignment or per SKU a year).",
             "A rate you cannot find in public goes in as 'not found', never as a guess.",
             "Three habits: never overwrite a row; close it and open a new one. Store the source with the row. Mark an unconfirmed rate as such, in a visible field.",
             "Design B rates go in rate_per_bl; design B2 rates go in rate_per_lal (INR a litre of alcohol).",
             "The real state rows copy Appendix B.2 as printed. None is a confirmed rate to quote to a state office. Confirm every rate with the state excise office before you sign a price."]
    for i, n in enumerate(notes, 18):
        t.cell(i, 1, n).font = NOTE
    widths(t, [18, 55, 55, 30])

    sheets = [("State S (synthetic)", "rate_table_state_s.csv"),
              ("State S, 13.1 change", "rate_table_state_s_oct_change.csv"),
              ("Real states (as printed)", "rate_table_real_states.csv")]
    for title, f in sheets:
        ws = wb.create_sheet(title)
        write_rates(ws, pd.read_csv(DATA / f), first=3, with_checks=True)
        ws["A1"] = "Synthetic State S rows: they match no real state." if "State S" in title else (
            "Copied from Appendix B.2 as printed, with source and date. Blank means the book prints nothing. "
            "Status 'not found' means no public source was found. Not used by the calculator. Not legal or tax advice.")
        ws["A1"].font = NOTE

    c = wb.create_sheet("Checks", 1)
    c["A1"] = "The five checks, run at load time (chapter 13.4)"
    c["A1"].font = Font(bold=True, size=12)
    c["A3"], c["B3"] = "Today (for the expiry check)", datetime(2026, 11, 3)
    c["B3"].number_format, c["B3"].fill = DATE, INPUT
    header(c, 5, ["Check", "Fails when", "State S (synthetic)", "State S, 13.1 change", "Where it runs"])
    s1, s2 = "'State S (synthetic)'", "'State S, 13.1 change'"
    rows = [
        ("Rate exists", "no row covers the state, band and date", "see the Walk sheet of the calculator", "", "duty-mrp-calculator.xlsx, Walk!B19; notebooks ch04 and ch13"),
        ("No gap, no overlap", "two rows cover one date or none does",
         f'=IF(COUNTIF({s1}!Z:Z,">1")=0,"no overlap","FAIL")', f'=IF(COUNTIF({s2}!Z:Z,">1")=0,"no overlap","FAIL")',
         "overlaps column here; gaps day by day in notebook ch13"),
        ("Recompute", "the duty charged differs from the larger of rate x DMC and floor x bulk litres by more than a paisa",
         "", "", "notebooks ch04 and ch13, against data/dispatches_state_s.csv"),
        ("Band", "ABV and band disagree", "", "", "notebook ch13"),
        ("Expiry", "a row has had no check for 90 days",
         f'=IF(COUNTIF({s1}!AB:AB,"FAIL")=0,"pass",COUNTIF({s1}!AB:AB,"FAIL")&" rows FAIL")',
         f'=IF(COUNTIF({s2}!AB:AB,"FAIL")=0,"pass",COUNTIF({s2}!AB:AB,"FAIL")&" rows FAIL")',
         "expiry check column here; notebook ch13"),
    ]
    for i, r in enumerate(rows, 6):
        for j, v in enumerate(r, 1):
            c.cell(i, j, v).alignment = Alignment(wrap_text=True, vertical="top")
    widths(c, [22, 50, 22, 22, 50])
    wb.save(OUT / "rate-table-template.xlsx")


if __name__ == "__main__":
    calculator()
    template()
    print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.xlsx"))))
