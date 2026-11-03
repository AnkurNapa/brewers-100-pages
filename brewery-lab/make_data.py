"""Writes every CSV in data/ and every workbook in sheets/ from fixed seeds.

Kestrel Brewing is a synthetic plant. Every number here is made up and labelled as such.
Run: python3 make_data.py  (about a minute; the panel and micro sets search for an exact fit)
Seeds: week 1103, dirty haze export 41, haze 5, pH 9, water check 71, gauge study 72,
fills 42, micro 7, scoring panel 1011, tasting records 1102, lot TPO 2081, DO release 14.
"""
import math
import random
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as ss
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import ch11_tpo_lots

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
DATA, SHEETS = HERE / "data", HERE / "sheets"


def save(df, name):
    DATA.mkdir(exist_ok=True)
    df.to_csv(DATA / name, index=False)


# ---------------------------------------------------------------- MBAA relations (chapter 2)
def rdf(og, ae):
    re = 0.1808 * og + 0.8192 * ae
    abw = (og - re) / (2.0665 - 0.010665 * og)
    return 100 * 2.0665 / (2.0665 + re / abw)


def ae_for_rdf(og, target):
    lo, hi = np.full_like(og, 0.5), np.full_like(og, 5.0)
    for _ in range(60):
        mid = (lo + hi) / 2
        high = rdf(og, mid) > target
        lo, hi = np.where(high, mid, lo), np.where(high, hi, mid)
    return (lo + hi) / 2


# ---------------------------------------------------------------- chapters 1 and 3: the synthetic week
DAYS = [datetime(2026, 10, 28) + timedelta(days=i) for i in range(7)]
SPECS = [  # beer, test_code, low, target, high, version, valid_from
    ("Kestrel Lager", "OG", 11.8, 12.0, 12.2, 3, "2026-01-01"), ("Kestrel Lager", "AE", 1.8, 2.2, 2.6, 3, "2026-01-01"),
    ("Kestrel Lager", "ABV", 5.1, 5.3, 5.5, 3, "2026-01-01"), ("Kestrel Lager", "IBU", 16, 18, 20, 3, "2026-01-01"),
    ("Kestrel Lager", "COLOUR", 6, 7, 8, 3, "2026-01-01"), ("Kestrel Lager", "PH", 4.2, None, 4.5, 3, "2026-01-01"),
    ("Kestrel Lager", "CO2", 4.8, 5.0, 5.2, 3, "2026-01-01"), ("Kestrel Pale Ale", "OG", 13.3, 13.5, 13.7, 2, "2026-01-01"),
    ("Kestrel Pale Ale", "AE", 2.4, 2.8, 3.2, 2, "2026-01-01"), ("Kestrel Pale Ale", "PH", 4.2, None, 4.5, 2, "2026-01-01"),
    ("Kestrel Stout", "OG", 13.8, 14.0, 14.2, 2, "2026-01-01"), ("Kestrel Stout", "AE", 3.2, 3.6, 4.0, 2, "2026-01-01"),
    ("Kestrel Stout", "PH", 4.1, None, 4.4, 2, "2026-01-01"), ("Kestrel Stout", "CO2", 4.0, 4.2, 4.4, 2, "2026-01-01"),
    ("Kestrel Pale Ale", "ABV", 5.6, 5.8, 6.0, 2, "2026-01-01"), ("Kestrel Pale Ale", "IBU", 34, None, 42, 2, "2026-01-01"),
    ("Kestrel Pale Ale", "COLOUR", 12, None, 16, 2, "2026-01-01"), ("Kestrel Stout", "ABV", 5.5, 5.7, 5.9, 2, "2026-01-01"),
    ("Kestrel Stout", "IBU", 28, None, 36, 2, "2026-01-01"), ("Kestrel Stout", "COLOUR", 62, None, 78, 2, "2026-01-01"),
    ("all", "TEMPCHK", 10.5, 11.0, 11.5, 1, "2026-01-01"), ("all", "FILL", 330, None, None, 1, "2026-01-01"),
    ("all", "PU", 15, None, None, 1, "2026-01-01"), ("all", "CELLS", 12, 15, 18, 1, "2026-01-01"),
    ("all", "VIAB", 90, None, None, 1, "2026-01-01"), ("all", "YSUSP", None, None, None, 1, "2026-01-01"),
    ("all", "VDK", None, 0.05, 0.10, 2, "2026-01-01"), ("all", "DO", None, 30, 50, 2, "2026-01-01"),
    ("all", "TPO", None, 100, 150, 2, "2026-01-01"), ("all", "HAZE90", None, 0.4, 0.5, 2, "2026-06-01"),
    ("all", "HAZE25", None, None, 0.5, 2, "2026-06-01"), ("all", "FAHAZE", None, None, 2.0, 1, "2026-01-01"),
    ("all", "MIC_MEM", None, None, 5, 1, "2026-01-01"), ("all", "MIC_PLATE", None, None, 10, 1, "2026-01-01"),
    ("all", "MIC_RINSE", None, None, 10, 1, "2026-01-01"), ("all", "ATP", None, None, 300, 1, "2026-01-01"),
    ("all", "TTT", None, None, None, 1, "2026-01-01"),
]
TESTS = [  # test_code, method, version, unit, instrument_id, stream
    ("OG", "M-DEN-01", 4, "degrees Plato", "DM-01", "density"), ("AE", "M-DEN-02", 4, "degrees Plato", "DM-01", "density"),
    ("ABV", "M-ALC-01", 2, "percent", "BA-01", "density"), ("IBU", "M-IBU-01", 3, "IBU", "SP-01", "other chemistry"),
    ("COLOUR", "M-COL-01", 2, "EBC", "SP-01", "other chemistry"), ("PH", "M-PH-01", 5, "pH", "PH-02", "pH"),
    ("CO2", "M-CO2-01", 2, "g/L", "CO2-01", "other chemistry"), ("VDK", "M-VDK-01", 2, "mg/L", "GC-01", "other chemistry"),
    ("DO", "M-DO-01", 3, "ppb", "DO-01", "dissolved oxygen"), ("TPO", "M-DO-02", 3, "ppb", "DO-02", "dissolved oxygen"),
    ("HAZE90", "M-HAZ-01", 3, "EBC", "HZ-01", "haze"), ("HAZE25", "M-HAZ-01", 3, "EBC", "HZ-01", "haze"),
    ("FAHAZE", "M-HAZ-03", 1, "EBC", "HZ-01", "haze"), ("ALK", "M-WAT-01", 1, "mg/L CaCO3", "TI-01", "other chemistry"),
    ("CL2", "M-WAT-02", 1, "mg/L", "PHO-01", "other chemistry"), ("CO2PUR", "M-GAS-01", 1, "percent", "GA-01", "other chemistry"),
    ("MOIST", "M-RAW-01", 2, "percent", "NIR-01", "other chemistry"), ("CELLS", "M-YST-01", 2, "million/mL", "CC-01", "other chemistry"),
    ("MIC_MEM", "M-MIC-01", 3, "CFU/100 mL", "INC-01", "micro"), ("MIC_PLATE", "M-MIC-02", 3, "CFU/mL", "INC-02", "micro"),
    ("MIC_RINSE", "M-MIC-03", 2, "CFU/100 mL", "INC-01", "micro"), ("ATP", "M-HYG-01", 2, "RLU", "ATP-01", "micro"),
    ("TTT", "M-SEN-01", 2, "votes not TTT", "PANEL", "sensory"),
    ("EXTR", "M-RAW-02", 1, "percent", "MASH-01", "other chemistry"), ("VIAB", "M-YST-02", 1, "percent", "CC-01", "other chemistry"),
    ("TEMPCHK", "M-FER-01", 1, "degrees C", "TH-03", "other chemistry"), ("YSUSP", "M-YST-03", 1, "million/mL", "CC-01", "other chemistry"),
    ("FILL", "M-PKG-01", 1, "mL", "BAL-02", "other chemistry"), ("PU", "M-PKG-02", 1, "PU", "PU-01", "other chemistry"),
]
# stage: (samples a day, join group, sample points, tests) from the series bible sample plan
PLAN = [
    ("water", 4, "equipment", ["BRW.LIQ01", "BRW.LIQ01", "DAW.TK01", "UTL.CO2"], None),
    ("raw material", 1, "ingredient", ["RAW.MALT"], ["MOIST", "EXTR", "COLOUR"]),
    ("wort", 2, "brew", ["BRW.KET01", "CEL.INLET"], ["OG", "PH", "COLOUR", "IBU"]),
    ("yeast", 1, "fill", ["YST.TK01"], ["CELLS", "VIAB"]),
    ("fermentation", 6, "fill", ["CEL.FV%02d" % i for i in (1, 2, 3, 4, 5, 6)], ["AE", "PH", "TEMPCHK", "YSUSP"]),
    ("maturation", 3, "fill", ["CEL.FV07", "CEL.FV08", "CEL.FV09"], ["AE", "VDK", "CO2", "PH", "HAZE90"]),
    ("filtration and bright beer", 4, "bright or pack", ["FIL.OUT01", "FIL.OUT01", "BBT.BT03", "BBT.BT05"], ["HAZE90", "HAZE25", "DO"]),
    ("packaging", 8, "bright or pack", ["PKG.B1"] * 4 + ["PKG.C1"] * 4, ["TPO", "CO2", "FILL", "ABV", "PU"]),
    ("process micro", 12, "micro", ["CEL.INLET", "CEL.FV03", "BBT.BT03", "BBT.BT05", "PKG.B1", "PKG.C1"] * 2, None),
    ("hygiene", 14, "equipment", ["HYG.FIL%02d" % i for i in range(1, 11)] + ["CIP.RINSE%02d" % i for i in range(1, 5)], None),
    ("shelf life", 2, "bright or pack", ["QA.RETAIN", "QA.RETAIN"], ["HAZE90", "TPO", "FAHAZE", "CO2"]),
    ("sensory", 3, "bright or pack", ["QA.PANEL", "QA.PANEL", "QA.COMPLAINT"], ["TTT"]),
]
VALUE = {"OG": (12.0, 0.03), "AE": (2.2, 0.12), "ABV": (5.3, 0.04), "IBU": (18, 0.6), "COLOUR": (7, 0.2), "PH": (4.35, 0.03),
         "CO2": (5.0, 0.05), "VDK": (0.06, 0.02), "DO": (28, 5), "TPO": (85, 18), "HAZE90": (0.36, 0.04), "HAZE25": (0.30, 0.04),
         "FAHAZE": (1.2, 0.25), "ALK": (25, 3), "CL2": (0.02, 0.01), "CO2PUR": (99.95, 0.02), "MOIST": (4.3, 0.2), "CELLS": (15, 2),
         "EXTR": (81.0, 0.5), "VIAB": (96, 1.5), "TEMPCHK": (11.0, 0.3), "YSUSP": (20, 6), "FILL": (332, 1.2), "PU": (19, 1.5)}
BEER_VALUE = {"Kestrel Pale Ale": {"OG": (13.5, 0.03), "AE": (2.8, 0.12), "IBU": (38, 1.0), "COLOUR": (14, 0.5), "ABV": (5.8, 0.04), "CO2": (4.8, 0.05)},
              "Kestrel Stout": {"OG": (14.0, 0.03), "AE": (3.6, 0.12), "IBU": (32, 1.0), "COLOUR": (70, 2.0), "ABV": (5.7, 0.04), "CO2": (4.2, 0.05)}}
DECIMALS = {"OG": 2, "AE": 2, "ABV": 2, "IBU": 1, "COLOUR": 1, "PH": 2, "CO2": 2, "VDK": 3, "DO": 0, "TPO": 0, "HAZE90": 2,
            "HAZE25": 2, "FAHAZE": 2, "ALK": 0, "CL2": 2, "CO2PUR": 2, "MOIST": 1, "CELLS": 1, "EXTR": 1,
            "VIAB": 0, "TEMPCHK": 1, "YSUSP": 0, "FILL": 0, "PU": 1}


def week_tests(stage, point):
    if stage == "water":
        return {"BRW.LIQ01": ["PH", "ALK", "CL2"], "DAW.TK01": ["DO"], "UTL.CO2": ["CO2PUR"]}[point]
    if stage == "process micro":
        return ["MIC_MEM"] if point.startswith(("BBT", "PKG")) else ["MIC_PLATE"]
    if stage == "hygiene":
        return ["MIC_RINSE"] if point.startswith("CIP") else ["ATP"]
    tests = dict((p[0], p[4]) for p in PLAN)[stage]
    if point == "BBT.BT03" and stage.startswith("filtration"):
        return ["AE", "ABV", "PH", "IBU", "COLOUR", "HAZE90", "HAZE25", "DO", "CO2"]
    if stage == "wort" and point == "CEL.INLET":
        return ["OG", "PH"]
    return tests


def place_named(timed, seq, point, at):
    """Puts the bright beer sample at `point` in position `seq` of the day, sampled at `at`."""
    k = next(i for i, r in enumerate(timed) if r[1] == "filtration and bright beer" and r[3] == point)
    rec = timed.pop(k)
    timed.insert(seq - 1, (at,) + rec[1:])
    out = []
    for i, r in enumerate(timed):
        t = r[0]
        if i < seq - 1 and t >= at: t = at - timedelta(minutes=seq - 1 - i)
        if i > seq - 1 and t <= at: t = at + timedelta(minutes=i - seq + 1)
        out.append((t,) + r[1:])
    return out


def make_week(seed=1103):
    rng = np.random.default_rng(seed)
    samples, results = [], []
    fill_no, brew_no, lot_no = 30, 60, 0
    micro_positive = {(1, "BBT.BT05"), (3, "CIP.RINSE02"), (4, "HYG.FIL07"), (5, "PKG.C1")}  # 4 of 182: about 2 percent
    for di, day in enumerate(DAYS):
        rows = []
        for stage, n, group, points, _ in PLAN:
            for k in range(n):
                rows.append((stage, group, points[k % len(points)]))
        hours = np.sort(rng.uniform(6.0, 29.9, len(rows)))
        order = rng.permutation(len(rows))
        timed = []
        for (stage, group, point), h in zip([rows[i] for i in order], hours):
            if stage in ("process micro", "hygiene", "sensory", "raw material", "yeast"):
                h = 6.5 + (h - 6.0) * 15 / 24        # day work only: no plating or panel at night
            timed.append((day + timedelta(hours=float(h)), stage, group, point))
        timed.sort()
        if day.day == 3: timed = place_named(timed, 4, "BBT.BT03", day + timedelta(hours=6, minutes=5))
        if day.day == 31: timed = place_named(timed, 17, "FIL.OUT01", day + timedelta(hours=9, minutes=5))
        brew_no += 1
        for seq, (t, stage, group, point) in enumerate(timed, 1):
            sid = "S%s-%03d" % (day.strftime("%y%m%d"), seq)     # the lab day runs 06:00 to 06:00
            beer = "" if group in ("equipment", "ingredient") else str(rng.choice(["Kestrel Lager"] * 7 + ["Kestrel Pale Ale"] * 2 + ["Kestrel Stout"]))
            fill_id = brew_id = lot_id = ""
            if group == "brew": brew_id = "B26-%04d" % brew_no
            if group == "fill" or point.startswith(("BBT", "FIL", "CEL.FV")):
                fill_id = "F%s-26-%03d" % (point[-2:] if point.startswith("CEL.FV") else "07", fill_no + int(rng.integers(0, 6)))
            if group in ("bright or pack", "micro") and point.startswith(("PKG", "QA")):
                lot_no += 1
                lot_id = "L%s-%s-%d" % (day.strftime("%y%m%d"), "B1" if "B1" in point or rng.random() < 0.5 else "C1", 1 + lot_no % 2)
            if group == "ingredient": lot_id = "M-26-%04d" % (180 + di)
            link = "typed" if (fill_id or brew_id or lot_id) else ("equipment" if group == "equipment" else "none")
            if link == "typed" and (point.startswith(("BBT", "FIL")) or rng.random() < 0.12): link = "derived"
            samples.append(dict(sample_id=sid, stage=stage, sample_point=point, sampled_at=t.strftime("%Y-%m-%d %H:%M"),
                                sampler="AN%d" % (1 + (t.hour // 8 + di) % 4), beer=beer, fill_id=fill_id, brew_id=brew_id,
                                lot_id=lot_id, equipment_id=point if group == "equipment" else "", link_method=link))
            for code in week_tests(stage, point):
                if code in VALUE:
                    mu, sd = BEER_VALUE.get(beer, {}).get(code, VALUE[code])
                    v = round(float(rng.normal(mu, sd)), DECIMALS[code]); q = ""
                elif code == "ATP":
                    v, q = int(rng.integers(20, 140)), ""
                elif code == "TTT":
                    v, q = int(rng.integers(0, 2)), ""
                else:
                    v, q = 1, "<"
                if (di, point) in micro_positive and code.startswith(("MIC", "ATP")):
                    v, q = {"MIC_MEM": 6, "MIC_RINSE": 12, "ATP": 420, "MIC_PLATE": 14}[code], ""
                    micro_positive.discard((di, point))
                micro = code.startswith("MIC")
                tested = t + timedelta(hours=72 if micro else float(rng.uniform(0.3, 1.0)))
                entered = tested + timedelta(minutes=int(rng.integers(10, 120)))
                approved = entered + timedelta(minutes=int(rng.integers(30, 200)))
                results.append(dict(sample_id=sid, test_code=code, value=v, qualifier=q,
                                    analyst="MIC" if micro or code == "ATP" else "AN%d" % (1 + (t.hour // 8 + di) % 4),
                                    tested_at=tested.strftime("%Y-%m-%d %H:%M"), entered_at=entered.strftime("%Y-%m-%d %H:%M"),
                                    approved_at=approved.strftime("%Y-%m-%d %H:%M"), status="approved", is_current=1))
    smp, res = pd.DataFrame(samples), pd.DataFrame(results)
    # the two samples the book names, set exactly
    smp.loc[smp.sample_id.isin(["S261103-004", "S261031-017"]), "beer"] = "Kestrel Lager"
    res.loc[res.sample_id == "S261103-004", "tested_at"] = "2026-11-03 06:40"
    smp.loc[smp.sample_id == "S261031-017", "sampler"] = "AN3"
    named = res.sample_id == "S261031-017"
    res.loc[named, ["analyst", "tested_at", "entered_at", "approved_at"]] = ["AN3", "2026-10-31 09:50", "2026-10-31 11:15", "2026-10-31 13:20"]
    for c, v in (("DO", 31), ("HAZE90", 0.42), ("HAZE25", 0.44)): res.loc[named & (res.test_code == c), "value"] = v
    # planted orphans for the chapter 3 notebook: 2 unknown samples, 1 unknown test, 2 pale ale CO2 rows with no spec
    orph = res.sample(3, random_state=seed).copy()
    orph.iloc[0, 0] = orph.iloc[0, 0][:-3] + "1O7"
    orph.iloc[1, 0] = orph.iloc[1, 0].replace("S26", "S62")
    orph.iloc[2, 1] = "HAZE"
    res = pd.concat([res, orph], ignore_index=True)
    pa = smp.index[smp.beer == "Kestrel Pale Ale"][:2]
    extra = [dict(sample_id=smp.at[k, "sample_id"], test_code="CO2", value=4.8, qualifier="", analyst="AN2",
                  tested_at=smp.at[k, "sampled_at"], entered_at=smp.at[k, "sampled_at"], approved_at=smp.at[k, "sampled_at"],
                  status="approved", is_current=1) for k in pa]
    res = pd.concat([res, pd.DataFrame(extra)], ignore_index=True)
    res.insert(0, "result_id", ["R%05d" % (i + 1) for i in range(len(res))])
    lots = sorted(set(smp.lot_id) - {""} - {x for x in smp.lot_id if x.startswith("M-")})
    disp = [dict(lot_id=l, decision="hold" if k == 3 else "release", decided_by="QAL" if k % 5 else "MIC",
                 decided_at="", reason="72 hour plates read; chemistry and TTT in spec" if k != 3 else "membrane at action limit on line C1; trace started")
            for k, l in enumerate(lots)]
    for d in disp:
        d["decided_at"] = (datetime.strptime(d["lot_id"][1:7], "%y%m%d") + timedelta(days=3, hours=10)).strftime("%Y-%m-%d %H:%M")
    save(smp, "week_sample.csv"); save(res, "week_result.csv")
    save(pd.DataFrame(TESTS, columns=["test_code", "method", "version", "unit", "instrument_id", "stream"]), "week_test.csv")
    save(pd.DataFrame(SPECS, columns=["beer", "test_code", "low", "target", "high", "version", "valid_from"]), "week_spec_limit.csv")
    save(pd.DataFrame(disp), "week_disposition.csv")


# ---------------------------------------------------------------- chapter 4: the dirty haze export
def make_dirty_export(seed=41):
    random.seed(seed)                          # same draws as figures/brewery-lab/fig-4-1.py
    clean = [round(min(max(random.gauss(0.40, 0.04), 0.30), 0.48), 2) for _ in range(56)]
    clean[31] = 4.1
    sup = [round(random.uniform(0.34, 0.46), 2) for _ in range(3)]
    rows = []
    for i, v in enumerate(clean):
        s = i // 2
        day = datetime(2026, 10, 27) + timedelta(days=s // 4)
        t = day + timedelta(hours=7 + 4 * (s % 4))
        sid = "S%s-%03d" % (day.strftime("%y%m%d"), 5 + s % 4)
        rows.append(dict(sample_id=sid, test_code="HAZE90" if i % 2 == 0 else "HAZE25", value=f"{v}", unit="EBC",
                         lot_id="L%s-B1-%d" % (day.strftime("%y%m%d"), 1 + s % 2), sampled_at=t.strftime("%Y-%m-%d %H:%M"),
                         entered_at=(t + timedelta(minutes=50)).strftime("%Y-%m-%d %H:%M"), analyst="AN%d" % (1 + s % 4),
                         qualifier="", status="approved", is_current=1, fault=""))
    for i in (9, 40):
        rows[i].update(value="0.41 EBC", fault="text value")
    rows[31]["fault"] = "range: 4.1 against a 0.5 limit"
    rows[17]["unit"] = ""; rows[17]["fault"] = "blank unit"
    rows[23]["entered_at"] = (datetime.strptime(rows[23]["sampled_at"], "%Y-%m-%d %H:%M") - timedelta(minutes=35)).strftime("%Y-%m-%d %H:%M")
    rows[23]["fault"] = "entered before sampled"
    for i in (36, 37):
        sid = rows[i]["sample_id"]; rows[i]["sample_id"] = sid[:8] + str(int(sid[8:])); rows[i]["fault"] = "ID not padded"
    for s in (5, 12, 22):
        for i in (2 * s, 2 * s + 1):
            rows[i]["lot_id"] = ""; rows[i]["fault"] = (rows[i]["fault"] + "; " if rows[i]["fault"] else "") + "no batch key"
    out = list(rows)
    for k, src in enumerate(sorted([3, 14, 22, 47], reverse=True)):
        dup = dict(rows[src]); dup["fault"] = "exact duplicate"
        out.insert(src + 1, dup)
    for k, p in enumerate((12, 29, 51)):
        tgt = rows[(6, 26, 44)[k]]
        old = dict(tgt, value=f"{sup[k]}", is_current=0, status="superseded", fault="superseded retest")
        old["entered_at"] = (datetime.strptime(tgt["entered_at"], "%Y-%m-%d %H:%M") - timedelta(minutes=40)).strftime("%Y-%m-%d %H:%M")
        out.insert(p, old)
    df = pd.DataFrame(out)
    df.insert(0, "row", range(1, len(df) + 1))
    assert len(df) == 63
    save(df.drop(columns="fault"), "ch04_haze_export_raw.csv")
    save(df[df.fault != ""][["row", "fault"]], "ch04_planted_faults.csv")


# ---------------------------------------------------------------- chapters 5 and 6: haze and pH
def make_haze(seed=5):
    rng = np.random.default_rng(seed)
    x = rng.normal(0.36, 0.04, 120); x[80:] += 0.06
    save(pd.DataFrame(dict(result=range(1, 121), haze90_ebc=np.round(x, 3))), "ch05_haze.csv")


def make_ph(seed=9):
    rng = np.random.default_rng(seed)
    x = rng.normal(4.35, 0.03, 150); x[60:] += 0.015
    save(pd.DataFrame(dict(result=range(1, 151), ph=np.round(x, 3))), "ch06_ph.csv")


# ---------------------------------------------------------------- chapter 7: water check, beer chart, gauge study
def make_checks(seed=71):
    random.seed(seed)                          # same draws as figures/brewery-lab/fig-7-1.py

    def series(c, sd, d):
        out = []
        for i in range(60):
            e = random.gauss(0, sd)
            while abs(e) > 2.8 * sd: e = random.gauss(0, sd)
            out.append(c + (d if i >= 30 else 0) + e)
        return out
    beer = series(2.20, 0.129, 0.05)
    water = series(0.99820, 0.00001, 0.0002)
    save(pd.DataFrame(dict(result=range(1, 61), beer_ae_plato=np.round(beer, 3), water_check_g_cm3=np.round(water, 6))), "ch07_checks.csv")


def make_gauge(seed=72):
    """30 bitterness readings: repeatability sd 0.4, between analyst and day sd 0.45 (0.03 of it analyst x sample)."""
    rng = np.random.default_rng(seed)
    true = np.array([16.4, 17.3, 18.0, 18.9, 19.6])
    e = rng.normal(0, 1, (3, 5, 2)); e -= e.mean(2, keepdims=True)
    e *= math.sqrt(0.16 / ((e ** 2).sum() / 15))            # within cell MS = 0.16 exactly
    ia = rng.normal(0, 1, (3, 5)); ia -= ia.mean(0) + ia.mean(1, keepdims=True) - ia.mean()
    ia *= math.sqrt((0.16 + 2 * 0.03) * 8 / 2 / (ia ** 2).sum())   # MS analyst x sample = 0.22
    a = np.array([-1.0, 0.25, 0.75]); a -= a.mean()
    a *= math.sqrt((0.22 + 10 * 0.1725) * 2 / 10 / (a ** 2).sum())  # MS analyst = 0.22 + 10 x 0.1725
    y = true[None, :, None] + a[:, None, None] + ia[:, :, None] + e
    order = rng.permutation(30)
    rows = [dict(analyst="AN%d" % (i + 1), sample="RS%d" % (j + 1), replicate=k + 1, ibu=round(float(y[i, j, k]), 2))
            for i in range(3) for j in range(5) for k in range(2)]
    df = pd.DataFrame(rows); df.insert(0, "run_order", order + 1)
    save(df.sort_values(["analyst", "run_order"]), "ch07_gauge_study.csv")


# ---------------------------------------------------------------- chapter 8: 300 fermenter fills, seed 42
FILL_FEATS = ["ae_48h_plato", "og_plato", "mean_temp_c", "pitch_mcells_ml", "yeast_generation"]


def fill_features(rng, n):
    og = rng.normal(12.0, 0.08, n); temp = rng.normal(11.0, 0.35, n)
    pitch = rng.normal(12.0, 1.5, n); gen = rng.integers(1, 9, n)
    ae48 = rng.normal(6.8, 0.45, n) - 0.5 * (temp - 11) - 0.08 * (pitch - 12)
    return np.column_stack([ae48, og, temp, pitch, gen])


def fill_rdf(X):
    ae48, og, temp, pitch, gen = X.T
    return 68.3 - 1.9 * (ae48 - 6.8) + 0.5 * (temp - 11) + 0.05 * (pitch - 12) - 0.08 * (gen - 4.5) - 0.25 * np.maximum(ae48 - 7.3, 0) ** 2


def lab(og, r):
    ae = np.round(ae_for_rdf(og, r), 3)
    return ae, np.round(rdf(og, ae), 2)


def err_stats(p, y):
    d = p - y
    return round(np.mean(np.abs(d)), 2), round(d.mean(), 2), round(d.std(ddof=1), 2)


def gb_model():
    return GradientBoostingRegressor(n_estimators=150, max_depth=2, learning_rate=0.05, random_state=42)


def make_fills(seed=42):
    """Train on 225 fills, test on the newest 75: the test labels are drawn until chapter 8.2.2 reproduces."""
    rng = np.random.default_rng(seed)
    while True:
        Xtr = np.round(fill_features(rng, 225), 3)
        r = fill_rdf(Xtr) + rng.normal(0, 0.62, 225); r = r - r.mean() + 68.3
        aetr, ytr = lab(Xtr[:, 1], r)
        if round(ytr.mean(), 1) == 68.3: break
    lin = LinearRegression().fit(Xtr, ytr); gb = gb_model().fit(Xtr, ytr); base = ytr.mean()
    found = None
    while found is None:
        Xte = fill_features(rng, 75)
        p0 = lin.predict(Xte)
        Xte[:, 0] += ((p0 - p0.mean()) * (1.0 / p0.std(ddof=1) - 1) + (base - 0.23 - p0.mean())) / lin.coef_[0]
        Xte = np.round(Xte, 3)
        pl, pg = lin.predict(Xte), gb.predict(Xte)
        if not 0.022 < (pg - pl).mean() < 0.038: continue
        for _ in range(3000):
            e = rng.normal(0, 1, 75); e = (e - e.mean()) / e.std(ddof=1) * 0.67 - 0.06
            y0 = pl - e
            if abs(y0.std(ddof=1) - 1.22) > 0.006 or abs(np.mean(np.abs(e)) - 0.53) > 0.006: continue
            if abs(np.std(pg - y0, ddof=1) - 0.70) > 0.006 or abs(np.mean(np.abs(pg - y0)) - 0.54) > 0.006: continue
            if abs(np.mean(np.abs(base - y0)) - 1.03) > 0.006: continue
            aete, yte = lab(Xte[:, 1], y0)
            if (err_stats(pl, yte) == (0.53, -0.06, 0.67) and err_stats(pg, yte) == (0.54, -0.03, 0.70)
                    and err_stats(np.full(75, base), yte) == (1.03, 0.17, 1.22)):
                found = (Xte, aete, yte); break
    Xte, aete, yte = found
    X = np.vstack([Xtr, Xte]); ae = np.r_[aetr, aete]; y = np.r_[ytr, yte]
    start = datetime(2024, 6, 3)
    dates = [start + timedelta(days=round(i * 30.4 / 10.2)) for i in range(300)]
    seq = {}
    ids = []
    for i, d in enumerate(dates):
        yy = d.strftime("%y"); seq[yy] = seq.get(yy, 0) + 1
        ids.append("F%02d-%s-%03d" % (1 + i % 9, yy, seq[yy]))
    df = pd.DataFrame(X, columns=FILL_FEATS)
    df["yeast_generation"] = df.yeast_generation.astype(int)
    df.insert(0, "fill_id", ids); df.insert(1, "filled_on", [d.strftime("%Y-%m-%d") for d in dates])
    df["final_ae_plato"] = ae; df["rdf_pct"] = y
    df["split"] = ["train"] * 225 + ["test"] * 75
    save(df, "ch08_fills.csv")
    make_live_fills(rng, lin)


def make_live_fills(rng, lin):
    """Chapter 13: 44 fills after go live. Malt lot M-26-0188 arrives at live fill 25 and lifts final AE by 0.12."""
    while True:
        X = np.round(fill_features(rng, 44), 3); p = lin.predict(X)
        e = rng.normal(-0.06, 0.67, 44)
        e[24:34] = (e[24:34] - e[24:34].mean()) + (0.74 - 0.80)      # the 10 shadow fills: mean error 0.74
        e[34:] = e[34:] - e[34:].mean() + 0.02                        # the next 10: revalidation after the offset refit
        target = p - e
        target[24:] -= 0.80                                            # 0.12 degrees Plato of AE is about 0.80 RDF points
        ae, y = lab(X[:, 1], target)
        err = p - y
        if (all(-2.07 < v < 1.95 for v in err[:24]) and round(err[24:34].mean(), 2) == 0.74
                and abs(err[34:].mean() - err[24:34].mean()) < 0.2): break
    df = pd.DataFrame(X, columns=FILL_FEATS)
    df["yeast_generation"] = df.yeast_generation.astype(int)
    start = datetime(2026, 11, 2)
    df.insert(0, "fill_id", ["F%02d-26-%03d" % (1 + i % 9, 150 + i) for i in range(44)])
    df.insert(1, "filled_on", [(start + timedelta(days=round(i * 3))).strftime("%Y-%m-%d") for i in range(44)])
    df.insert(2, "malt_lot", ["M-26-0171"] * 24 + ["M-26-0188"] * 20)
    df["final_ae_plato"] = ae; df["rdf_pct"] = y
    save(df, "ch13_live_fills.csv")


# ---------------------------------------------------------------- chapter 9: micro and swab results, seed 7
N_PTS, N_DAYS, TRAIN = 26, 547, 365
HARD = [5, 6, 20, 21, 22]
POINTS = (["CEL.FV%02d" % i for i in range(1, 6)] + ["BBT.BT01.OUT", "BBT.BT02.OUT"] + ["BBT.BT%02d" % i for i in range(3, 9)]
          + ["FIL.OUT01", "FIL.OUT02", "PKG.B1.RINSE", "PKG.C1.RINSE", "PKG.B1.CROWN", "PKG.C1.SEAM", "CIP.RINSE01",
             "PKG.B1.FH01", "PKG.B1.FH02", "PKG.C1.FH01", "PKG.B1.CONV", "PKG.C1.CONV", "CIP.RINSE02"])
MICRO_FEATS = ["days_since_cip", "cip_short", "asset_age_years", "days_since_known_positive", "hard_fitting"]
CELL_POS = {(1, 0, 1): 3, (1, 0, 0): 107, (1, 1, 1): 2, (1, 1, 0): 88,
            (0, 0, 1): 30, (0, 0, 0): 12, (0, 1, 1): 12, (0, 1, 0): 29}


def micro_frame(rng, base=0.065, slip=0.3):
    pt = np.repeat(np.arange(N_PTS), N_DAYS); day = np.tile(np.arange(N_DAYS), N_PTS)
    age = np.round(rng.uniform(1, 18, N_PTS), 1)
    lag = np.where(rng.random(N_PTS) < 0.3, 5, 3)
    dsc = np.zeros(N_PTS * N_DAYS, int); short = np.zeros(N_PTS * N_DAYS, int)
    for p in range(N_PTS):
        d = 0
        while d < N_DAYS:
            gap = int(rng.integers(2, 6))
            s = int(rng.random() < (slip if (TRAIN + 35 <= d < TRAIN + 95 and p not in HARD) else base))
            for k in range(gap):
                if d + k < N_DAYS:
                    dsc[p * N_DAYS + d + k] = min(k, 10); short[p * N_DAYS + d + k] = s
            d += gap
    df = pd.DataFrame(dict(point=pt, day=day, days_since_cip=dsc, cip_short=short, asset_age_years=age[pt],
                           hard_fitting=np.isin(pt, HARD).astype(int), read_lag_days=lag[pt]))
    df["window"] = (df.day >= TRAIN).astype(int)
    return df


def known_positive_age(df, pos):
    """Days since the last positive whose plate had been read by 06:00 that day (capped at 90)."""
    out = np.zeros(len(df), int); lagv = df.read_lag_days.to_numpy()
    for p in range(N_PTS):
        sl = slice(p * N_DAYS, (p + 1) * N_DAYS); lag = lagv[p * N_DAYS]
        hits = np.flatnonzero(pos[sl]); v = np.full(N_DAYS, 90); j = -1
        for d in range(N_DAYS):
            while j + 1 < len(hits) and hits[j + 1] + lag <= d: j += 1
            if j >= 0: v[d] = min(90, d - hits[j])
        out[sl] = v
    return out


def top5(df, model):
    te = df[df.window == 1]
    p = model.predict_proba(te[MICRO_FEATS])[:, 1]
    order = np.lexsort((-p, te.day.to_numpy()))
    days = te.day.to_numpy()[order]
    first = np.r_[True, days[1:] != days[:-1]]
    rank = np.arange(len(days)) - np.maximum.accumulate(np.where(first, np.arange(len(days)), 0))
    return te.index.to_numpy()[order][rank < 5]


def micro_model():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))


def make_micro(seed=7):
    rng = np.random.default_rng(seed)
    while True:                                # 1,107 to 1,132 short CIP rows keep the 4.2 and 1.8 percent rates
        df = micro_frame(rng)
        if 1107 <= df.cip_short.sum() <= 1132: break
    cells = {k: df.index[(df.hard_fitting == k[0]) & (df.window == k[1]) & (df.cip_short == k[2])].to_numpy() for k in CELL_POS}
    pos = np.zeros(len(df), int)
    for k, n in CELL_POS.items():
        g = cells[k]; w = 1 + df.days_since_cip.to_numpy()[g] / 4
        pos[rng.choice(g, n, replace=False, p=w / w.sum())] = 1
    df["days_since_known_positive"] = known_positive_age(df, pos); df["positive"] = pos
    tr = df[df.window == 0]
    model = micro_model().fit(tr[MICRO_FEATS], tr.positive)
    for _ in range(5000):                      # move test positives within their cell until the top 5 a day find 94
        f = top5(df, model); found = int(pos[f].sum())
        if found == 94: break
        k = [(1, 1, 0), (0, 1, 0), (0, 1, 1)][rng.integers(3)]
        g = cells[k]; fl = np.isin(g, f)
        src = g[(pos[g] == 1) & (fl if found > 94 else ~fl)]; dst = g[(pos[g] == 0) & (~fl if found > 94 else fl)]
        if len(src) and len(dst):
            pos[rng.choice(src)] = 0; pos[rng.choice(dst)] = 1
            df["positive"] = pos; df["days_since_known_positive"] = known_positive_age(df, pos)
    assert found == 94
    start = datetime(2025, 4, 1)
    out = pd.DataFrame(dict(sample_point=[POINTS[p] for p in df.point], sampled_on=[(start + timedelta(days=int(d))).strftime("%Y-%m-%d") for d in df.day],
                            day=df.day))
    out = pd.concat([out, df[MICRO_FEATS + ["read_lag_days", "positive"]]], axis=1)
    save(out.sort_values(["day", "sample_point"]), "ch09_micro.csv")


# ---------------------------------------------------------------- chapter 10: scoring panel, seed 1011
TCRIT5 = ss.t.ppf(0.975, 5)
CLEAR = {1, 5, 6, 9, 10}                       # assessors 2, 6, 7, 10 and 11


def panel_totals(rng):
    """Integer totals that fix the ANOVA table: gap sums D, assessor sums S, session sums T."""
    while True:
        D = rng.integers(2, 7, 12); D[[5, 6, 9, 10]] = rng.integers(7, 11, 4); D[0], D[1], D[3] = 2, 11, 2
        if D.sum() == 68 and (D ** 2).sum() == 506: break
    while True:
        S = rng.integers(42, 67, 12); S[8] = 66; S[0] = 42
        if S.sum() == 664 and (S ** 2).sum() == 37414 and ((S - D) % 2 == 0).all(): break
    while True:
        T = rng.integers(104, 118, 6)
        if T.sum() == 664 and (T ** 2).sum() == 73560: break
    return D, S, T


def spread(total, n, rng, lo, hi):
    v = np.full(n, total // n); v[: total - v.sum()] += 1
    for _ in range(20):
        i, j = rng.choice(n, 2, replace=False)
        if v[i] < hi and v[j] > lo: v[i] += 1; v[j] -= 1
    return rng.permutation(v)


def panel_cost(std, d, T):
    tri = std + d
    bad = np.clip(-tri, 0, None).sum() + np.clip(tri - 9, 0, None).sum() + np.clip(-std, 0, None).sum() + np.clip(std - 9, 0, None).sum()
    c = 20 * bad + np.abs((2 * std + d).sum(0) - T).sum() + abs(int((std ** 2).sum() + (tri ** 2).sum()) - 3238)
    for a in range(12):
        sq = (d[a] ** 2).sum()
        if a == 1: c += abs(sq - 23)
        elif a in (0, 3): c += abs(sq - 8)
        else:
            sd = d[a].std(ddof=1)
            t = np.inf if sd == 0 else d[a].mean() / (sd / math.sqrt(6))
            c += 0 if ((TCRIT5 < t < 40) if a in CLEAR else (t < TCRIT5)) else 1
    return c


def make_panel(seed=1011):
    rng = np.random.default_rng(seed)
    D, S, T = panel_totals(rng)
    d = np.array([spread(D[a], 6, rng, -3, 4) for a in range(12)])
    std = np.array([spread((S[a] - D[a]) // 2, 6, rng, 0, 9) for a in range(12)])
    c, temp = panel_cost(std, d, T), 2.0
    while c:
        a = rng.integers(12); t, u = rng.choice(6, 2, replace=False); kind = rng.integers(3)
        arr = std if kind == 0 else d
        if kind == 2: arr[a, t], arr[a, u] = arr[a, u], arr[a, t]
        else: arr[a, t] += 1; arr[a, u] -= 1
        c2 = panel_cost(std, d, T)
        if c2 <= c or rng.random() < math.exp((c - c2) / temp): c = c2
        elif kind == 2: arr[a, t], arr[a, u] = arr[a, u], arr[a, t]
        else: arr[a, t] -= 1; arr[a, u] += 1
        temp = max(0.15, temp * 0.9998)
    rows = []
    for a in range(12):
        for t in range(6):
            for s, v in (("standard", std[a, t]), ("trial", std[a, t] + d[a, t])):
                rows.append(dict(assessor=a + 1, session=t + 1, sample=s, ibu=18 if s == "standard" else 20, bitterness=int(v)))
    save(pd.DataFrame(rows), "ch10_scores.csv")


# ---------------------------------------------------------------- chapter 11: 400 tasting records, seed 1102
TASTERS = ["T%02d" % i for i in range(1, 19)]
REC_COUNTS = {"T03": 27, "T07": 20, "T10": 21, "T13": 21, "T12": 24}
OFFSET = {"T03": (1.68, 7.6), "T07": (-0.91, 5.1), "T10": (0.80, 4.5), "T13": (-1.09, 4.8)}
SPIKES = {"T01": 6, "T02": 5, "T03": 5, "T04": 5, "T05": 5, "T06": 5, "T07": 4, "T08": 5, "T09": 4, "T10": 6,
          "T11": 4, "T12": 2, "T13": 3, "T14": 4, "T15": 3, "T16": 4, "T17": 4, "T18": 4}
HIGH_LOT, EXAMPLE_LOT = 39, 42                 # bitterness mean 5.38 (T03 and T10 seated); the 138 ppb lot with 5 of 8 papery
BAND = {"malt": 4, "hop_aroma": 3, "bitterness": 4, "esters": 2, "body": 4, "finish": 4}
OTHER_TAGS = ["buttery"] * 24 + ["cooked vegetable"] * 26 + ["green apple"] * 26 + ["sulphury"] * 24


def seat(rng):
    counts = dict(REC_COUNTS)
    for i, t in enumerate(t for t in TASTERS if t not in REC_COUNTS): counts[t] = 23 if i == 0 else 22
    while True:
        left, seats = dict(counts), []
        for s in range(50):
            forced = ["T03", "T10"] if s == HIGH_LOT else []
            pool = [t for t in TASTERS if left[t] > 0 and t not in forced]
            if any(left[t] == 0 for t in forced) or len(pool) < 8 - len(forced): break
            w = np.array([left[t] for t in pool], float)
            pick = forced + list(rng.choice(pool, 8 - len(forced), replace=False, p=w / w.sum()))
            for t in pick: left[t] -= 1
            seats.append(sorted(pick))
        if len(seats) == 50 and not any(left.values()): return seats


def bitter_cost(b, sess, tid):
    tot = np.bincount(sess, b, minlength=50); off = b - (tot[sess] - b) / 7
    c = 0.0
    for i, t in enumerate(TASTERS):
        o = off[tid == i]; m = o.mean()
        if t in OFFSET:
            z = abs(m) / (o.std(ddof=1) / math.sqrt(len(o)))
            c += 50 * max(0, abs(m - OFFSET[t][0]) - 0.004) + 5 * max(0, abs(z - OFFSET[t][1]) - 0.04)
        else:
            c += 50 * max(0, abs(m) - 0.70)
    for s in range(50):
        c += abs(tot[s] - 43) if s == HIGH_LOT else abs(tot[s] - 33) if s == EXAMPLE_LOT else max(0, 25 - tot[s]) + max(0, tot[s] - 39)
    return c


def make_tasting(seed=1102):
    rng = np.random.default_rng(seed)
    _, tpo, pap, _ = ch11_tpo_lots.find()
    seats = seat(rng)
    sess = np.repeat(np.arange(50), 8); tid = np.array([TASTERS.index(t) for s in seats for t in s])
    bias = np.array([OFFSET.get(t, (0, 0))[0] for t in TASTERS])
    b = np.clip(np.round(4 + bias[tid] + rng.normal(0, 0.8, 400)), 0, 9).astype(int)
    c, temp = bitter_cost(b, sess, tid), 1.0
    while c > 0:
        r = rng.integers(400); st = rng.choice([-1, 1])
        if not 0 <= b[r] + st <= 9: continue
        b[r] += st
        c2 = bitter_cost(b, sess, tid)
        if c2 <= c or rng.random() < math.exp((c - c2) / temp): c = c2
        else: b[r] -= st
        temp = max(0.02, temp * 0.9997)
    # tags: papery as the lot set says (never by T12), then the other off flavours on records left
    tag = np.array(["none"] * 400, dtype=object)
    for s in range(50):
        idx = [i for i in range(s * 8, s * 8 + 8) if TASTERS[tid[i]] != "T12"]
        tag[rng.choice(idx, pap[s], replace=False)] = "papery"
    free = np.flatnonzero(tag == "none")
    tag[rng.choice(free, len(OTHER_TAGS), replace=False)] = rng.permutation(OTHER_TAGS)
    # true to type: 7 lots with 5 or more papery tags fail the half rule; elsewhere at most 3 vote no
    fail_lots = [s for s in range(50) if pap[s] >= 5]
    ttt = np.ones(400, int)
    for s in range(50):
        idx = np.arange(s * 8, s * 8 + 8)
        no = idx[tag[idx] == "papery"] if s in fail_lots else idx[tag[idx] != "none"][:3]
        ttt[no] = 0
    scores = {k: np.clip(np.round(v + rng.normal(0, 0.55, 400)), v - 2, v + 2).astype(int) for k, v in BAND.items() if k != "bitterness"}
    order = rng.permutation(50)                # tasting order is not TPO order
    day0 = datetime(2026, 9, 28)
    sess_time = {}
    for k, s in enumerate(order):
        d = day0 + timedelta(days=(k // 2) // 5 * 7 + (k // 2) % 5, hours=11 if k % 2 == 0 else 14)
        sess_time[s] = d
    lot_id, runs = {}, {}
    for s in sorted(range(50), key=lambda s: sess_time[s]):
        packed = (sess_time[s] - timedelta(days=4 + s % 3)).strftime("%y%m%d"); runs[packed] = runs.get(packed, 0) + 1
        lot_id[s] = "L%s-B1-%d" % (packed, runs[packed])
    fill_id = {s: "F%02d-26-%03d" % (1 + s % 9, 60 + s) for s in range(50)}
    rows = []
    for i in range(400):
        s = sess[i]
        rows.append(dict(record_id="TR%04d" % (i + 1), session_at=sess_time[s].strftime("%Y-%m-%d %H:%M"), taster=TASTERS[tid[i]],
                         fill_id=fill_id[s], lot_id=lot_id[s], malt=scores["malt"][i], hop_aroma=scores["hop_aroma"][i],
                         bitterness=b[i], esters=scores["esters"][i], body=scores["body"][i], finish=scores["finish"][i],
                         off_flavour=tag[i], true_to_type="yes" if ttt[i] else "no"))
    rec = pd.DataFrame(rows).sort_values(["session_at", "taster"])
    rec["record_id"] = ["TR%04d" % (i + 1) for i in range(400)]
    complaints = {31, 41, 43, 44, 45, 49}
    lots = pd.DataFrame(dict(lot_id=[lot_id[s] for s in range(50)], fill_id=[fill_id[s] for s in range(50)], pack="bottle",
                             tpo_ppb=tpo, staling_complaint=[int(s in complaints) for s in range(50)]))
    save(rec, "ch11_tasting_records.csv"); save(lots, "ch11_lots.csv")
    save(pd.DataFrame(dict(taster=TASTERS, spikes_named_of_6=[SPIKES[t] for t in TASTERS])), "ch11_spikes.csv")
    words = [("cardboard", "papery"), ("wet paper", "papery"), ("stale", "papery"), ("old", "papery"), ("butterscotch", "buttery"),
             ("movie popcorn", "buttery"), ("slick", "buttery"), ("cut apple", "green apple"), ("emulsion paint", "green apple"),
             ("nail varnish", "solvent (ethyl acetate)"), ("thinners", "solvent (ethyl acetate)"), ("solvent", "solvent (ethyl acetate)"),
             ("struck match", "sulphury"), ("drains", "sulphury"), ("eggy", "sulphury")]
    save(pd.DataFrame(words, columns=["word", "controlled_term"]), "ch11_descriptor_map.csv")
    raw = ["Wet paper on the nose", "slight cardboard", "STALE finish", "butterscotch, low", "eggy at first then clean",
           "cut apple", "grassy", "struck match on opening", "clean", "nail varnish hint", "old, tired", "honey note"]
    save(pd.DataFrame(dict(comment=raw)), "ch11_raw_comments.csv")


# ---------------------------------------------------------------- chapter 8.4 DO run, chapter 12 test set, chapter 14 DO series
def make_small(seed=14):
    save(pd.DataFrame(dict(reading=range(1, 14), hour=[f"{6 + i:02d}:00" for i in range(13)],
                           do_ppb=[18, 26, 21, 24, 19, 25, 22, 23, 26, 29, 33, 38, 46])), "ch08_do_filler_run.csv")
    qs = [("What is the DO limit for bright beer?", "SPEC-REL-004", "rev 6", "SPEC-REL-004", "rev 6", "yes"),
          ("How long are aerobic plates incubated?", "SOP-MIC-012", "rev 3", "SOP-MIC-012", "rev 3", "yes"),
          ("What haze limit applies at 25 degrees?", "SPEC-REL-004", "rev 6", "SPEC-REL-004", "rev 5", "yes"),
          ("How many buffers calibrate the pH meter?", "SOP-CHE-031", "rev 2", "SOP-CHE-031", "rev 2", "yes"),
          ("Who signs a pack lot to dispatch?", "SOP-QA-001", "rev 9", "SOP-QA-001", "rev 9", "yes"),
          ("What is the chill haze limit?", "SPEC-REL-004", "rev 6", "", "", "yes"),
          ("How is a positive anaerobic plate handled after dispatch?", "SOP-QA-017", "rev 4", "SOP-QA-017", "rev 4", "yes"),
          ("What ATP reading triggers action?", "SOP-HYG-008", "rev 2", "SOP-HYG-008", "rev 2", "yes"),
          ("What is the forced ageing cycle?", "SOP-CHE-044", "rev 1", "", "", "no"),
          ("What is the TPO limit for cans?", "SPEC-REL-004", "rev 6", "SPEC-REL-004", "rev 6", "yes")]
    save(pd.DataFrame(qs, columns=["question", "answer_doc", "answer_rev", "cited_doc", "cited_rev", "answered"]), "ch12_sop_testset.csv")
    rng = np.random.default_rng(seed)
    n = 305
    x = np.exp(rng.normal(math.log(28), 0.18, n))
    x[200:214] *= np.linspace(1.05, 1.6, 14)  # a filter outlet seal wearing over two weeks
    x[262] *= 1.9                             # one bad flush on the sample line
    start = datetime(2025, 8, 1)
    save(pd.DataFrame(dict(result=range(1, n + 1), sampled_on=[(start + timedelta(days=round(i * 30.4 / 20.3))).strftime("%Y-%m-%d") for i in range(n)],
                           bright_tank=["BT%02d" % (1 + i % 8) for i in range(n)], do_ppb=np.round(x).astype(int))), "ch14_do_release.csv")


# ---------------------------------------------------------------- workbooks with live formulas
def make_sheets():
    from openpyxl import Workbook
    SHEETS.mkdir(exist_ok=True)
    ph = pd.read_csv(DATA / "ch06_ph.csv")
    wb = Workbook(); ws = wb.active; ws.title = "CUSUM"
    ws.append(["Chapter 6 CUSUM recipe on the 150 synthetic pH results. Baseline from results 1 to 60."])
    ws.append(["Baseline mean", "=AVERAGE(B8:B67)"]); ws.append(["Average moving range", "=AVERAGE(C9:C67)"])
    ws.append(["Sigma (AMR / 1.128)", "=B3/1.128"]); ws.append(["k = 0.5 sigma", "=0.5*B4"]); ws.append(["h = 5 sigma", "=5*B4"])
    ws.append(["result", "pH", "moving range", "C", "alarm"])
    for i, v in enumerate(ph.ph, start=8):
        mr = "" if i == 8 else f"=ABS(B{i}-B{i-1})"
        c = f"=MAX(0,B{i}-($B$2+$B$5))" if i == 8 else f"=MAX(0,D{i-1}+B{i}-($B$2+$B$5))"
        ws.append([i - 7, float(v), mr, c, f'=IF(D{i}>$B$6,"alarm","")'])
    ws["G2"] = "First alarm (result number)"; ws["H2"] = '=MATCH("alarm",E8:E157,0)'
    wb.save(SHEETS / "ch06-cusum.xlsx")
    g = pd.read_csv(DATA / "ch07_gauge_study.csv").sort_values(["analyst", "sample", "replicate"])
    wb = Workbook(); ws = wb.active; ws.title = "Readings"
    ws.append(["run_order", "analyst", "sample", "replicate", "ibu"])
    for r in g.itertuples(index=False): ws.append([int(r.run_order), r.analyst, r.sample, int(r.replicate), float(r.ibu)])
    calc = wb.create_sheet("Gauge study")
    n = len(g) + 1
    rows = [("Bitterness gauge study: 3 analysts x 5 samples x 2 readings", ""),
            ("Grand mean", f"=AVERAGE(Readings!E2:E{n})"),
            ("SS total", f"=DEVSQ(Readings!E2:E{n})"),
            ("SS analyst", "=10*(" + "+".join(f'(AVERAGEIFS(Readings!E2:E{n},Readings!B2:B{n},"AN{a}")-B2)^2' for a in (1, 2, 3)) + ")"),
            ("SS sample", "=6*(" + "+".join(f'(AVERAGEIFS(Readings!E2:E{n},Readings!C2:C{n},"RS{s}")-B2)^2' for s in range(1, 6)) + ")"),
            ("SS within (repeat pairs)", "=" + "+".join(f'(SUMIFS(Readings!E2:E{n},Readings!B2:B{n},"AN{a}",Readings!C2:C{n},"RS{s}",Readings!D2:D{n},1)-SUMIFS(Readings!E2:E{n},Readings!B2:B{n},"AN{a}",Readings!C2:C{n},"RS{s}",Readings!D2:D{n},2))^2/2' for a in (1, 2, 3) for s in range(1, 6))),
            ("SS analyst x sample", "=B3-B4-B5-B6"),
            ("MS analyst (2 df)", "=B4/2"), ("MS analyst x sample (8 df)", "=B7/8"), ("MS within (15 df)", "=B6/15"),
            ("Repeatability sd", "=SQRT(B10)"),
            ("Between analyst and day sd", "=SQRT(MAX(0,(B8-B9)/10)+MAX(0,(B9-B10)/2))"),
            ("Within lab sd", "=SQRT(B11^2+B12^2)"),
            ("Tolerance (16 to 20 IBU)", 4),
            ("Precision to tolerance", "=6*B13/B14"),
            ("Repeatability alone", "=6*B11/B14")]
    for r in rows: calc.append(list(r))
    wb.save(SHEETS / "ch07-gauge-study.xlsx")
    wb = Workbook(); ws = wb.active; ws.title = "Triangle"
    ws.append(["Chapter 10 triangle test in one cell. Type 1 for a correct pick, 0 for a wrong one."])
    ws.append(["taster", "correct (1 or 0)"])
    for i in range(18): ws.append([i + 1, 1 if i < 9 else 0])
    ws["D2"] = "Tasters"; ws["E2"] = "=COUNT(B3:B20)"
    ws["D3"] = "Correct"; ws["E3"] = "=SUM(B3:B20)"
    ws["D4"] = "p value (one sided)"; ws["E4"] = "=1-_xlfn.BINOM.DIST(E3-1,E2,1/3,TRUE)"
    ws["D6"] = "Check: 8 of 18"; ws["E6"] = "=1-_xlfn.BINOM.DIST(7,18,1/3,TRUE)"
    ws["D7"] = "Check: 9 of 18"; ws["E7"] = "=1-_xlfn.BINOM.DIST(8,18,1/3,TRUE)"
    ws["D8"] = "Check: 11 of 18"; ws["E8"] = "=1-_xlfn.BINOM.DIST(10,18,1/3,TRUE)"
    ws["D10"] = "Correct needed at 5 percent"; ws["E10"] = "=CRITBINOM(E2,1/3,0.95)+1"
    wb.save(SHEETS / "ch10-triangle.xlsx")


if __name__ == "__main__":
    make_week(); make_dirty_export(); make_haze(); make_ph(); make_checks(); make_gauge()
    make_fills(); make_micro(); make_panel(); make_tasting(); make_small(); make_sheets()
    print("wrote", len(list(DATA.glob("*.csv"))), "CSV files and", len(list(SHEETS.glob("*.xlsx"))), "workbooks")
