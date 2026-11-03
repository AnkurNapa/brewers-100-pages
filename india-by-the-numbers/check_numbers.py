"""Asserts that every number the book prints from this data comes out of it.

It runs each notebook's code cells top to bottom (plots go to a dummy
backend) and checks the results to the precision the book prints.
Run make_data.py first, then: python3 check_numbers.py
"""
import json
import math
import os
import warnings
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib

matplotlib.use("Agg")
warnings.filterwarnings("ignore", message=".*non-interactive.*")
import matplotlib.pyplot as plt

import calculator as calc
from calculator import r2

HERE = Path(__file__).resolve().parent
NB = HERE / "notebooks"
failures = []


def run(name):
    """Execute a notebook's code cells in one namespace, from the notebooks folder."""
    cells = json.loads((NB / f"{name}.ipynb").read_text())["cells"]
    ns = {"__name__": "__main__"}
    old = os.getcwd()
    os.chdir(NB)
    try:
        with redirect_stdout(StringIO()):
            for c in cells:
                if c["cell_type"] == "code":
                    exec(compile("".join(c["source"]), name, "exec"), ns)
                    plt.close("all")
    finally:
        os.chdir(old)
    return ns


def near(label, got, want, tol=1.0):
    """Totals the book adds from lines rounded to the rupee: within INR 1 (chapter 10.4 says so)."""
    if abs(float(got) - float(want)) > tol:
        failures.append(f"{label}: got {got}, book prints {want}")


def eq(label, got, want, dp=2):
    if round(float(got), dp) != round(float(want), dp):
        failures.append(f"{label}: got {got}, book prints {want}")


def check_calculator():
    base = calc.load_rates()
    w = calc.walk(982.80, rates=base)
    for label, got, want in [("DMC", w.dmc, 982.80), ("excise", w.duty, 1081.08), ("fee", w.fee, 15.60),
                             ("landed", w.landed, 2079.48), ("wholesaler margin", w.buyer_margin, 166.36),
                             ("wholesaler price", w.buyer_price, 2245.84), ("retailer margin", w.retail_margin, 336.88),
                             ("before rounding", w.pre_round, 2582.72), ("bottle before rounding", w.pre_round_bottle, 215.23),
                             ("MRP bottle", w.mrp_bottle, 220), ("MRP case", w.mrp_case, 2640.00),
                             ("rounding", w.rounding, 57.28), ("duty plus fee", w.duty + w.fee, 1096.68)]:
        eq(f"ch6.4 {label}", got, want)
    eq("ch1.4 state share percent", w.state_share * 100, 41.5, 1)
    for label, case, want in [("DMC", w.dmc, 81.90), ("excise", w.duty, 90.09), ("fee", w.fee, 1.30),
                              ("wholesaler", w.buyer_margin, 13.86), ("retailer", w.retail_margin, 28.07),
                              ("rounding", w.rounding, 4.77), ("wholesaler price", w.buyer_price, 187.15),
                              ("landed", w.landed, 173.29)]:
        eq(f"ch1.4 {label} a bottle", r2(case / 12), want)
    for label, case, want in [("DMC", w.dmc, 37.23), ("excise", w.duty, 40.95), ("fee", w.fee, 0.59),
                              ("wholesaler", w.buyer_margin, 6.30), ("retailer", w.retail_margin, 12.76),
                              ("rounding", w.rounding, 2.17)]:
        eq(f"ch1.4 {label} share", case / w.mrp_case * 100, want)
    eq("ch1.4 excise and fee a bottle", r2((w.duty + w.fee) / 12), 91.39)
    eq("ch1.4 margin share", 315.60 / 2640 * 100, 12.0, 1)
    eq("ch1.4 trade margin share", (w.buyer_margin + w.retail_margin) / w.mrp_case * 100, 19.1, 1)
    eq("ch1.4 trade keeps", (w.buyer_margin + w.retail_margin + w.rounding) / w.mrp_case * 100, 21.2, 1)
    eq("ch6.4 USD MRP", 220 / 90, 2.44)
    # Reverse formula (6.2) and Route C (6.3, 7.5)
    eq("ch6.2 reverse at 220", (220 / 1.242 - 1.30) / 2.10, 83.73)
    eq("ch6.2 reverse at 215", (215 / 1.242 - 1.30) / 2.10, 81.81)
    eq("ch6.2 reverse case", calc.reverse_dmc(220), 1004.76)
    eq("ch6.2 edge gap", 81.90 - (215 / 1.242 - 1.30) / 2.10, 0.0867, 4)
    eq("ch6.2 edge a hL", (81.90 - (215 / 1.242 - 1.30) / 2.10) / 0.0065, 13.34)
    eq("ch6.2 shelf a rupee", 2.10 * 1.242, 2.61)
    for f, pre, mrp in [(1.05, 225.91, 230), (0.95, 204.55, 205)]:
        wf = calc.walk(r2(982.80 * f), rates=base)
        eq(f"ch6.2 DMC x {f} before rounding", wf.pre_round_bottle, pre)
        eq(f"ch6.2 DMC x {f} MRP", wf.mrp_bottle, mrp)
    wc = calc.walk(982.80, rates=base, buyer=0.10)
    for label, got, want in [("corporation margin", wc.buyer_margin, 207.95), ("buyer price", wc.buyer_price, 2287.43),
                             ("retailer", wc.retail_margin, 343.11), ("before rounding", wc.pre_round, 2630.54),
                             ("bottle", wc.pre_round_bottle, 219.21), ("MRP", wc.mrp_bottle, 220),
                             ("rounding", wc.rounding, 9.46), ("price gap", wc.pre_round - w.pre_round, 47.82)]:
        eq(f"ch7.5 Route C {label}", got, want)
    eq("ch7.5 Route C ceiling", calc.reverse_dmc(220, buyer=0.10) / 12, 82.20)
    eq("ch7.5 Route C floor", calc.reverse_dmc(215, buyer=0.10) / 12, 80.31)
    eq("ch6.3 retailer keeps", w.retail_margin + w.rounding, 394.16)
    eq("ch6.3 bar keeps", 440 - 187.15, 252.85)
    eq("ch6.3 bar share", (440 - 187.15) / 440 * 100, 57.5, 1)
    eq("ch6.3 bar state share", 91.39 / 440 * 100, 20.8, 1)
    # Cash (3.4, 7.3)
    eq("ch3.4 carry 30", calc.carrying_cost(1096.68, 30), 10.82)
    eq("ch3.4 carry 60", calc.carrying_cost(1096.68, 60), 21.63)
    eq("ch7.3 carry A", calc.carrying_cost(1763.88, 30), 17.40)
    eq("ch7.3 carry C", calc.carrying_cost(1763.88, 60), 34.79)
    eq("ch7.3 cash out", 667.20 + 1096.68, 1763.88)
    cases_year = round(1000 * 12 / 0.078)
    eq("ch7.3 cases a year", cases_year, 153846, 0)
    # The book prints about 26,77,000 and 53,52,000: cases a year times the per case cost rounded to the paisa.
    eq("ch7.3 yearly carry A, thousand", cases_year * 17.40 / 1e3, 2677, 0)
    eq("ch7.3 yearly carry C, thousand", cases_year * 34.79 / 1e3, 5352, 0)
    eq("ch7.3 yearly margin", cases_year * 315.60, 48553798, 0)
    cases_month = round(1000 / 0.078)
    eq("ch7.3 month billed lakh", cases_month * 2079.48 / 1e5, 266.6, 1)
    eq("ch7.3 month duty lakh", cases_month * 1096.68 / 1e5, 140.6, 1)
    eq("ch7.2 registration a case", 25000 / 153846, 0.16)
    eq("ch8.4 TN fee share", 40 / 982.80 * 100, 4.1, 1)
    # Chapter 14.2 scenarios and chapter 15.1
    chg = calc.load_rates("rate_table_state_s_oct_change.csv")
    w120 = calc.walk(982.80, rates=chg, date="2026-10-15")
    eq("ch14.2 bottle at 120", w120.pre_round_bottle, 225.40)
    eq("ch14.2 MRP at 120", w120.mrp_bottle, 230)
    hold = r2((2640 / 1.242 - 15.60) / 2.2)
    eq("ch14.2 hold DMC", hold, 959.09)
    eq("ch14.2 DMC cut", 982.80 - hold, 23.71)
    eq("ch14.2 hold contribution", hold - 519.78, 439.31)
    eq("ch14.2 pass on monthly", 3840 * 463.02, 1777997, 0)
    eq("ch14.2 hold monthly", 4000 * 439.31, 1757240, 0)
    eq("ch14.2 base monthly", 4000 * 463.02, 1852080, 0)
    eq("ch14.2 gap", 3840 * 463.02 - 4000 * 439.31, 20757, 0)
    eq("ch14.2 volume fall", 4000 * (1 - 0.90 * 10 / 225), 3840, 0)
    eq("ch14.2 pack move", 500 * 65.50, 32750, 0)
    eq("ch14.4 mild pass short", 200 * 294.84, 58968, 0)
    eq("ch15.1 extra duty", 10000 * r2(0.10 * 982.80), 982800, 0)
    eq("ch10.2 plant duty a hL", 1096.68 / 0.078, 14060, 0)
    eq("ch10.2 ratio", 14060 / 3000, 4.7, 1)


def check_eval():
    import pandas as pd
    q = pd.read_csv(HERE / "eval" / "duty-eval-20.csv")
    if len(q) != 20:
        failures.append(f"eval has {len(q)} questions, not 20")
    want = {"Q01": 1081.08, "Q02": 786.24, "Q03": 354.55, "Q04": 2079.48, "Q05": 230}
    for k, v in want.items():
        eq(f"ch14.5 {k}", float(q.set_index("id").answer[k]), v)
    if q.set_index("id").answer["Q06"] != "REFUSE":
        failures.append("ch14.5 Q06 must be a refusal")


def check_notebooks():
    n = run("ch02-volume-price-mix")
    eq("ch2.1 FY2026 revenue crore", n["tot"].revenue_inr["FY2026"] / 1e7, 135, 2)
    eq("ch2.1 FY2026 hL", n["tot"].hl["FY2026"], 100000, 0)
    eq("ch2.6 volume growth", n["vol_growth"] * 100, 6.0, 1)
    eq("ch2.1 revenue growth", n["rev_growth"] * 100, 11.3, 1)
    eq("ch2.6 price mix", n["price_mix"] * 100, 5.0, 1)
    eq("ch2.4 Route C share", n["route_c_share"] * 100, 40, 0)
    eq("ch2.2 lager ratio", n["lager_ratio"], 1.16)
    eq("ch2.2 mix 5", n["mix5"], 3.75)
    eq("ch2.2 mix 5 percent", n["mix5"] / 190 * 100, 2.0, 1)
    eq("ch2.2 mix 20", n["mix20"], 15.00)
    eq("ch2.2 mix 20 percent", n["mix20"] / 190 * 100, 7.9, 1)

    n = run("ch03-duty-cash-by-week")
    eq("ch3.4 carry 30", n["carry_30"], 10.82)
    eq("ch3.4 carry 60", n["carry_60"], 21.63)
    eq("ch3.4 front 1,000", n["front_1000"], 1096680)

    n = run("ch04-star-schema")
    eq("ch4.2 cases", n["sep_cases"], 1000, 0)
    eq("ch4.2 hL", n["sep_hl"], 78, 1)
    eq("ch4.2 duty", n["sep_duty_due"], 1081080)
    eq("ch4.2 fee", n["sep_fee"], 15600)
    if len(n["flags"]) != 2:
        failures.append(f"ch4.4 expected 2 flagged rows, got {len(n['flags'])}")

    n = run("ch05-duty-calculator")
    d = list(n["designs"].values())
    for got, want in zip(d, [1081.08, 1092.00, 1095.51, 1081.08]):
        eq("ch5.2 design duty", got, want)
    eq("ch5.2.3 floor case", n["floor_case"], 390.00)
    eq("ch5.2.3 floor line", n["floor_line"], 354.55)
    eq("ch5.2.3 floor a litre", 50 / 1.10, 45.45)
    t = n["per_litre"]
    for col, want in [("A: 110 percent", [138.60, 97.02, 44.00]), ("C: larger of A and 50", [138.60, 97.02, 50.00])]:
        for got, w in zip(t[col], want):
            eq(f"ch5.2.3 {col}", got, w)
    eq("ch5.3 mild", n["mild"], 786.24)
    eq("ch5.3 cliff", n["cliff"], 294.84)
    eq("ch5.3 cliff share", n["cliff"] / n["strong"] * 100, 27.3, 1)
    eq("ch5.3 cliff bottle", n["cliff"] / 12, 24.57)
    eq("ch5.3 alcohol removed", 0.3 / 5.3 * 100, 5.7, 1)
    eq("ch5.4 duty a hL", n["strong"] / 0.078, 13860, 0)
    eq("ch5.5 registration 500 hL", 25000 / round(500 / 0.078), 3.90)
    eq("ch5.5 registration 50 hL", 25000 / round(50 / 0.078), 39.00)
    eq("ch1.4 margin", n["margin_over_delivered"], 315.60)
    if "refusal" not in n:
        failures.append("ch5 calculator did not refuse a date with no row")

    n = run("ch06-mrp-in-20-lines")
    eq("ch6.5 lager MRP", n["mrp"](982.80)[1], 220)
    eq("ch6.5 low", n["low"][0], 204.55)
    eq("ch6.5 high", n["high"][0], 225.91)
    eq("ch6.5 edge low", n["edge_low"], 81.81)
    eq("ch6.5 edge high", n["edge_high"], 83.73)

    n = run("ch09-cost-per-case")
    c = n["cpc"]
    book = {"beer": [224.64, 228.10, 228.10], "packaging": [246.00, 294.20, 322.40], "overhead": [147.42, 149.69, 149.69],
            "ex_works": [618.06, 671.99, 700.19], "ex_works_hl": [7923.85, 8484.72, 8840.78],
            "freight": [49.14, 49.90, 49.90], "delivered": [667.20, 721.89, 750.09], "dmc": [982.80, 997.92, 997.92],
            "contribution": [463.02, 425.72, 397.52], "margin": [315.60, 276.03, 247.83]}
    for col, vals in book.items():
        for got, want in zip(c[col], vals):
            eq(f"ch9.6 {col}", got, want)
    for got, want in zip(n["pack_share"], [39.8, 43.8, 46.0]):
        eq("ch9.6 packaging share", got, want, 1)
    for got, want in zip(n["usd_hl"], [88.04, 94.27, 98.23]):
        eq("ch9.5 USD a hL", got, want)
    eq("ch9.5 gap", n["gap_sku1"], 363.85)
    eq("ch9.2 malt a hL", n["malt_hl"], 1431)
    eq("ch9.2 stress a hL", n["stress_hl"], 286.20)
    eq("ch9.2 stress a case", n["stress_hl"] * 0.078, 22.32)
    eq("ch9.6 DMC over cost", c.dmc.SKU1 - c.ex_works.SKU1, 364.74)
    eq("ch9.6 can delivered", c.delivered.SKU3 - c.delivered.SKU1, 82.89)
    eq("ch9.6 can margin", c.margin.SKU1 - c.margin.SKU3, 67.77)
    eq("ch9.3 glass rise", 12 * 0.1 * 15.75, 18.90)
    eq("ch9.2 can stress", 24 * 0.15 * 12.60, 45.36)
    eq("ch9.2 can stress share", 45.36 / 700.19 * 100, 6.5, 1)

    n = run("ch10-brewpub")
    b = n["base"]
    eq("ch10.1 net a hL", b["beer_net"], 87909.09)
    eq("ch10.1 net a hL cast", b["beer_net"] * 675 / 750, 79118.18)
    eq("ch10.1 USD", b["beer_net"] / 90, 976.77)
    eq("ch10.1 glasses a day", n["glasses_year"] / 360, 568, 0)
    eq("ch10.4 var cast", b["var_cast"], 3849.50)
    eq("ch10.4 var sold", b["var_sold"], 4277.22)
    eq("ch10.4 food net", b["food_net"], 47619.05)
    eq("ch10.4 food contribution", b["food_contrib"], 30952.38)
    eq("ch10.4 contribution", b["contrib"], 114584.25)
    p = n["pnl"]
    for k, want in [("Beer sales before VAT", 61363636), ("Food sales before tax", 32142857), ("Excise", 2025000),
                    ("Beer variable cost", 2887125), ("Food cost", 11250000), ("Contribution", 77344369),
                    ("Fixed costs", 62642857), ("Profit before interest and tax", 14701512)]:
        near(f"ch10.4 {k}", p[k], want)
    eq("ch10.4 revenue", b["revenue"], 93506494, 0)
    eq("ch10.4 margin", b["profit"] / b["revenue"] * 100, 15.7, 1)
    near("ch10.4 beer contribution", n["beer_contrib"], 56451512)
    eq("ch10.3 depreciation", b["dep"], 10142857, 0)
    s = n["sens"]
    book_sens = [(114584.25, 547, 147.02), (105493.34, 594, 85.65), (123675.16, 507, 208.38), (108393.77, 578, 105.23),
                 (114584.25, 562, 129.02), (114084.36, 549, 143.64), (114332.65, 548, 102.44), (103724.25, 604, 73.71)]
    for (k, r), (c1, be, pr) in zip(s.iterrows(), book_sens):
        eq(f"ch10.6 {k} contribution", r["contribution a hL sold"], c1)
        eq(f"ch10.6 {k} break-even", r["break-even hL"], be, 0)
        eq(f"ch10.6 {k} profit", r["profit, lakh"], pr)
    eq("ch10.6 with hurdle, whole hL needed", n["breakeven_with_hurdle"], 631, 0)
    eq("ch10.6 payback", n["payback"], 3.2, 1)
    eq("ch10.5 ratio", b["beer_net"] / 12600, 7.0, 1)

    n = run("ch11-sku-case")
    b = n["base"]
    eq("ch11.4 undiscounted", b["total"], 25855769, 0)
    eq("ch11.4 NPV lakh", b["npv"] / 1e5, 199.58)
    eq("ch11.4 worst lakh", b["worst"] / 1e5, -37.5, 1)
    eq("ch11.4 positive month", b["positive_month"], 13, 0)
    book_t = {"Volume, steady state": (141.28, 257.87), "Glass price": (171.18, 227.97), "Listing delay": (175.89, 215.74),
              "Duty, with elasticity of minus 1": (188.51, 210.68), "Route": (189.39, None)}
    for k, (lo, hi) in book_t.items():
        eq(f"ch11.4 {k} low", n["tornado"].loc[k, "low"], lo)
        if hi:
            eq(f"ch11.4 {k} high", n["tornado"].loc[k, "high"], hi)
    eq("ch11.4 stacked", n["stacked"]["npv"] / 1e5, 98.52)
    eq("ch11.4 stacked worst", n["stacked"]["worst"] / 1e5, -54.1, 1)
    eq("ch11.5 Route C worst (reconcile prints 59.65)", n["route_c"]["worst"] / 1e5, -59.65)
    eq("ch11.5 loaded NPV", n["loaded"]["npv"] / 1e5, 122.06)
    eq("ch11.4 duty without elasticity", (b["npv"] - n["duty_no_elasticity"]["npv"]) / 1e5, 0.49)
    eq("ch11.5 zero NPV hL", n["zero_npv_hl"], 288, 0)
    eq("ch11.5 zero NPV share", n["zero_npv_hl"] / 2000 * 100, 14, 0)
    eq("ch11.5 zero NPV loaded", n["zero_npv_loaded_hl"], 432, 0)
    eq("ch11.3 cases a month", n["per_month"], 2136.75)
    eq("ch11.3 funding A", n["funding_a"], 15.94)
    eq("ch11.3 funding C", n["funding_c"], 31.89)
    eq("ch11.3 tied A lakh", n["per_month"] * 1616.46 / 1e5, 34.5, 1)
    eq("ch11.3 tied C lakh", 2 * n["per_month"] * 1616.46 / 1e5, 69.1, 1)
    eq("ch11.3 month contribution lakh", n["per_month"] * 463.02 / 1e5, 9.89)
    eq("ch11.3 duty share of cash", 1096.68 / 1616.46 * 100, 68, 0)
    for got, want in zip(n["contrib_hl"].values(), [5936.15, 5375.25, 5019.19]):
        eq("ch11.1 contribution a hL", got, want)
    eq("ch11.1 moved hL", n["contrib_hl"]["650 ml bottle"] - n["contrib_hl"]["330 ml bottle"], 560.90)
    eq("ch11.1 tank days", 4650 * 0.02, 93, 0)
    eq("ch11.2 contribution share", 463.02 / 2640 * 100, 17.5, 1)
    eq("ch11.4 glass swing share", 54 / 463.02 * 100, 11.7, 1)

    n = run("ch12-price-ladder")
    lad = n["ladder"]
    for i, (dmc, mrp, ratio, litre, contrib) in enumerate([(982.80, 220, 1.16, 338.46, 463.02), (1193.40, 265, 1.39, 407.69, 673.62),
                                                           (1263.60, 280, 1.47, 430.77, 743.82)]):
        r = lad.iloc[i]
        eq("ch12.1 DMC", r.dmc, dmc); eq("ch12.1 MRP", r.mrp, mrp); eq("ch12.1 ratio", r.vs_anchor, ratio)
        eq("ch12.1 a litre", r.mrp_litre, litre); eq("ch12.4 contribution", r.contribution, contrib)
        if r.band != "premium":
            failures.append(f"ch12.1 band {r.band}")
    eq("ch12.2 330 bottle", lad.iloc[3].before_rounding, 109.27)
    eq("ch12.2 330 MRP", lad.iloc[3].mrp, 110)
    eq("ch12.2 330 a litre", lad.iloc[3].mrp_litre, 333.33)
    eq("ch12.1 shelf a rupee", n["shelf_per_rupee"], 2.61)
    eq("ch12.2 mild bottle", n["mild"].pre_round_bottle, 184.71)
    eq("ch12.2 mild MRP", n["mild"].mrp_bottle, 185)
    eq("ch12.2 mild ceiling", n["mild_ceiling"], 1172.22)
    eq("ch12.2 headroom", n["mild_ceiling"] - 982.80, 189.42)
    eq("ch12.4 trade up", n["trade_up"], 280.80)
    eq("ch12.4 can loss", n["can_loss"], 65.50)
    eq("ch12.4 cases pale, whole cases", math.ceil(25000 / 743.82), 34, 0)
    eq("ch12.4 cases switched, whole cases", math.ceil(25000 / 280.80), 90, 0)
    eq("ch12.3 elasticity", n["elasticity"], -0.90)

    n = run("ch13-rate-table-checks")
    eq("ch13.1 30 Sep", n["sep30"], 1081.08)
    eq("ch13.1 1 Oct", n["oct1"], 1179.36)
    eq("ch13.1 difference", n["oct1"] - n["sep30"], 98.28)
    eq("ch13.4 short 1,000", n["short_1000"], 294840)
    eq("ch13.2 closing", n["closing"], 3200, 0)
    eq("ch13.2 cover", n["cover_days"], 20, 0)
    eq("ch13.2 ratio", n["sell_in_ratio"], 1.25)
    gaps = [round(r[3], 2) for r in n["recompute"]]
    if len(gaps) != 2 or 58968.00 not in gaps:
        failures.append(f"ch13.4 recompute flags {n['recompute']}")
    if len(n["bands"]) != 1 or n["missing"] or n["gaps"]:
        failures.append("ch13.4 checks on the clean data did not behave")

    n = run("ch14-retrieval")
    if n["chunks"].file.nunique() != 5:
        failures.append("ch14.3 expected five circulars")
    if not n["ask"]("What is the excise rate on cider and perry?").startswith("No clause found"):
        failures.append("ch14.3 retrieval should find no clause for cider")
    if "S/EXC/2026/09" not in n["ask"]("When does the amendment on strong beer come into force?"):
        failures.append("ch14.3 retrieval missed the revision notice")


if __name__ == "__main__":
    check_calculator()
    check_eval()
    check_notebooks()
    if failures:
        print("\n".join(failures))
        raise SystemExit(f"{len(failures)} numbers do not match the book")
    print("check_numbers: every number matches the book")
