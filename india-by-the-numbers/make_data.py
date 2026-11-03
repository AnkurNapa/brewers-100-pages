"""Writes every CSV in data/, the five synthetic circulars and the chapter 14.5 eval set.

Fixed seeds, so every run gives the same files. Every figure is synthetic:
Kestrel Brewing and State S match no real brewery or state. The one
exception is data/rate_table_real_states.csv, which copies only the real
rates the book prints in Appendix B.2, with their source and date.
Run: python3 make_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SEED = 2026

RATE_COLS = ["row_id", "state", "kind", "item", "band", "abv_min", "abv_max", "design",
             "share", "floor_per_bl", "rate_per_bl", "rate_per_lal", "fee_amount", "fee_unit",
             "effective_from", "effective_to", "notification", "link", "source_fetch_date",
             "checked_by", "checked_on", "status", "note"]

SYN = dict(source_fetch_date="2026-04-01", checked_by="rate owner (synthetic)",
           checked_on="2026-10-01", status="synthetic")


def row(**kw):
    base = {c: None for c in RATE_COLS}
    base.update(SYN)
    base.update(kw)
    return base


def state_s_rows():
    """State S as the book teaches it (chapters 5 and 6), open until superseded."""
    n1 = "State S Excise Notification S/EXC/2026/01 of 15 March 2026 (synthetic)"
    return [
        row(row_id="S-STRONG-2026-04", state="S", kind="duty", item="beer", band="strong",
            abv_min=5.0, abv_max=8.0, design="C", share=1.10, floor_per_bl=50,
            effective_from="2026-04-01", notification=n1, link="data/circulars/c1-beer-duty.txt",
            note="larger of 110 percent of DMC and INR 50 a bulk litre"),
        row(row_id="S-MILD-2026-04", state="S", kind="duty", item="beer", band="mild",
            abv_min=0.0, abv_max=5.0, design="C", share=0.80, floor_per_bl=40,
            effective_from="2026-04-01", notification=n1, link="data/circulars/c1-beer-duty.txt",
            note="larger of 80 percent of DMC and INR 40 a bulk litre; up to 5.0 percent is mild"),
        row(row_id="S-FEE-PASS-2026-04", state="S", kind="fee", item="transport pass",
            band="all", abv_min=0.0, abv_max=8.0, fee_amount=2.0, fee_unit="INR a bulk litre",
            effective_from="2026-04-01",
            notification="State S Excise Circular S/EXC/2026/02 (synthetic)",
            link="data/circulars/c2-transport-pass.txt"),
        row(row_id="S-FEE-REG-2026-04", state="S", kind="fee", item="label registration",
            band="all", abv_min=0.0, abv_max=8.0, fee_amount=25000.0, fee_unit="INR a SKU a year",
            effective_from="2026-04-01",
            notification="State S Excise Circular S/EXC/2026/03 (synthetic)",
            link="data/circulars/c3-label-registration.txt", note="paid before the first dispatch"),
        # Teaching rows for the other designs of chapter 5.2, same beer.
        row(row_id="SA-2026-04", state="S-A", kind="duty", item="beer", band="all",
            abv_min=0.0, abv_max=8.0, design="A", share=1.10, effective_from="2026-04-01",
            notification="teaching row, chapter 5.2.1", note="design A: 110 percent of DMC, no floor"),
        row(row_id="SB-2026-04", state="S-B", kind="duty", item="beer", band="all",
            abv_min=0.0, abv_max=8.0, design="B", rate_per_bl=140.0, effective_from="2026-04-01",
            notification="teaching row, chapter 5.2.2", note="design B: INR 140 a bulk litre"),
        row(row_id="SB2-2026-04", state="S-B2", kind="duty", item="beer", band="all",
            abv_min=0.0, abv_max=8.0, design="B2", rate_per_lal=2650.0, effective_from="2026-04-01",
            notification="teaching row, chapter 5.2.2", note="design B2: INR 2,650 a litre of alcohol"),
    ]


def oct_change_rows():
    """Chapter 13.1: the strong row closes on 30 September 2026; a 120 percent row opens."""
    rows = state_s_rows()
    strong = dict(rows[0])
    strong.update(effective_to="2026-09-30", note="closed 30 September 2026, superseded by S-STRONG-2026-10")
    new = dict(rows[0])
    new.update(row_id="S-STRONG-2026-10", share=1.20, effective_from="2026-10-01",
               notification="State S Excise Notification S/EXC/2026/09 of 15 September 2026 (synthetic)",
               link="data/circulars/c4-strong-beer-revision.txt",
               note="invented in chapter 13.1 to teach a rule change")
    return [strong, new] + rows[1:]


def real_state_rows():
    """Appendix B.2 as printed. Nothing here is computed from or filled in.

    Blank numbers stay blank. Status is 'to verify' for every printed row and
    'not found' where the book found no public source.
    """
    mh_src = ("State Excise Department, Excise Duty and Fee Structure 2025-26, "
              "page reviewed 11 July 2025")
    mh_link = "stateexcise.maharashtra.gov.in/1246/Excise-Duty-and-Fee-Structure"
    mh_fee = "Home Department notification No. BPA-0126/C.R.14/Exc-2 of 18 February 2026"
    ka = "Karnataka Excise (Excise Duties and Fees) (Amendment) Rules, 2025, dated 8 January 2025"
    ka_link = "republished copies: legitquest.com, teamleaseregtech.com (gazette not fetched)"
    tn = ("G.O. Ms. No. 30, SRO A-12(b-2)/2026, Gazette Extraordinary No. 273 of 5 June 2026; "
          "wording fixed by No. 281 of 12 June 2026")
    real = dict(checked_by=None, checked_on=None, status="to verify")
    rows = [
        row(row_id="MH-STRONG-2025-26", state="Maharashtra", kind="duty", item="beer",
            band="strong (fermented), over 5 percent ABV", design="C", share=2.35, floor_per_bl=80,
            notification=mh_src, link=mh_link, source_fetch_date="2026-11-03",
            note="period as printed: 2025-26; start date not printed", **real),
        row(row_id="MH-MILD-2025-26", state="Maharashtra", kind="duty", item="beer",
            band="mild, under 5 percent ABV", design="C", share=1.75, floor_per_bl=42,
            notification=mh_src, link=mh_link, source_fetch_date="2026-11-03",
            note="period as printed: 2025-26; where exactly 5.0 falls is not stated", **real),
        row(row_id="MH-CRAFT-2025-26", state="Maharashtra", kind="duty", item="craft beer",
            band="craft beer up to 8 percent ABV", design="B", rate_per_bl=60.0,
            notification=mh_src, link=mh_link, source_fetch_date="2026-11-03",
            note="period as printed: 2025-26", **real),
        row(row_id="MH-FEE-TRANSPORT-2025-26", state="Maharashtra", kind="fee", item="transport fee",
            band="beer", fee_amount=0.25, fee_unit="INR a bulk litre", notification=mh_src,
            link=mh_link, source_fetch_date="2026-11-03", note="period as printed: 2025-26", **real),
        row(row_id="MH-FEE-BRL-2026-27", state="Maharashtra", kind="fee", item="brewery licence, Form BRL",
            band="beer", fee_amount=1122000.0, fee_unit="INR a year up to 1,00,000 cases of 7.8 bulk litres",
            notification=mh_fee, link="stateexcise.maharashtra.gov.in/1247/Excise-License-Fee",
            source_fetch_date="2026-11-03",
            note="period as printed: 2026-27; plus INR 11.22 a case above 1,00,000 cases", **real),
        row(row_id="MH-FEE-CRAFT-2026-27", state="Maharashtra", kind="fee", item="craft beer licence",
            band="craft beer", fee_amount=320100.0, fee_unit="INR a year up to 2,00,000 bulk litres",
            notification=mh_fee, link="stateexcise.maharashtra.gov.in/1247/Excise-License-Fee",
            source_fetch_date="2026-11-03",
            note="period as printed: 2026-27; 6,40,100 to 4,00,000 bulk litres; 8,00,200 to 15,00,000", **real),
        row(row_id="KA-BASIC-MILD-2025-01", state="Karnataka", kind="duty", item="basic excise",
            band="beer up to 5 percent ABV", design="B", rate_per_bl=12.0,
            effective_from="2025-01-20", effective_to="2026-05-10", notification=ka, link=ka_link,
            source_fetch_date="2026-11-03", note="replaced from 11 May 2026 by FD 14 PES 2026", **real),
        row(row_id="KA-BASIC-STRONG-2025-01", state="Karnataka", kind="duty", item="basic excise",
            band="beer from 5 to 8 percent ABV", design="B", rate_per_bl=20.0,
            effective_from="2025-01-20", effective_to="2026-05-10", notification=ka, link=ka_link,
            source_fetch_date="2026-11-03", note="replaced from 11 May 2026 by FD 14 PES 2026", **real),
        row(row_id="KA-ADDL-BOTTLED-2025-01", state="Karnataka", kind="duty", item="additional excise",
            band="bottled beer, declared price INR 300 and above", design="C", share=1.95,
            floor_per_bl=130, effective_from="2025-01-20", effective_to="2026-05-10",
            notification=ka, link=ka_link, source_fetch_date="2026-11-03",
            note=("price read as a case on the author's reading only; press reports of 2025 put it at "
                  "200 percent with no gazette number; replaced from 11 May 2026"), **real),
        row(row_id="KA-BEER-2026-05", state="Karnataka", kind="duty", item="beer, alcohol in beverage system",
            band="beer", effective_from="2026-05-11",
            notification="FD 14 PES 2026 of 8 May 2026", link="summary on teamleaseregtech.com",
            source_fetch_date="2026-11-03", checked_by=None, checked_on=None, status="not found",
            note="beer rates under the new system not found in a public source; none printed"),
        row(row_id="TN-FEE-CASE-2026-06", state="Tamil Nadu", kind="fee", item="additional licence fee",
            band="beer", fee_amount=40.0, fee_unit="INR a standard case",
            effective_from="2026-06-05", notification=tn,
            link="stationeryprinting.tn.gov.in/extraordinary/2026/273_Ex_III_1a_2026.pdf",
            source_fetch_date="2026-11-03",
            note=("paid by the brewery before removal; a standard case is 12 x 650 ml, "
                  "24 x 325 ml bottles or 24 cans of 500 ml"), **real),
        row(row_id="TN-DRAUGHT-2024-06", state="Tamil Nadu", kind="duty", item="draught beer",
            band="draught beer", design="B", rate_per_bl=42.60, effective_from="2024-06-10",
            notification=("G.O. Ms. No. 26, Home, Prohibition and Excise (III-2), notification "
                          "No. II(1)/HOPE/10(r)/2024, Gazette Extraordinary No. 186 of 10 June 2024, "
                          "amending notification No. II(1)/PE/239(d)/81 under section 18-B"),
            link="stationeryprinting.tn.gov.in/extraordinary/2024/186_Ex_II_1_2024.pdf",
            source_fetch_date="2026-11-03",
            note=("up from INR 13.10; draught only, not bottled beer; no later amendment found; "
                  "effective date taken as the gazette date"), **real),
        row(row_id="TN-BEER-DUTY", state="Tamil Nadu", kind="duty", item="bottled beer excise", band="beer",
            notification=None, source_fetch_date="2026-11-03", checked_by=None, checked_on=None,
            status="not found", note="basis and rate for bottled or canned beer not found in a public source"),
        row(row_id="HR-FEE-BOTTLING-2024-25", state="Haryana", kind="fee", item="bottling fee",
            band="beer", fee_amount=12.0, fee_unit="INR a bulk litre",
            notification="Food Business Middle East and Africa, 23 May 2024 (trade press)",
            source_fetch_date=None, note="period as printed: 2024-25, up from INR 11; not confirmed for 2025-27",
            **real),
        row(row_id="HR-BEER-DUTY-2025-27", state="Haryana", kind="duty", item="beer excise", band="beer",
            notification="2025-27 policy, 12 June 2025 to 31 March 2027 (Tribune India, press)",
            source_fetch_date=None, checked_by=None, checked_on=None, status="not found",
            note="basis, rate, MRP formula and margins not found in a public source"),
    ]
    return rows


def skus():
    """Kestrel India packs (Series Bible, India v4). DMC is the net selling price a hL x hL a case."""
    s = pd.DataFrame([
        ("SKU1", "Kestrel Lager", "12 x 650 ml bottle", 12, 0.65, 5.3, 12600, 18.00, 30.0),
        ("SKU2", "Kestrel Lager", "24 x 330 ml bottle", 24, 0.33, 5.3, 12600, 10.80, 35.0),
        ("SKU3", "Kestrel Lager", "24 x 330 ml can", 24, 0.33, 5.3, 12600, 12.60, 20.0),
        ("SKU4", "Kestrel Stout", "12 x 650 ml bottle", 12, 0.65, 5.7, 15300, 18.00, 30.0),
        ("SKU5", "Kestrel Pale Ale", "12 x 650 ml bottle", 12, 0.65, 5.8, 16200, 18.00, 30.0),
    ], columns=["sku_id", "beer", "pack", "units", "litres_per_unit", "abv",
                "net_price_per_hl", "unit_cost", "carton_cost"])
    s["bulk_litres_case"] = (s.units * s.litres_per_unit).round(2)
    s["hl_case"] = (s.bulk_litres_case / 100).round(4)
    s["dmc_case"] = (s.net_price_per_hl * s.hl_case).round(2)
    return s


def params():
    p = [
        ("book_rate_inr_per_usd", 90, "INR", "planning rate, not a market one"),
        ("cost_of_capital", 0.12, "a year", "carrying cost, NPV, capital charge"),
        ("beer_to_bright_per_hl", 2880, "INR a hL", "USD 32 x 90"),
        ("wort_cost_per_hl", 2160, "INR a hL", "malt 1,431 + other 729"),
        ("malt_per_kg", 81, "INR a kg", "USD 0.90 x 90"),
        ("malt_kg_per_brew", 5300, "kg", "300 hL brew"),
        ("brew_hl", 300, "hL", ""),
        ("other_wort_cost_per_hl", 729, "INR a hL", "hops, water, energy, brewhouse labour; not split"),
        ("overhead_per_hl", 1890, "INR a hL", "typical month"),
        ("freight_per_hl", 630, "INR a hL", "outbound"),
        ("blended_packaging_per_hl", 2790, "INR a hL", "USD 31 x 90"),
        ("blended_cogs_ex_works_per_hl", 7560, "INR a hL", "USD 84 x 90"),
        ("net_price_blended_per_hl", 13500, "INR a hL", "USD 150 x 90"),
        ("annual_volume_hl", 100000, "hL a year", "Kestrel plant"),
        ("wholesaler_margin_route_a", 0.08, "of landed price", "pays 30 days after dispatch"),
        ("corporation_margin_route_c", 0.10, "of landed price", "pays 60 days after depot receipt"),
        ("retailer_margin", 0.15, "of buyer's price", ""),
        ("mrp_rounding_step", 5, "INR a bottle", "round up; retailer keeps it"),
        ("popular_anchor_mrp", 190, "INR a 650 ml bottle", "synthetic State S anchor for price bands"),
    ]
    return pd.DataFrame(p, columns=["name", "value", "unit", "note"])


def volume_by_year(rng):
    """Chapter 2: two financial years by route and SKU.

    FY2026: 1,00,000 hL at a blended INR 13,500 a hL (lager 70, pale ale 10, stout 20 percent
    gives exactly 13,500). Route A 60,000 hL, Route C 40,000 hL. FY2027: volume up 6 percent,
    the mix moves toward stout and pale ale, prices are scaled so revenue grows 11.3 percent,
    so price mix is 1.113 / 1.06 - 1 = 5 percent.
    """
    price = {"Lager": 12600, "Pale Ale": 16200, "Stout": 15300}
    y1 = {"Lager": 70000, "Pale Ale": 10000, "Stout": 20000}
    e, f = rng.integers(-1500, 1500), rng.integers(-500, 500)
    a1 = {"Lager": 42000 + e, "Pale Ale": 6000 + f, "Stout": 12000 - e - f}
    y2_total = 106000
    shift = int(rng.integers(1500, 2500))
    y2 = {"Lager": 74200 - 2 * shift, "Pale Ale": 10600 + shift, "Stout": 21200 + shift}
    g = rng.integers(-1500, 1500)
    a2 = {"Lager": int(round(y2["Lager"] * 0.6)) + g, "Pale Ale": int(round(y2["Pale Ale"] * 0.6))}
    a2["Stout"] = 63600 - a2["Lager"] - a2["Pale Ale"]
    rev1 = sum(price[b] * y1[b] for b in price)
    rev2_at_y1_prices = sum(price[b] * y2[b] for b in price)
    k = rev1 * 1.113 / rev2_at_y1_prices
    rows = []
    for fy, tot, a, kk in (("FY2026", y1, a1, 1.0), ("FY2027", y2, a2, k)):
        for b in price:
            for route, hl in (("Route A", a[b]), ("Route C", tot[b] - a[b])):
                rows.append((fy, route, b, hl, round(price[b] * kk, 6), round(hl * price[b] * kk, 2)))
    df = pd.DataFrame(rows, columns=["fy", "route", "beer", "hl", "price_per_hl", "revenue_inr"])
    assert df[df.fy == "FY2027"].hl.sum() == y2_total
    return df


def dispatches(rng, sku):
    """Chapter 4 and 13: passes from April to September 2026 under the base State S table.

    September 2026 holds exactly 1,000 cases of SKU1 in five passes of 200 (chapter 13.3); one of
    them is charged at the mild rate (chapter 14.4, INR 58,968 short). One June pass carries a
    stale DMC. Every other pass is charged right.
    """
    s = sku.set_index("sku_id")
    rows, n = [], 0
    months = pd.date_range("2026-04-01", "2026-09-01", freq="MS")
    for m in months:
        for sid in s.index:
            if sid == "SKU1" and m.month == 9:
                days, sizes = [2, 8, 14, 21, 28], [200] * 5
            else:
                k = int(rng.integers(3, 7))
                days = sorted(rng.choice(np.arange(1, 29), size=k, replace=False))
                sizes = list(rng.integers(10, 41, size=k) * 10)
            for d, c in zip(days, sizes):
                n += 1
                rows.append(dict(pass_no=f"TP-S-26-{n:04d}", invoice_no=f"INV-26-{n:04d}",
                                 dispatch_date=m + pd.Timedelta(days=int(d) - 1), state="S",
                                 sku_id=sid, cases=int(c)))
    f = pd.DataFrame(rows)
    f = f.merge(s[["abv", "bulk_litres_case", "hl_case", "dmc_case"]], left_on="sku_id", right_index=True)
    f["hl"] = (f.cases * f.hl_case).round(4)
    f["bulk_litres"] = (f.cases * f.bulk_litres_case).round(2)
    f["band_charged"] = np.where(f.abv > 5.0, "strong", "mild")
    share = np.where(f.band_charged == "strong", 1.10, 0.80)
    f["rate_version"] = np.where(f.band_charged == "strong", "S-STRONG-2026-04", "S-MILD-2026-04")
    f["dmc_stored"] = f.dmc_case
    sep = f[(f.sku_id == "SKU1") & (f.dispatch_date.dt.month == 9)].index
    mild_pass = sep[2]
    f.loc[mild_pass, ["band_charged", "rate_version"]] = ["mild", "S-MILD-2026-04"]
    share[f.index.get_loc(mild_pass)] = 0.80
    jun = f[(f.sku_id == "SKU2") & (f.dispatch_date.dt.month == 6)].index[0]
    f.loc[jun, "dmc_stored"] = 950.00
    duty_case = np.round(share * f.dmc_stored.to_numpy() + 1e-9, 2)
    f["duty_charged"] = np.round(duty_case * f.cases, 2)
    f["fee_charged"] = np.round(2.0 * f.bulk_litres, 2)
    f = f.drop(columns=["dmc_stored"]).sort_values(["dispatch_date", "pass_no"])
    return f[["pass_no", "invoice_no", "dispatch_date", "state", "sku_id", "cases", "hl",
              "bulk_litres", "abv", "band_charged", "rate_version", "dmc_case",
              "duty_charged", "fee_charged", "bulk_litres_case"]]


def weekly_plan(rng):
    """Chapter 3.4: a 26 week dispatch plan for SKU1, cases a week."""
    weeks = pd.date_range("2026-04-06", periods=26, freq="W-MON")
    cases = (rng.normal(2000, 300, size=26) / 10).round() * 10
    return pd.DataFrame({"week_start": weeks.date, "sku_id": "SKU1", "cases": cases.astype(int)})


CIRCULARS = {
    "c1-beer-duty.txt": """STATE S EXCISE DEPARTMENT (SYNTHETIC)
Notification No. S/EXC/2026/01
Issued: 15 March 2026
Effective: 1 April 2026
Language: English
Subject: Excise duty on beer

1. Short title. This notification sets the excise duty on beer made in State S.
2. Strong beer. Beer above 5.0 percent alcohol by volume and up to 8.0 percent shall pay the larger of 110 percent of the declared manufacturing cost and INR 50 a bulk litre.
3. Mild beer. Beer up to 5.0 percent alcohol by volume shall pay the larger of 80 percent of the declared manufacturing cost and INR 40 a bulk litre.
4. Time of payment. Duty shall be paid by the licensee before the transport pass is issued.
5. Declared manufacturing cost. The licensee shall declare the ex brewery price of each pack before the first removal.
""",
    "c2-transport-pass.txt": """STATE S EXCISE DEPARTMENT (SYNTHETIC)
Circular No. S/EXC/2026/02
Issued: 15 March 2026
Effective: 1 April 2026
Language: English
Subject: Transport pass fee

1. Fee. A transport pass fee of INR 2 a bulk litre shall be paid on every removal of beer.
2. Pass. No beer shall move from the brewery without a transport pass issued for the consignment.
3. Record. The pass number shall appear on the invoice for the consignment.
""",
    "c3-label-registration.txt": """STATE S EXCISE DEPARTMENT (SYNTHETIC)
Circular No. S/EXC/2026/03
Issued: 15 March 2026
Effective: 1 April 2026
Language: English
Subject: Label and brand registration

1. Registration. Every pack of every brand shall be registered before its first dispatch.
2. Fee. The registration fee is INR 25,000 for each SKU for each year.
3. Changes. A change of label artwork requires a fresh registration.
""",
    "c4-strong-beer-revision.txt": """STATE S EXCISE DEPARTMENT (SYNTHETIC)
Notification No. S/EXC/2026/09
Issued: 15 September 2026
Effective: 1 October 2026
Language: English
Subject: Revision of excise duty on strong beer

1. Amendment. In clause 2 of Notification No. S/EXC/2026/01, for the words 110 percent the words 120 percent shall be substituted.
2. Commencement. This amendment shall come into force on 1 October 2026 and applies to beer removed from the brewery on or after that date.
3. Other clauses. Clause 3 of Notification No. S/EXC/2026/01 stands unchanged.
""",
    "c5-dry-days.txt": """STATE S EXCISE DEPARTMENT (SYNTHETIC)
Circular No. S/EXC/2026/11
Issued: 1 April 2026
Effective: 1 April 2026
Language: English
Subject: Dry days for the year 2026-27

1. Dry days. No sale of liquor shall take place in State S on the days listed in the schedule to this circular.
2. Schedule. 2 October 2026, 26 January 2027 and any polling day notified by the state.
3. Stock. Licensees may receive stock on a dry day but shall not sell it.
""",
}


def eval_set():
    """Chapter 14.5: 20 questions, each answer produced by the calculator, with its rate version."""
    import calculator as calc
    base = calc.load_rates()
    chg = calc.load_rates("rate_table_state_s_oct_change.csv")
    dmc1, dmc330 = 982.80, 997.92
    strong = calc.row_in_force(base, "S", 5.3, "2026-07-15")
    w = calc.walk(dmc1, rates=base)
    w330 = calc.walk(dmc330, bottles=24, litres=0.33, rates=base)
    wc = calc.walk(dmc1, rates=base, buyer=0.10)
    w120 = calc.walk(dmc1, rates=chg, date="2026-10-15")
    stout = calc.walk(1193.40, abv=5.7, rates=base)
    mild = calc.row_in_force(base, "S", 5.0, "2026-07-15")
    q = []

    def add(text, answer, version, trap="no", chapter=""):
        q.append(dict(id=f"Q{len(q) + 1:02d}", question=text, answer=answer,
                      rate_version=version, trap=trap, chapter=chapter))

    S, M, F = "S-STRONG-2026-04", "S-MILD-2026-04", "S-FEE-PASS-2026-04"
    add("Duty on one case of Kestrel Lager, 5.3 percent ABV, DMC 982.80, dispatched 15 July 2026?",
        calc.duty_for(strong, dmc1, 7.8, 5.3), S, chapter="5.2.1")
    add("Duty on the same case brewed at exactly 5.0 percent ABV, dispatched 15 July 2026?",
        calc.duty_for(mild, dmc1, 7.8, 5.0), M, "yes: exactly 5.0 percent is mild", "5.3")
    add("Below what DMC a case does the strong floor set the duty?",
        calc.floor_bites_below(1.10, 50, 7.8), S, chapter="5.2.3")
    add("Landed price a case at 110 percent, dispatched 15 July 2026?", w.landed, S, chapter="6.4")
    add("MRP a bottle for a case dispatched 15 October 2026, under the table with the 1 October change?",
        w120.mrp_bottle, "S-STRONG-2026-10", chapter="14.2")
    add("Duty on a case of Kestrel Lager dispatched 15 March 2026?", "REFUSE",
        "none: no row before 1 April 2026", "yes: no rate row for the date", "14.5")
    add("Duty a case under design B at INR 140 a bulk litre?",
        calc.duty_for(calc.row_in_force(base, "S-B", 5.3, "2026-07-15"), dmc1, 7.8, 5.3),
        "SB-2026-04", chapter="5.2.2")
    add("Duty a case under design B2 at INR 2,650 a litre of alcohol?",
        calc.duty_for(calc.row_in_force(base, "S-B2", 5.3, "2026-07-15"), dmc1, 7.8, 5.3),
        "SB2-2026-04", chapter="5.2.2")
    add("Transport pass fee on one case, dispatched 15 July 2026?", w.fee, F, chapter="5.5")
    add("Wholesaler's price a case on Route A?", w.buyer_price, S, chapter="6.4")
    add("MRP a bottle on Route A?", w.mrp_bottle, S, chapter="6.4")
    add("Price before rounding a bottle on Route C (10 percent corporation margin)?",
        wc.pre_round_bottle, S, chapter="7.5")
    add("Highest DMC a case that still gives an MRP of INR 220 on Route A?",
        calc.r2(calc.reverse_dmc(220)), S, chapter="6.2")
    add("Excise plus pass fee on one case, dispatched 15 July 2026?", calc.r2(w.duty + w.fee), S, chapter="6.4")
    add("Duty on 10 cases of 12 x 650 ml plus 10 cases of 24 x 330 ml Kestrel Lager, both dispatched 15 July 2026?",
        calc.r2(10 * w.duty + 10 * w330.duty), S, "yes: mixes a 650 ml case with a 330 ml case", "9.1")
    add("Duty on 1,000 cases of Kestrel Lager in one month, dispatched July 2026?",
        calc.r2(1000 * w.duty), S, chapter="13.3")
    add("Using the 110 percent row, what is the duty on a lager case dispatched 15 October 2026?",
        w120.duty, "S-STRONG-2026-10", "yes: the 110 percent row expired on 30 September", "13.1")
    add("A pass of 200 cases of Kestrel Lager was charged at the mild rate. How much duty is short?",
        calc.r2(200 * (w.duty - calc.duty_for(mild, dmc1, 7.8, 5.0))), S, chapter="14.4")
    add("MRP a bottle of Kestrel Stout, 5.7 percent ABV, DMC 1,193.40?", stout.mrp_bottle, S, chapter="12.1")
    add("Duty on a case of Kestrel Lager dispatched 30 September 2026 under the table with the 1 October change?",
        calc.duty_for(calc.row_in_force(chg, "S", 5.3, "2026-09-30"), dmc1, 7.8, 5.3), S, chapter="13.1")
    return pd.DataFrame(q)


def main():
    DATA.mkdir(exist_ok=True)
    (DATA / "circulars").mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    pd.DataFrame(state_s_rows(), columns=RATE_COLS).to_csv(DATA / "rate_table_state_s.csv", index=False)
    pd.DataFrame(oct_change_rows(), columns=RATE_COLS).to_csv(DATA / "rate_table_state_s_oct_change.csv", index=False)
    pd.DataFrame(real_state_rows(), columns=RATE_COLS).to_csv(DATA / "rate_table_real_states.csv", index=False)
    sku = skus()
    sku.to_csv(DATA / "skus.csv", index=False)
    params().to_csv(DATA / "kestrel_india_params.csv", index=False)
    volume_by_year(rng).to_csv(DATA / "volume_by_year.csv", index=False)
    d = dispatches(rng, sku)
    d.to_csv(DATA / "dispatches_state_s.csv", index=False, date_format="%Y-%m-%d")
    weekly_plan(rng).to_csv(DATA / "dispatch_plan_weekly.csv", index=False)
    for name, text in CIRCULARS.items():
        (DATA / "circulars" / name).write_text(text)
    (HERE / "eval").mkdir(exist_ok=True)
    eval_set().to_csv(HERE / "eval" / "duty-eval-20.csv", index=False)
    print("wrote", len(list(DATA.glob("*.csv"))), "CSVs, 5 circulars and the 20 question eval set")


if __name__ == "__main__":
    main()
