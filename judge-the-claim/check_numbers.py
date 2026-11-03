"""Asserts that every number the book prints from this data comes out of it.

Run after make_data.py and make_sheets.py: python3 check_numbers.py
"""
import math
from decimal import ROUND_HALF_UP, Decimal
import os
import re

import numpy as np
import pandas as pd
from openpyxl import load_workbook

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda name: pd.read_csv(os.path.join(HERE, "data", name))
CHECKS = 0


def eq(got, want, places=0, what=""):
    global CHECKS
    CHECKS += 1
    half_up = lambda x: Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-places), ROUND_HALF_UP)
    assert half_up(got) == half_up(want), f"{what}: got {got}, book prints {want}"


# Data: the loss records (chapters 2 and 7)
m = D("kestrel_monthly_loss.csv")
eq(m["cast_hL"].sum(), 104500, what="wort cast a year")
eq(100 * m["lost_hL"].sum() / m["cast_hL"].sum(), 2.4, 1, "twelve month loss rate")
q = m.tail(3)
eq(q["cast_hL"].sum(), 27000, what="quarter cast")
eq(q["lost_hL"].sum(), 648, what="quarter lost")
for (_, r), cast, lost, rate in zip(q.iterrows(), (8000, 9500, 9500), (200, 228, 220), (2.5, 2.4, 2.3)):
    eq(r["cast_hL"], cast, what="month cast")
    eq(r["lost_hL"], lost, what="month lost")
    eq(r["loss_rate_pct"], rate, 1, "month rate")
eq(4 * q["cast_hL"].sum(), 108000, what="four quarters")
mi = m.set_index("month")
summer = mi.loc[["2026-06", "2026-07"]]
winter = mi.loc[["2025-12", "2026-01"]]
eq(100 * summer["lost_hL"].sum() / summer["cast_hL"].sum(), 2.8, 1, "summer rate")
eq(100 * winter["lost_hL"].sum() / winter["cast_hL"].sum(), 2.0, 1, "winter rate")
w = D("weekly_loss_sheet.csv")
eq(w["loss_rate_pct"].max(), 3.6, 1, "bad week")
wm = w.groupby("month")[["cast_hL", "lost_hL"]].sum().round(1)
assert (wm["cast_hL"].values == m["cast_hL"].values).all() and (wm["lost_hL"].values == m["lost_hL"].values).all()
eq(100 * (3.6 - 2.4) / 3.6, 33, 0, "bad week cut")

# Data: fill records and the pilot (chapters 11 and 12)
f = D("fill_records.csv")
f["side"] = f["tank"].str[2:].astype(int) % 2
pairs = f.pivot_table(index=["pair", "cycle"], columns="side", values="loss_pct")
eq(f["loss_pct"].mean(), 2.4, 1, "lager fill mean")
eq(f["loss_pct"].std(), 0.6, 1, "single fill spread")
eq((pairs[1] - pairs[0]).std(), 0.4, 1, "pair gap spread")
eq(f["tank"].nunique(), 12, what="lager fermenters")
g = D("pilot_pair_gaps.csv")
first = g[g["phase"] == "first_look"]
eq(len(first), 12, what="first look pair gaps")
eq(len(g), 24, what="pair gaps after the extension")
eq(first.groupby("pair")["gap_points"].mean().mean(), 0.41, 2, "first look result")
eq(g["gap_points"].mean(), 0.44, 2, "result after extension")

# Data: anonymised counts (chapters 1, 3, 4, 6, 10)
c = D("vendor_counts.csv").set_index("measure")["count"]
for name, want in [("Beer AI vendors at shipping or pilot stage", 116), ("Sell to breweries", 95),
                   ("Make a quantified claim", 50), ("Offer a calculator", 14),
                   ("Explain any part of how savings are worked out", 23),
                   ("Of those 23 also make a quantified claim", 20), ("Of those 3 also make a quantified claim", 2),
                   ("Offer a guarantee or pilot or trial", 22), ("Tie the price to the result", 3),
                   ("Publish a price", 13), ("Price on request", 49)]:
    eq(c[name], want, what=name)
eq(c["Make a quantified claim"] - c["Of those 23 also make a quantified claim"], 30, what="numbers with no working")
assert list(D("vendor_counts.csv").columns) == ["measure", "count"] and len(c) == 12, "counts table must hold counts only"

# Data: the chapter 4.4 scores and chapter 5 templates
s = D("ch04_scores.csv")
own = s[s["scorer"] == "owner"].groupby("claim")["point"].sum()
eq(own["A"], 0, what="claim A")
eq(own["B"], 2, what="claim B")
eq(own["C"], 6, what="claim C")
st = D("ch05_filler_stops.csv")
eq(st["duration_s"].sum() / 3600, 62, 1, "coded stops hours")
eq(st.loc[st["logged_by_operator"] == 1, "duration_s"].sum() / 3600, 40, 1, "logged hours")
eq(len(D("ch05_seeded_packs.csv")), 200, what="seeded packs")
eq(len(D("ch05_copilot_test_set.csv")), 50, what="question set")

# Model: the vendor case (chapters 1 to 10, series bible v4)
inp = D("kestrel_inputs.csv").set_index("item")["value"]
vol, rate, share = inp["volume_hL_a_year"], inp["cellar_loss_rate"], inp["share_recovered_claim"]
rec = vol * rate * share
lic, cloud = 12 * inp["licence_usd_a_month"], 12 * inp["cloud_bill_usd_a_month"]
for got, want in [(vol * rate, 2400), (rec, 480), (rec * 150, 72000), (rec * 30, 14400), (rec * 110, 52800),
                  (rec / 2 * 30, 7200), (lic, 16800), (cloud, 3000), (rec * 150 - lic - cloud, 52200),
                  (rec * 30 - lic - cloud, -5400), (rec * 110 - lic - cloud, 33000), (2400 * 30, 72000),
                  (52800 * 0.45, 23760), (23760 - 19800, 3960), (14400 * 0.45, 6480),
                  (14400 * 0.625, 9000), (52800 * 0.625, 33000)]:
    eq(got, want, what="vendor case")
eq(100 * 52200 / 72000, 73, 0, "net share of headline")
eq(100 * 19800 / 52800, 37.5, 1, "fee break even share")
eq(0.5 / 2.4, 0.208, 3, "ceiling")
# chapter 4.4 claim C and B
eq(7200 * 9 / 12 - 6000, -600, what="claim C conservative")
eq(14400 * 9 / 12 - 6000, 4800, what="claim C base")
eq(12 * 1500, 18000, what="claim B")
# chapter 5 and 6
eq(36000 * 0.005, 180, what="false rejects")
eq(62 * 0.25, 15.5, 1, "downtime cut")
eq(10 * 52 * 40, 20800, what="copilot hours")
eq(2400 * 0.80, 1920, what="up to 80")

# Whole cost and the monthly model (chapters 8 and 9)
people1, people_n = (13 * 4 + 39) * 40, 52 * 40
y1 = lic + cloud + 6000 + 6000 + people1
later = lic + cloud + people_n
total = y1 + 2 * later
for got, want in [(people1, 3640), (people_n, 2080), (y1, 35440), (later, 21880), (total, 79200),
                  (total + 1500, 80700), (rec * 110 * 2.625, 138600), (14400 * 2.625 - total, -41400),
                  (later / 30, 729), (480 * (30 + 80 * 0.41) * 2.625, 79128)]:
    eq(got, want, what="whole cost")
eq(100 * later / 14400, 152, 0, "steady break even at 30")
eq(100 * later / 52800, 41, 0, "steady break even at 110")
eq(100 * total / 138600, 57, 0, "three year break even")


def cash(p, value):
    out = []
    for mth in range(37):
        earned = 0 if mth <= 3 else (0.5 * (mth - 3) if mth <= 6 else 1.5 + (mth - 6))
        out.append(rec * value * p / 12 * earned - (15640 + 1650 * mth + people_n / 12 * max(0, mth - 12)))
    return out


for p, a, b, cm, pay in [(0.25, -18280, -8680, -44550, None), (0.45, -15400, 1880, -16830, None),
                         (0.70, -11800, 15080, 17820, 22), (1.00, -7480, 30920, 59400, 13)]:
    sr = cash(p, 110)
    eq(rec * 30 * p - later, a, what=f"steady at 30, p {p}")
    eq(rec * 110 * p - later, b, what=f"steady at 110, p {p}")
    eq(sr[36], cm, what=f"month 36, p {p}")
    assert next((mm for mm, v in enumerate(sr) if mm > 0 and v >= 0), None) == pay, f"payback p {p}"
    CHECKS += 1
eq(cash(1.0, 30)[36], -41400, what="replacement cost month 36")


def steady(v=vol, r=rate, sh=share, val=110, p=0.45, li=lic):
    return v * r * sh * val * p - (li + cloud + people_n)


for got, want in [(steady(p=0.36), -2872), (steady(p=0.54), 6632), (steady(val=30), -15400),
                  (steady(sh=0.10), -10000), (steady(sh=0.5 / 2.4), 2870), (steady(r=0.020), -2080),
                  (steady(r=0.028), 5840), (steady(v=90000), -496), (steady(v=110000), 4256),
                  (steady(li=13440), 5240), (steady(li=20160), -1480), (steady(p=0.54) - steady(), 4752)]:
    eq(got, want, what="sensitivity")

# Pricing (chapter 10)
for got, want in [(1190 * 36, 42840), (16800 * 3, 50400), (50400 - 42840, 7560), (1190 * 24, 28560)]:
    eq(got, want, what="multi year")
for hl, fixed, fee, net in [(100, -5800, 3630, 7370), (300, 16200, 10890, 22110), (480, 36000, 17424, 35376)]:
    eq(hl * 110 - 16800, fixed, what="fixed fee net")
    eq(hl * 110 * 0.33, fee, what="outcome fee")
    eq(hl * 110 - round(hl * 110 * 0.33), net, what="outcome net")

# Pilot lines (chapters 11 and 12)
be = total / (110000 * 2.625)
se = 0.4 / math.sqrt(2) / math.sqrt(6)
eq(21880 / 30000, 0.73, 2, "steady break even points")
eq(be, 0.27, 2, "three year break even points")
eq(300 * 110 * 2.625, 86625, what="kill line over three years")
eq(0.4 / math.sqrt(2), 0.28, 2, "pair figure spread")
eq(se, 0.115, 3, "standard error")
eq(2 * se, 0.23, 2, "noise margin")
eq(8 * 0.16 / 0.2304, 5.6, 1, "Lehr full claim")
eq(8 * 0.16 / 0.18 ** 2, 40, 0, "Lehr kill line")
for x, units in [(0.12, -1.6), (0.41, 1.0), (0.56, 2.3)]:
    eq((x - 0.3) / 0.115, units, 1, "noise units")
for got, want in [(440 * 30, 13200), (440 * 110, 48400), (round(8330 * 0.004), 33), (9 * 110 + 18 * 30, 1530),
                  (1530 - 21880 / 12, -293)]:
    eq(got, want, what="chapter 12")
eq(100 * 0.4 / 0.48, 83, 0, "line one share")
eq(100 * 27 / 33, 82, 0, "share banked")

rng = np.random.default_rng(1203)
for true_gap, stop_w, first_w, pass_w in [(0.48, 0.06, 1 / 3, 0.94), (0.15, None, None, 0.02), (0.27, None, None, 0.25)]:
    gp = rng.normal(true_gap, 0.4, size=(200_000, 24))
    fl, fn = gp[:, :12].mean(axis=1), gp.mean(axis=1)
    passed = (fl >= 0.53) | ((fl >= 0.3) & (fl < 0.53) & (fn >= 0.3))
    if stop_w:
        assert abs((fl < 0.3).mean() - stop_w) < 0.005 and abs((fl >= 0.53).mean() - first_w) < 0.01
    assert abs(passed.mean() - pass_w) < 0.015, f"simulated pass at {true_gap}: {passed.mean()}"
    CHECKS += 1

# Rupees and euros (chapter 7.4 and Appendix B.3)
for usd, inr, eur in [(72000, 6480000, 65500), (14400, 1296000, 13100), (-16800, -1512000, -15300),
                      (-3000, -270000, -2700), (-5400, -486000, -4900), (33000, 2970000, 30000)]:
    eq(usd * 90, inr, what="rupees")
    eq(round(usd / 1.1, -2), eur, what="euros")
eq(-5400 * 94.91, -512514, what="live rupees")
eq(round(-5400 / 1.12, -2), -4800, what="live euros")


# Spreadsheets: evaluate every formula and compare with the Kestrel figure beside it
def evaluate(wb):
    cache = {}

    def val(sheet, ref):
        key = (sheet, ref)
        if key not in cache:
            v = wb[sheet][ref].value
            cache[key] = calc(sheet, v[1:]) if isinstance(v, str) and v.startswith("=") else v
        return cache[key]

    def rng_vals(sheet, a, b):
        return [val(sheet, f"{a[0]}{r}") for r in range(int(a[1:]), int(b[1:]) + 1)]

    def calc(sheet, f):
        f = f.replace("_xlfn.", "").replace("^", "**").replace("<>", "!=")
        f = re.sub(r"(?<![<>!=])=(?!=)", "==", f)

        def ranges(mm):
            sh = mm.group(1) or sheet
            return f"[{', '.join(repr(x) for x in rng_vals(sh, mm.group(2), mm.group(3)))}]"
        f = re.sub(r"(?:(\w+)!)?\$?([A-Z]\$?\d+):\$?([A-Z]\$?\d+)", lambda mm: ranges(mm).replace("$", ""), f)
        f = re.sub(r"(?:(\w+)!)?\$?\b([A-Z])\$?(\d+)\b",
                   lambda mm: repr(val(mm.group(1) or sheet, mm.group(2) + mm.group(3))), f)
        f = f.replace("STDEV.S", "STDEVS")
        env = {"IF": lambda a, b, c: b if a else c, "ROUND": lambda x, n: round(x, int(n)),
               "ROUNDUP": lambda x, n: math.ceil(x * 10 ** n - 1e-9) / 10 ** n, "SQRT": math.sqrt,
               "ABS": abs, "SUM": sum, "AVERAGE": lambda xs: sum(xs) / len(xs),
               "STDEVS": lambda xs: float(np.std(xs, ddof=1))}
        env["__builtins__"] = {}
        # Only formulas written by make_sheets.py reach here; builtins are switched off.
        return eval(f, env)
    return val


def places(want):
    return 0 if isinstance(want, int) else len(str(want).split(".")[1])


wb = load_workbook(os.path.join(HERE, "sheets", "claim-rebuild-template.xlsx"))
v = evaluate(wb)
for row in range(1, 33):
    want = wb["Rebuild"][f"D{row}"].value
    if want is None:
        continue
    got = v("Rebuild", f"B{row}")
    if isinstance(want, str):
        assert got == want, f"Rebuild B{row}"
        CHECKS += 1
    else:
        eq(got, want, places(want), f"Rebuild B{row}")
for r in range(2, 6):
    for col, book in zip("CDE", "FGH"):
        eq(v("Check values", f"{col}{r}"), wb["Check values"][f"{book}{r}"].value, what=f"Check values {col}{r}")
for r, (fixed, fee, net) in zip((12, 13, 14), [(-5800, 3630, 7370), (16200, 10890, 22110), (36000, 17424, 35376)]):
    eq(v("Pricing", f"C{r}"), fixed, what="Pricing fixed")
    eq(v("Pricing", f"D{r}"), fee, what="Pricing fee")
    eq(v("Pricing", f"E{r}"), net, what="Pricing net")
eq(v("Pricing", "B6"), 7560, what="Pricing saved")
eq(v("Pricing", "B7"), 28560, what="Pricing owed")

wb = load_workbook(os.path.join(HERE, "sheets", "pilot-lines.xlsx"))
v = evaluate(wb)
for row in range(1, 18):
    want = wb["Lines"][f"C{row}"].value
    eq(v("Lines", f"B{row}"), want, places(want), f"Lines B{row}")
eq(v("Read the result", "B9"), 0.41, 2, "pilot sheet result")
assert v("Read the result", "B11") == "Extend once"
CHECKS += 1

wb = load_workbook(os.path.join(HERE, "sheets", "working-score-sheet.xlsx"))
v = evaluate(wb)
eq(v("Working Score", "C10"), 6, what="score sheet claim C")
assert v("Working Score", "C11") == "Worth a pilot" and v("Working Score", "C12") == "No"
CHECKS += 1

print(f"All {CHECKS} checks pass.")
