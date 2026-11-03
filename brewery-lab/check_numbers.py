"""Asserts that every number the book prints from the companion data comes out of it.

Run python3 make_data.py first, then python3 check_numbers.py. Prints one line per check and fails on any miss.
Each check rounds to the precision the chapter prints.
"""
import math
from decimal import ROUND_HALF_UP, Decimal
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as ss
from scipy.stats import norm

import make_data as md

D = Path(__file__).resolve().parent / "data"
FAILS = []


def half_up(x, places):
    q = Decimal(1).scaleb(-places)
    return float(Decimal(repr(round(float(x), 10))).quantize(q, rounding=ROUND_HALF_UP))


def ok(label, got, want, places=None):
    g = half_up(got, places) if places is not None else got
    good = abs(g - want) < 1e-9 if isinstance(want, float) else g == want
    print(("ok   " if good else "MISS ") + f"{label}: {g} (book {want})")
    if not good: FAILS.append(label)


NOTES = []


def note(label, got, want, places):
    """A book sum that uses no companion data; a mismatch is listed for the author, not failed."""
    g = half_up(got, places)
    print(("ok   " if g == want else "NOTE ") + f"{label}: {g} (book {want}, a sum, not from the data)")
    if g != want: NOTES.append(f"{label}: {got:.3f} against {want}")


def csv(name):
    return pd.read_csv(D / name, keep_default_na=False)


# ------------------------------------------------ run lengths by Markov chain (chapters 5, 6 and 13)
def arl_shewhart(delta, L=3.0):
    return 1 / (1 - norm.cdf(L - delta) + norm.cdf(-L - delta))


def arl_runs(delta, n=8, limit=None):
    """Eight in a row on one side of the centre line; with limit=3 the beyond-limit rule is added."""
    up, dn = 1 - norm.cdf(-delta), norm.cdf(-delta)
    out = 0.0 if limit is None else 1 - norm.cdf(limit - delta) + norm.cdf(-limit - delta)
    up_in = up - (0.0 if limit is None else 1 - norm.cdf(limit - delta))
    dn_in = dn - (0.0 if limit is None else norm.cdf(-limit - delta))
    m = 2 * (n - 1)                                   # states: run of 1..7 above, 1..7 below
    Q = np.zeros((m, m))
    for s in range(m):
        side, k = divmod(s, n - 1)
        if side == 0:
            if k + 1 < n - 1: Q[s, k + 1] = up_in
            Q[s, n - 1] = dn_in
        else:
            if k + 1 < n - 1: Q[s, n - 1 + k + 1] = dn_in
            Q[s, 0] = up_in
    t = np.linalg.solve(np.eye(m) - Q, np.ones(m))
    return 1 + up_in * t[0] + dn_in * t[n - 1]


def arl_cusum(delta, k=0.5, h=5.0, m=300):
    """Brook and Evans chain for the two sided CUSUM: state 0 holds C = 0, state j holds C near j x w."""
    w = 2 * h / (2 * m - 1)
    def one(d):
        Q = np.empty((m, m))
        for i in range(m):
            c = i * w
            up = norm.cdf((np.arange(m) + 0.5) * w - c + k - d)
            Q[i] = np.diff(np.r_[0.0, up]); Q[i, 0] = up[0]
        return np.linalg.solve(np.eye(m) - Q, np.ones(m))[0]
    return 1 / (1 / one(delta) + 1 / one(-delta))


def arl_ewma(delta, lam=0.2, L=3.0, m=401):
    lim = L * math.sqrt(lam / (2 - lam))
    w = 2 * lim / m
    mids = -lim + (np.arange(m) + 0.5) * w
    lo = mids - w / 2; hi = mids + w / 2
    Q = np.empty((m, m))
    for i, z in enumerate(mids):
        Q[i] = norm.cdf((hi - (1 - lam) * z) / lam - delta) - norm.cdf((lo - (1 - lam) * z) / lam - delta)
    t = np.linalg.solve(np.eye(m) - Q, np.ones(m))
    return t[m // 2]


# ------------------------------------------------ chapters 1 and 3
def week():
    s, r = csv("week_sample.csv"), csv("week_result.csv")
    ok("ch1 samples in the week (60 x 7)", len(s), 420)
    ok("ch1 samples a day", set(s.sample_id.str[1:7].value_counts()), {60})
    ok("ch1 results in the week, well over a thousand", len(r) > 1000, True)
    by = s.stage.value_counts()
    ok("ch1 micro and hygiene a day (12 + 14)", (by["process micro"] + by["hygiene"]) / 7, 26.0)
    micro = r[r.test_code.isin(["MIC_MEM", "MIC_PLATE", "MIC_RINSE", "ATP"])]
    lim = {"MIC_MEM": 5, "MIC_PLATE": 10, "MIC_RINSE": 10, "ATP": 301}
    hits = sum(pd.to_numeric(v) >= lim[c] for v, c in zip(micro.value, micro.test_code))
    ok("ch1 share of micro results at the action limit, about 2 percent", round(100 * hits / len(micro)), 2)
    groups = {"brew": ["wort"], "fill": ["yeast", "fermentation", "maturation"], "micro": ["process micro"], "ingredient": ["raw material"],
              "bright or pack": ["filtration and bright beer", "packaging", "shelf life", "sensory"], "equipment": ["water", "hygiene"]}
    want = {"brew": 2, "fill": 10, "bright or pack": 17, "micro": 12, "ingredient": 1, "equipment": 18}
    for g, st in groups.items(): ok(f"ch4.2 samples a day joining to {g}", by[st].sum() / 7, float(want[g]))
    a = s[s.sample_id == "S261103-004"].iloc[0]
    ok("ch1 S261103-004 is bright tank 3 at 06:05", (a.sample_point, a.sampled_at[-5:]), ("BBT.BT03", "06:05"))
    b = r[r.sample_id == "S261031-017"].set_index("test_code")
    ok("ch3 S261031-017 DO", int(b.at["DO", "value"]), 31)
    ok("ch3 S261031-017 HAZE90", float(b.at["HAZE90", "value"]), 0.42)
    ok("ch3 S261031-017 HAZE25", float(b.at["HAZE25", "value"]), 0.44)
    t = [datetime.strptime(x, "%Y-%m-%d %H:%M") for x in ("2026-10-31 09:05", b.at["DO", "tested_at"], b.at["DO", "entered_at"], b.at["DO", "approved_at"])]
    ok("ch3 pull to approval, minutes (4 h 15)", (t[3] - t[0]).seconds // 60, 255)
    ok("ch3 DO over target, ppb", 31 - 30, 1)
    ok("ch3 rota spare shifts", 4 * 6 - 3 * 7, 3)


# ------------------------------------------------ chapter 2
def ch2():
    re = 0.1808 * 12 + 0.8192 * 2.2; abw = (12 - re) / (2.0665 - 0.010665 * 12); r0 = md.rdf(12.0, 2.2)
    ok("ch2 RE", re, 3.972, 3); ok("ch2 ABW", abw, 4.141, 3); ok("ch2 RDF", r0, 68.3, 1)
    ok("ch2 apparent attenuation", 100 * (1 - 2.2 / 12), 81.7, 1); ok("ch2 gap between attenuations", 100 * (1 - 2.2 / 12) - r0, 13.4, 1)
    ok("ch2 RDF at AE 2.25", md.rdf(12.0, 2.25), 68.0, 1)
    ok("ch2 RDF change for OG sd 0.015", abs(md.rdf(12.015, 2.2) - r0), 0.02, 2)
    rng = np.random.default_rng(2)
    sim = md.rdf(rng.normal(12, 0.015, 200000), rng.normal(2.2, 0.05, 200000))
    ok("ch2 combined RDF sd by simulation", sim.std(), 0.33, 2)
    ok("ch2 two results may differ by", 2.8 * 0.33, 0.9, 1)
    ok("ch2 meter alone in degrees Plato", 0.00001 / 0.00392, 0.003, 3); ok("ch2 handling worse by", 0.05 / 0.003, 17, 0)
    ok("ch2 Nernst slope at 20 C", 0.19842 * 293.15, 58.2, 1)
    ok("ch2 clean plate at 1 CFU", 100 * math.exp(-1), 37, 0); ok("ch2 clean plate at 0.5 CFU", 100 * math.exp(-0.5), 61, 0)
    for k, lo, hi, p in ((1, 0.03, 5.6, (2, 1)), (4, 1.1, 10.2, (1, 1))):
        ok(f"ch2 Poisson interval low, count {k}", ss.chi2.ppf(0.025, 2 * k) / 2, lo, p[0])
        ok(f"ch2 Poisson interval high, count {k}", ss.chi2.ppf(0.975, 2 * k + 2) / 2, hi, p[1])
    ok("ch2 DO band top, between labs", 38 + 1.96 * 6 < 50, True)
    ok("ch2 bitterness range low", 19.8 - 1.96 * 0.6, 18.6, 1); ok("ch2 bitterness range high", 19.8 + 1.96 * 0.6, 21.0, 1)


# ------------------------------------------------ chapter 4
def ch4():
    raw = csv("ch04_haze_export_raw.csv")
    ok("ch4 raw rows", len(raw), 63)
    cols = [c for c in raw.columns if c != "row"]
    dd = raw.drop_duplicates(subset=cols)
    ok("ch4 exact duplicates", len(raw) - len(dd), 4); ok("ch4 rows left", len(dd), 59)
    num = pd.to_numeric(dd.value, errors="coerce")
    ok("ch4 values stored as text", int(num.isna().sum()), 2)
    ok("ch4 text values read 0.41 EBC", set(dd.value[num.isna()]), {"0.41 EBC"})
    ok("ch4 blank units", int((dd.unit == "").sum()), 1)
    val = pd.to_numeric(dd.value.str.replace(" EBC", ""), errors="coerce")
    ok("ch4 values beyond the 0.5 limit by a factor", int((val > 1).sum()), 1)
    ok("ch4 rows entered before sampled", int((dd.entered_at < dd.sampled_at).sum()), 1)
    ok("ch4 IDs without padding", int((~dd.sample_id.str.match(r"^S\d{6}-\d{3}$")).sum()), 2)
    ok("ch4 samples with no batch key", dd[dd.lot_id == ""].sample_id.nunique(), 3)
    ok("ch4 superseded retests", int((dd.is_current == 0).sum()), 3); ok("ch4 current rows", int((dd.is_current == 1).sum()), 56)
    ok("ch4 censored as 0", 2 / 5, 0.4, 1); ok("ch4 censored as 1", 6 / 5, 1.2, 1)
    ok("ch4 mean of three repeats", (0.41 + 0.43 + 0.52) / 3, 0.45, 2); ok("ch4 critical range", 3.3 * 0.03, 0.10, 2)
    ok("ch4 spread of the three", 0.52 - 0.41, 0.11, 2)


# ------------------------------------------------ chapter 5
def ch5():
    x = csv("ch05_haze.csv").haze90_ebc.to_numpy()
    b = x[:60]; cl = b.mean(); amr = np.abs(np.diff(b)).mean(); ucl, lcl = cl + 2.66 * amr, cl - 2.66 * amr
    ok("ch5 baseline mean", cl, 0.351, 3); ok("ch5 average moving range", amr, 0.0451, 4)
    ok("ch5 lower limit", lcl, 0.231, 3); ok("ch5 upper limit", ucl, 0.471, 3)
    ok("ch5 moving range limit", 3.267 * amr, 0.147, 3); ok("ch5 sigma", amr / 1.128, 0.040, 3)
    ok("ch5 points beyond a limit", [i + 1 for i, v in enumerate(x) if v > ucl or v < lcl], [92, 106, 109])
    ok("ch5 result 92", x[91], 0.474, 3)
    run, side, first = 0, 0, None
    for i, v in enumerate(x, 1):
        s = 1 if v > cl else -1
        run = run + 1 if s == side else 1; side = s
        if run == 8 and first is None: first = i
    ok("ch5 eighth in a row", first, 88)
    ok("ch5 moving range chart quiet", bool((np.abs(np.diff(x)) < 3.267 * amr).all()), True)
    ok("ch5 mean of 81 to 120", x[80:].mean(), 0.412, 3); ok("ch5 highest result", x.max(), 0.496, 3)
    ok("ch5 every result passes 0.5", bool((x <= 0.5).all()), True)
    ok("ch5 margin lost, percent", 100 * (1 - (0.5 - 0.412) / (0.5 - 0.351)), 41, 0)
    ok("ch5 one point ARL", arl_shewhart(0), 370, 0); ok("ch5 eight in a row ARL", arl_runs(0), 255, 0)
    ok("ch5 both rules ARL, exact", arl_runs(0, limit=3), 153, 0)
    ok("ch5 both rules by adding rates", 1 / (1 / 370 + 1 / 255), 151, 0)
    ok("ch5 months between false alarms", 153 / 20.3, 7.5, 1)


# ------------------------------------------------ chapter 6
def ch6():
    x = csv("ch06_ph.csv").ph.to_numpy()
    b = x[:60]; t = b.mean(); amr = np.abs(np.diff(b)).mean(); s = amr / 1.128
    ok("ch6 baseline mean", t, 4.347, 3); ok("ch6 average moving range", amr, 0.0376, 4); ok("ch6 sigma", s, 0.0333, 4)
    ok("ch6 limits low", t - 3 * s, 4.247, 3); ok("ch6 limits high", t + 3 * s, 4.447, 3)
    ok("ch6 mean after the step", x[60:].mean(), 4.369, 3)
    ok("ch6 results after the step beyond a limit", int((np.abs(x[60:] - t) > 3 * s).sum()), 0)
    ok("ch6 k", 0.5 * s, 0.0166, 4); ok("ch6 h", 5 * s, 0.166, 3)
    c, C = 0.0, []
    for v in x: c = max(0, c + v - (t + 0.5 * s)); C.append(c)
    alarm = next(i for i in range(60, 150) if C[i] > 5 * s) + 1
    ok("ch6 CUSUM alarm result", alarm, 94); ok("ch6 C at alarm", C[alarm - 1], 0.191, 3)
    w = 3 * s * math.sqrt(0.2 / 1.8); z, Z = t, []
    for v in x: z = 0.2 * v + 0.8 * z; Z.append(z)
    ok("ch6 EWMA half width", w, 0.0333, 4)
    ok("ch6 EWMA out result", next(i for i in range(60, 150) if abs(Z[i] - t) > w) + 1, 93)
    ok("ch6 Cp", 0.3 / (6 * s), 1.50, 2); ok("ch6 Cpk", (t - 4.2) / (3 * s), 1.47, 2)
    ok("ch6 sample sd", b.std(ddof=1), 0.0297, 4); ok("ch6 Ppk", (t - 4.2) / (3 * b.std(ddof=1)), 1.65, 2)
    ok("ch6 Cpk at the new level", (4.5 - x[60:].mean()) / (3 * s), 1.31, 2)
    ok("ch6 test share of variance, percent", 100 * 0.02 ** 2 / s ** 2, 36, 0)
    for label, d, want, p in (("one point", 0.3, 253, 0), ("one point", 0.5, 155, 0), ("one point", 1, 44, 0)):
        ok(f"ch6 ARL {label} at {d} sigma", arl_shewhart(d), want, p)
    for d, want, p in ((0.3, 117, 0), (0.5, 59, 0), (1, 19, 0)): ok(f"ch6 ARL eight in a row at {d} sigma", arl_runs(d), want, p)
    for d, want, p in ((0, 465, 0), (0.3, 103, 0), (0.5, 38, 0), (1, 10.4, 1)): ok(f"ch6 ARL CUSUM at {d} sigma", arl_cusum(d), want, p)
    ok("ch6 ARL upper CUSUM alone, no shift, about 930", 2 * arl_cusum(0), 930, -1)
    for d, want, p in ((0, 560, -1), (0.3, 121, 0), (0.5, 44, 0), (1, 11, 0)): ok(f"ch6 ARL EWMA at {d} sigma", arl_ewma(d), want, p)
    rng = np.random.default_rng(44)                   # the 3,000 run test
    sims = rng.normal(4.35, 0.03, (3000, 150)); sims[:, 60:] += 0.015
    cl = sims[:, :60].mean(1, keepdims=True); sg = np.abs(np.diff(sims[:, :60], axis=1)).mean(1, keepdims=True) / 1.128
    def first(m): return np.where(m.any(1), m.argmax(1) + 1, 0)
    f1 = first(np.abs(sims[:, 60:] - cl) > 3 * sg)
    side = np.sign(sims - cl); run = np.ones(3000); r8 = np.zeros((3000, 90), bool); cc = np.zeros(3000); cs = np.zeros((3000, 90), bool)
    for i in range(150):
        if i: run = np.where(side[:, i] == side[:, i - 1], run + 1, 1)
        cc = np.maximum(0, cc + sims[:, i] - (cl[:, 0] + 0.5 * sg[:, 0]))
        if i >= 60: r8[:, i - 60] = run >= 8; cs[:, i - 60] = cc > 5 * sg[:, 0]
    f8, fc = first(r8), first(cs)
    ok("ch6 run test, one point caught, percent", 100 * (f1 > 0).mean(), 47, 0)
    ok("ch6 run test, eight in a row caught, percent", 100 * (f8 > 0).mean(), 78, 0)
    ok("ch6 run test, eight in a row median", int(np.median(f8[f8 > 0])), 29)
    ok("ch6 run test, CUSUM caught, percent", 100 * (fc > 0).mean(), 85, 0)
    ok("ch6 run test, CUSUM median", int(np.median(fc[fc > 0])), 22)


# ------------------------------------------------ chapter 7
def ch7():
    c = csv("ch07_checks.csv")
    ok("ch7 water step in sigma", 0.0002 / 0.00001, 20.0, 0)
    ok("ch7 water steps from result 31", round(c.water_check_g_cm3[30:].mean() - c.water_check_g_cm3[:30].mean(), 4), 0.0002)
    ok("ch7 beer step in sigma", 0.05 / 0.129, 0.39, 2)
    ok("ch7 CUSUM fills to find 0.39 sigma, about 64", arl_cusum(0.05 / 0.129), 64, 0)
    ok("ch7 months", 64 / 10.2, 6.3, 1)
    ok("ch7 RDF at AE 2.25", md.rdf(12.0, 2.25), 67.97, 2)
    g = csv("ch07_gauge_study.csv")
    y = g.ibu.to_numpy(); gm = y.mean()
    ss_a = 10 * ((g.groupby("analyst").ibu.mean() - gm) ** 2).sum()
    ss_s = 6 * ((g.groupby("sample").ibu.mean() - gm) ** 2).sum()
    cell = g.groupby(["analyst", "sample"]).ibu
    ss_e = ((g.ibu - cell.transform("mean")) ** 2).sum(); ss_t = ((y - gm) ** 2).sum()
    ss_as = ss_t - ss_a - ss_s - ss_e
    ms_a, ms_as, ms_e = ss_a / 2, ss_as / 8, ss_e / 15
    rep = math.sqrt(ms_e); between = math.sqrt(max(0, (ms_a - ms_as) / 10) + max(0, (ms_as - ms_e) / 2)); within = math.hypot(rep, between)
    ok("ch7 gauge study readings", len(g), 30)
    ok("ch7 repeatability sd", rep, 0.4, 1); ok("ch7 between analyst and day sd", between, 0.45, 2); ok("ch7 within lab sd", within, 0.6, 1)
    ok("ch7 precision to tolerance", 6 * within / 4, 0.90, 2); ok("ch7 repeatability alone", 6 * rep / 4, 0.60, 2)
    ok("ch7 between from the table", math.sqrt(0.6 ** 2 - 0.4 ** 2), 0.45, 2); ok("ch7 OG ratio", 6 * 0.02 / 0.4, 0.30, 2)
    ok("ch7 drift weeks", 0.00003 / 0.000004, 7.5, 1); ok("ch7 R", 2.8 * 0.10, 0.28, 2)
    ok("ch7 split sample interval", 2.262 * 0.14 / math.sqrt(10), 0.10, 2)
    return g


# ------------------------------------------------ chapter 8 and 13
def fills_model():
    f = csv("ch08_fills.csv"); tr, te = f[f.split == "train"], f[f.split == "test"]
    lin = md.LinearRegression().fit(tr[md.FILL_FEATS], tr.rdf_pct); gb = md.gb_model().fit(tr[md.FILL_FEATS], tr.rdf_pct)
    return f, tr, te, lin, gb


def ch8_13():
    f, tr, te, lin, gb = fills_model()
    ok("ch8 fills", len(f), 300); ok("ch8 split", (len(tr), len(te)), (225, 75))
    ok("ch8 RDF recomputed from final AE", bool(np.allclose(md.rdf(f.og_plato, f.final_ae_plato), f.rdf_pct, atol=0.006)), True)
    base = tr.rdf_pct.mean(); ok("ch8 training average", base, 68.3, 1)
    for name, p, want in (("baseline", np.full(75, base), (1.03, 0.17, 1.22, -2.22, 2.56)),
                          ("linear", lin.predict(te[md.FILL_FEATS]), (0.53, -0.06, 0.67, -1.37, 1.25)),
                          ("gradient boosting", gb.predict(te[md.FILL_FEATS]), (0.54, -0.03, 0.70, -1.40, 1.34))):
        d = p - te.rdf_pct.to_numpy()
        ok(f"ch8 {name} MAE", np.abs(d).mean(), want[0], 2); ok(f"ch8 {name} bias", d.mean(), want[1], 2)
        ok(f"ch8 {name} sd", d.std(ddof=1), want[2], 2)
        ok(f"ch8 {name} LoA low", round(d.mean(), 2) - 1.96 * round(d.std(ddof=1), 2), want[3], 2)
        ok(f"ch8 {name} LoA high", round(d.mean(), 2) + 1.96 * round(d.std(ddof=1), 2), want[4], 2)
    ok("ch8 RDF at AE 1.8", md.rdf(12.0, 1.8), 71.0, 1); ok("ch8 RDF at AE 2.6", md.rdf(12.0, 2.6), 65.6, 1)
    ok("ch8 slope", (md.rdf(12.0, 1.8) - md.rdf(12.0, 2.6)) / 0.8, 6.7, 1); ok("ch8 reference wobble", 0.05 * 6.7, 0.34, 2)
    ok("ch8 model only spread", math.sqrt(0.67 ** 2 - 0.34 ** 2), 0.58, 2); ok("ch8 in Plato", 1.3 / 6.7, 0.19, 2)
    ok("ch8 VDK day 6", 0.12 * 0.62, 0.074, 3); ok("ch8 VDK day 7", 0.074 * 0.62, 0.046, 3)
    ok("ch8 VDK ratios", (round(0.19 / 0.31, 2), round(0.12 / 0.19, 2)), (0.61, 0.63))
    do = csv("ch08_do_filler_run.csv").do_ppb.to_numpy(); b = do[:8]
    ok("ch8 DO baseline total", int(b.sum()), 178); ok("ch8 DO mean", b.mean(), 22.3, 1); ok("ch8 DO sd", b.std(ddof=1), 2.8, 1)
    flag = b.mean() + 3 * b.std(ddof=1); ok("ch8 flag line", flag, 30.7, 1)
    ok("ch8 first flag reading", int(next(i for i, v in enumerate(do, 1) if i > 8 and v > flag)), 11)
    # chapter 13
    ok("ch13 error limits low", -0.06 - 3 * 0.67, -2.07, 2); ok("ch13 error limits high", -0.06 + 3 * 0.67, 1.95, 2)
    ok("ch13 months of test fills", 75 / 10.2, 7.4, 1); ok("ch13 acceptance in RDF", 0.06 * 6.7, 0.40, 2)
    ok("ch13 LoA span", 1.25 + 1.37, 2.62, 2); ok("ch13 span in Plato", 2.62 / 6.7, 0.39, 2); ok("ch13 share of band", 100 * 0.39 / 0.8, 49, 0)
    live = csv("ch13_live_fills.csv"); err = lin.predict(live[md.FILL_FEATS]) - live.rdf_pct.to_numpy()
    ok("ch13 malt change at lot M-26-0188", live.malt_lot.iloc[24], "M-26-0188")
    ok("ch13 shadow fills mean error", err[24:34].mean(), 0.74, 2)
    ok("ch13 before the change inside limits", bool(((err[:24] > -2.07) & (err[:24] < 1.95)).all()), True)
    offset = err[24:34].mean() - (-0.06)
    ok("ch13 bias after refit inside 0.20", bool(abs((err[34:] - offset).mean()) < 0.20), True)
    zz = (1.95 - 0.74) / 0.67; ok("ch13 z", zz, 1.81, 2); ok("ch13 chance per fill, percent", 100 * (1 - norm.cdf(zz)), 3.5, 1)
    ok("ch13 one fill in", 1 / (1 - norm.cdf(zz)), 28, 0)
    p = norm.cdf(0.80 / 0.67); ok("ch13 above centre, percent", 100 * p, 88, 0)
    ok("ch13 eight in a row fills, about 14.5", (1 - p ** 8) / ((1 - p) * p ** 8), 14.5, 1)
    ok("ch13 shift in sigma", 0.80 / 0.67, 1.2, 1); ok("ch13 CUSUM fills, about 8", arl_cusum(0.80 / 0.67), 8, 0)
    ok("ch13 standard error", 0.67 / math.sqrt(75), 0.077, 3); ok("ch13 bias in SEs", 0.20 / 0.077, 2.6, 1)
    ok("ch13 SE with 30", 0.67 / math.sqrt(30), 0.122, 3); ok("ch13 bias in SEs with 30", 0.20 / 0.122, 1.6, 1)


# ------------------------------------------------ chapters 9 and 12
def ch9_12():
    m = csv("ch09_micro.csv")
    ok("ch9 results", len(m), 14222); ok("ch9 positives", int(m.positive.sum()), 283)
    ok("ch9 positive share, percent", 100 * m.positive.mean(), 1.99, 2)
    h, r = m[m.hard_fitting == 1], m[m.hard_fitting == 0]
    ok("ch9 hard fittings", h.sample_point.nunique(), 5); ok("ch9 hard rows", len(h), 2735); ok("ch9 hard positives", int(h.positive.sum()), 200)
    ok("ch9 hard share of rows, percent", 100 * len(h) / len(m), 19, 0); ok("ch9 hard share of positives, percent", 100 * 200 / 283, 71, 0)
    ok("ch9 hard rate", 100 * h.positive.mean(), 7.3, 1); ok("ch9 other rows", len(r), 11487)
    ok("ch9 other positives", int(r.positive.sum()), 83); ok("ch9 other rate", 100 * r.positive.mean(), 0.7, 1)
    ok("ch9 normal CIP rate", 100 * m[m.cip_short == 0].positive.mean(), 1.8, 1); ok("ch9 short CIP rate", 100 * m[m.cip_short == 1].positive.mean(), 4.2, 1)
    tr, te = m[m.day < 365], m[m.day >= 365]
    ok("ch9 training rows", len(tr), 9490); ok("ch9 training positives", int(tr.positive.sum()), 152)
    ok("ch9 test rows", len(te), 4732); ok("ch9 test positives", int(te.positive.sum()), 131)
    ok("ch9 test share", 100 * 131 / 4732, 2.8, 1); ok("ch9 train share", 100 * 152 / 9490, 1.6, 1)
    model = md.micro_model().fit(tr[md.MICRO_FEATS], tr.positive)
    te = te.assign(p=model.predict_proba(te[md.MICRO_FEATS])[:, 1])
    flags = te.sort_values(["day", "p"], ascending=[True, False], kind="stable").groupby("day").head(5)
    found = int(flags.positive.sum())
    ok("ch9 flags", len(flags), 910); ok("ch9 found", found, 94)
    ok("ch9 precision", 100 * found / 910, 10.3, 1); ok("ch9 recall", 100 * found / 131, 71.8, 1); ok("ch9 missed", 131 - found, 37)
    ok("ch9 lift", round(100 * found / 910, 1) / round(100 * 131 / 4732, 1), 3.7, 1)
    ok("ch9 random 5 a day", 910 * 131 / 4732, 25, 0)
    ok("ch9 fixed list", int(te[te.hard_fitting == 1].positive.sum()), 90)
    ok("ch9 false flags a day", (910 - found) / 182, 4.5, 1); ok("ch9 true hits a day", found / 182, 0.5, 1)
    ok("ch12 all clear right", 14222 - 283, 13939); ok("ch12 accuracy", 100 * 13939 / 14222, 98.0, 1)
    ok("ch12 never flag accuracy in test", 100 * (1 - 131 / 4732), 97.2, 1)
    ok("ch12 flag gap", 2.8 * 4, 11.2, 1); ok("ch12 ratio", 13 / 11.2, 1.2, 1); ok("ch12 inline sigmas", (0.10 + 0.30) / 0.05, 8.0, 1)
    q = csv("ch12_sop_testset.csv")
    ok("ch12 test set questions", len(q), 10)


# ------------------------------------------------ chapter 10
def ch10():
    s = csv("ch10_scores.csv"); y = s.bitterness.to_numpy(float); gm = y.mean()
    ok("ch10 scores", len(s), 144); ok("ch10 grand mean", gm, 4.611, 3)
    sm = s.groupby("sample").bitterness.mean(); ok("ch10 standard mean", sm["standard"], 4.139, 3); ok("ch10 trial mean", sm["trial"], 5.083, 3)
    am = s.groupby("assessor").bitterness.mean(); tm = s.groupby("session").bitterness.mean()
    cell = s.groupby(["assessor", "sample"]).bitterness.mean()
    ss_s = 72 * ((sm - gm) ** 2).sum(); ss_a = 12 * ((am - gm) ** 2).sum(); ss_t = 24 * ((tm - gm) ** 2).sum()
    ss_as = 6 * sum((cell[a, k] - am[a] - sm[k] + gm) ** 2 for a in am.index for k in sm.index)
    tot = ((y - gm) ** 2).sum(); res = tot - ss_s - ss_a - ss_t - ss_as
    for lab, v, w in (("sample", ss_s, 32.11), ("assessor", ss_a, 56.06), ("session", ss_t, 3.22), ("assessor x sample", ss_as, 10.06),
                      ("residual", res, 74.78), ("total", tot, 176.22)): ok(f"ch10 SS {lab}", v, w, 2)
    msr, msas = res / 115, ss_as / 11
    ok("ch10 MS assessor", ss_a / 11, 5.10, 2); ok("ch10 MS session", ss_t / 5, 0.64, 2); ok("ch10 MS AxS", msas, 0.91, 2); ok("ch10 MS residual", msr, 0.65, 2)
    F = ss_s / msas; ok("ch10 F sample", F, 35.1, 1); ok("ch10 p sample", ss.f.sf(F, 1, 11), 0.0001, 4)
    ok("ch10 F assessor", (ss_a / 11) / msr, 7.8, 1); ok("ch10 F session", (ss_t / 5) / msr, 1.0, 1); ok("ch10 p session", ss.f.sf((ss_t / 5) / msr, 5, 115), 0.43, 2)
    ok("ch10 F AxS", msas / msr, 1.4, 1); ok("ch10 p AxS", ss.f.sf(msas / msr, 11, 115), 0.18, 2); ok("ch10 F against residual", ss_s / msr, 49.4, 1)
    ok("ch10 assessor mean min", am.min(), 3.50, 2); ok("ch10 assessor mean max", am.max(), 5.50, 2); ok("ch10 assessor 9 mean", am[9], 5.50, 2)
    w = s.pivot_table(index=["assessor", "session"], columns="sample", values="bitterness")
    d = (w.trial - w.standard).unstack()
    gap = d.mean(1); t = gap / (d.std(1, ddof=1) / math.sqrt(6))
    ok("ch10 gap sd", gap.std(ddof=1), 0.552, 3); ok("ch10 paired t", gap.mean() / (gap.std(ddof=1) / math.sqrt(12)), 5.93, 2)
    ok("ch10 CI low", gap.mean() - 2.201 * gap.std(ddof=1) / math.sqrt(12), 0.59, 2); ok("ch10 CI high", gap.mean() + 2.201 * gap.std(ddof=1) / math.sqrt(12), 1.30, 2)
    ok("ch10 assessor 2 gap", gap[2], 1.83, 2); ok("ch10 assessor 2 t", t[2], 5.97, 2); ok("ch10 largest gap is assessor 2", int(gap.idxmax()), 2)
    ok("ch10 assessors clearing 2.571", sorted(int(a) for a in t.index if t[a] > 2.571), [2, 6, 7, 10, 11])
    for a in (1, 4): ok(f"ch10 assessor {a} gap", gap[a], 0.33, 2); ok(f"ch10 assessor {a} t", t[a], 0.67, 2)
    tail = lambda n, k, p: ss.binom.sf(k - 1, n, p)
    ok("ch10 9 of 18 numerator", sum(math.comb(18, k) * 2 ** (18 - k) for k in range(9, 19)), 41687369)
    ok("ch10 p 9 of 18", tail(18, 9, 1 / 3), 0.108, 3); ok("ch10 p 10 of 18", tail(18, 10, 1 / 3), 0.0433, 4)
    for k, pv in ((8, 0.223), (11, 0.014)): ok(f"ch10 p {k} of 18", tail(18, k, 1 / 3), pv, 3)
    ok("ch10 duo trio cut", next(k for k in range(19) if tail(18, k, 0.5) <= 0.05), 13); ok("ch10 duo trio p", tail(18, 13, 0.5), 0.048, 3)
    ok("ch10 two sided cut", next(k for k in range(19) if 2 * tail(18, k, 0.5) <= 0.05), 14); ok("ch10 two sided p", 2 * tail(18, 14, 0.5), 0.031, 3)
    lo, hi = ss.beta.ppf(0.025, 9, 10), ss.beta.ppf(0.975, 10, 9)
    ok("ch10 interval low", lo, 0.260, 3); ok("ch10 interval high", hi, 0.740, 3); ok("ch10 Pd high", (3 * hi - 1) / 2, 0.61, 2)
    ok("ch10 Pd low", (3 * lo - 1) / 2, -0.11, 2); ok("ch10 Pd at 9 of 18", (3 * 0.5 - 1) / 2, 0.25, 2)
    ok("ch10 power at Pd 0.3, 18 tasters", tail(18, 10, 1 / 3 + 2 / 3 * 0.3), 0.521, 3)
    rows = {12: (8, 0.019, 0.14, 0.26, 0.44), 18: (10, 0.043, 0.30, 0.52, 0.74), 24: (13, 0.028, 0.30, 0.55, 0.79),
            30: (15, 0.043, 0.43, 0.71, 0.90), 36: (18, 0.028, 0.41, 0.72, 0.92), 48: (22, 0.048, 0.60, 0.88, 0.98)}
    for n, (k, a, *pw) in rows.items():
        kk = next(k for k in range(n + 1) if tail(n, k, 1 / 3) <= 0.05)
        ok(f"ch10 cut for {n}", kk, k); ok(f"ch10 false alarm for {n}", tail(n, kk, 1 / 3), a, 3)
        for pd_, w in zip((0.2, 0.3, 0.4), pw): ok(f"ch10 power {n} at Pd {pd_}", tail(n, kk, 1 / 3 + 2 / 3 * pd_), w, 2)
    def need(pd_):
        return next(n for n in range(6, 300) if tail(n, next(k for k in range(n + 1) if tail(n, k, 1 / 3) <= 0.05), 1 / 3 + 2 / 3 * pd_) >= 0.8)
    ok("ch10 tasters for 0.8 at Pd 0.4", need(0.4), 23); ok("ch10 at Pd 0.3", need(0.3), 40); ok("ch10 at Pd 0.2", need(0.2), 87)
    def paired_power(n, delta, sd=0.552):
        tc = ss.t.ppf(0.975, n - 1); return ss.nct.sf(tc, n - 1, delta / (sd / math.sqrt(n)))
    ok("ch10 paired power 12 at 0.5", paired_power(12, 0.5), 0.81, 2); ok("ch10 paired power 8 at 0.75", paired_power(8, 0.75), 0.91, 2)
    a = (0.914 - 0.650) / 6; ok("ch10 a", a, 0.044, 3)
    for S, w in ((3, 0.72), (6, 0.55), (12, 0.44)): ok(f"ch10 gap spread at {S} sessions", math.sqrt(2 * (a + 0.650 / S)), w, 2)
    ok("ch10 floor", math.sqrt(2 * a), 0.30, 2)


# ------------------------------------------------ chapter 11
def ch11():
    r, lots, sp = csv("ch11_tasting_records.csv"), csv("ch11_lots.csv"), csv("ch11_spikes.csv")
    ok("ch11 records", len(r), 400); ok("ch11 sessions", r.lot_id.nunique(), 50)
    ok("ch11 tasters per session", set(r.groupby("lot_id").size()), {8}); ok("ch11 pool", r.taster.nunique(), 18)
    tags = r.off_flavour.value_counts().to_dict()
    ok("ch11 tags", tags, {"none": 197, "papery": 103, "cooked vegetable": 26, "green apple": 26, "buttery": 24, "sulphury": 24})
    ok("ch11 flagged records", int((r.off_flavour != "none").sum()), 203)
    n = sp.spikes_named_of_6.value_counts().to_dict(); ok("ch11 spike results", n, {6: 2, 5: 6, 4: 7, 3: 2, 2: 1})
    ok("ch11 tasters to retrain", int((sp.spikes_named_of_6 < 4).sum()), 3)
    tot = r.groupby("lot_id").bitterness.transform("sum"); r = r.assign(off=r.bitterness - (tot - r.bitterness) / 7)
    g = r.groupby("taster").off
    big = {t: (int(g.size()[t]), round(g.mean()[t], 2), round(abs(g.mean()[t]) / (g.std()[t] / math.sqrt(g.size()[t])), 1)) for t in g.mean().index if abs(g.mean()[t]) > 0.75}
    ok("ch11 tasters beyond 0.75", big, {"T03": (27, 1.68, 7.6), "T07": (20, -0.91, 5.1), "T10": (21, 0.80, 4.5), "T13": (21, -1.09, 4.8)})
    ok("ch11 one taster moves the mean", 1.68 / 8, 0.21, 2); ok("ch11 two tasters", (1.68 + 0.80) / 8, 0.31, 2)
    band = md.BAND; means = r.groupby("lot_id")[list(band)].mean()
    outside = [(l, a) for l in means.index for a in band if abs(means.at[l, a] - band[a]) > 1]
    no = r.groupby("lot_id").true_to_type.apply(lambda v: (v == "no").sum())
    half = set(no.index[no >= 4])
    ok("ch11 lots at the half rule", len(half), 7)
    ok("ch11 one more lot outside the band, on bitterness", [(a, round(means.at[l, a], 2), l in half) for l, a in outside], [("bitterness", 5.38, False)])
    lot_hi = [l for l, a in outside][0]
    ok("ch11 that lot seats T03 and T10", {"T03", "T10"} <= set(r[r.lot_id == lot_hi].taster), True)
    off = g.mean().abs(); spk = sp.set_index("taster").spikes_named_of_6
    safe = [t for t in spk.index if spk[t] >= 4 and off[t] <= 0.75]
    ok("ch11 safe corner", len(safe), 12)
    ok("ch11 good recognition, big offset", sorted(t for t in spk.index if spk[t] >= 4 and off[t] > 0.75), ["T03", "T07", "T10"])
    ok("ch11 small offset, weak recognition", sorted(t for t in spk.index if spk[t] < 4 and off[t] <= 0.75), ["T12", "T15"])
    ok("ch11 fails both", sorted(t for t in spk.index if spk[t] < 4 and off[t] > 0.75), ["T13"])
    t12 = r[r.taster == "T12"]; ok("ch11 T12 records and papery tags", (len(t12), int((t12.off_flavour == "papery").sum())), (24, 0))
    pap = r[r.off_flavour == "papery"].groupby("lot_id").size().reindex(lots.lot_id, fill_value=0).to_numpy()
    share = pap / 8; tpo = lots.tpo_ppb.to_numpy()
    ok("ch11 every lot under 150 ppb", bool((tpo < 150).all()), True)
    rr = np.corrcoef(tpo, share)[0, 1]
    ok("ch11 r", rr, 0.80, 2); ok("ch11 r squared", rr ** 2, 0.64, 2)
    ok("ch11 slope per 10 ppb, points", 1000 * np.polyfit(tpo, share, 1)[0], 7.6, 1)
    ok("ch11 t", rr * math.sqrt(48) / math.sqrt(1 - rr ** 2), 9.2, 1)
    ok("ch11 lots above 120", int((tpo > 120).sum()), 13); ok("ch11 mean above 120", 100 * share[tpo > 120].mean(), 54.8, 1)
    ok("ch11 mean of the rest", 100 * share[tpo <= 120].mean(), 15.5, 1); ok("ch11 weighted check", (13 * 54.8 + 37 * 15.5) / 50, 25.7, 1)
    ex = lots.index[(tpo == 138) & (pap == 5)]
    ok("ch11 example lot: 138 ppb, 5 of 8 papery", len(ex) >= 1, True)
    ok("ch11 example lot bitterness mean", r[r.lot_id == lots.lot_id[ex[0]]].bitterness.mean(), 4.1, 1)
    c = lots[lots.staling_complaint == 1]
    ok("ch11 complaints", len(c), 6); ok("ch11 complaints on the 7 lots above 140", int((c.tpo_ppb > 140).sum()), 4)
    ok("ch11 lots above 140", int((tpo > 140).sum()), 7); ok("ch11 expected at random", 6 * 7 / 50, 0.84, 2)
    ok("ch11 tail", ss.binom.sf(3, 6, 0.14), 0.0045, 4)


def sheets():
    from openpyxl import load_workbook
    S = Path(__file__).resolve().parent / "sheets"
    ws = load_workbook(S / "ch06-cusum.xlsx")["CUSUM"]
    ok("sheet ch6 CUSUM row 9", ws["D9"].value, "=MAX(0,D8+B9-($B$2+$B$5))"); ok("sheet ch6 h", ws["B6"].value, "=5*B4")
    ok("sheet ch6 pH values", [ws.cell(r, 2).value for r in range(8, 158)], csv("ch06_ph.csv").ph.tolist())
    ws = load_workbook(S / "ch07-gauge-study.xlsx")["Gauge study"]
    ok("sheet ch7 repeatability cell", ws["B11"].value, "=SQRT(B10)"); ok("sheet ch7 ratio cell", ws["B15"].value, "=6*B13/B14")
    ws = load_workbook(S / "ch10-triangle.xlsx")["Triangle"]
    ok("sheet ch10 p value cell", ws["E4"].value, "=1-_xlfn.BINOM.DIST(E3-1,E2,1/3,TRUE)")
    ok("sheet ch10 nine correct entered", sum(ws.cell(r, 2).value for r in range(3, 21)), 9)


def ch14():
    ok("ch14 project hours", 13 * 8, 104); ok("ch14 months per false alarm, limit rule", 370 / 20.3, 18, 0)
    ok("ch14 eight in a row added", 153 / 20.3, 7.5, 1); ok("ch14 over 13 weeks", 3 * 20.3 / 153, 0.4, 1)
    ok("ch14 baseline months", 60 / 20.3, 3, 0); ok("ch14 hours gained", (25 - 10) * 30 / 60, 7.5, 1)
    do = csv("ch14_do_release.csv"); ok("ch14 DO results, 15 months at 20.3 a month", len(do), 305)


if __name__ == "__main__":
    week(); ch2(); ch4(); ch5(); ch6(); ch7(); ch8_13(); ch9_12(); ch10(); ch11(); ch14(); sheets()
    print(f"\n{len(FAILS)} misses; {len(NOTES)} notes on book sums: " + "; ".join(NOTES))
    if FAILS: raise SystemExit("MISSES: " + "; ".join(FAILS))
