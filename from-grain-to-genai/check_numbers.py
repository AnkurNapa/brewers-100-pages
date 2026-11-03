"""Assert that every number the book prints from the companion data comes out of it.

Run after make_data.py: python3 check_numbers.py
Each check names the chapter section. Precision matches what the book prints.
"""
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler, normalize

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_data as md  # noqa: E402  shared model recipes so the check and the data agree

D = HERE / "data"
done = []


def check(label, ok):
    assert ok, label
    done.append(label)


def pct(x):
    return round(100 * x)


# ---------------------------------------------------------------- 4
brews = pd.read_csv(D / "plant_brews.csv")
lab = pd.read_csv(D / "plant_lab.csv")
hist = pd.read_csv(D / "plant_historian.csv")
row = lab[lab.batch_id == "B24-118"].merge(hist, on="batch_id").iloc[0]
check("4.2 lab 13.2, line 12.9, gap 0.3", (row.og_plato_lab, row.line_og_plato) == (13.2, 12.9)
      and round(row.og_plato_lab - row.line_og_plato, 1) == 0.3)
check("4.2 3 x 100 = 300 hl", 3 * 100 == 300)
check("4.3 18 C = 64.4 F", round(18 * 1.8 + 32, 1) == 64.4)
check("4.3 1,000 lb = 453.6 kg", round(1000 / 2.2046, 1) == 453.6)
check("4.3 100 bbl = 117.3 hl", round(100 * 1.1734, 1) == 117.3)

# ---------------------------------------------------------------- 5.2
rdf = 100 * 2.0665 / (2.0665 + 4.771 / 4.269)
check("5.2.1 RDF from RE 4.771 and ALC 4.269 = 64.9", round(rdf, 1) == 64.9)
r = pd.read_csv(D / "rdf_batches.csv")
tr, te = r[r.split == "train"], r[r.split == "test"]
check("5.2.1 180 batches, 144 train, 36 test", (len(r), len(tr), len(te)) == (180, 144, 36))
check("5.2.1 baseline 66.5", round(tr.rdf_pct.mean(), 2) == 66.5)
model = LinearRegression().fit(tr[md.RDF_COLS], tr.rdf_pct)
pred = model.predict(te[md.RDF_COLS])
for (bid, meas, mod), (_, t), p in zip(md.RDF_FIXED, te.head(5).iterrows(), pred):
    check(f"5.2.1 {bid} measured {meas} model {mod}",
          t.batch_id == bid and t.rdf_pct == meas and round(p, 1) == mod)
err, base = np.abs(te.rdf_pct - pred), np.abs(te.rdf_pct - 66.5)
check("5.2.1 five rows: model 0.9, baseline 2.1",
      (round(err[:5].mean(), 1), round(base[:5].mean(), 1)) == (0.9, 2.1))
check("5.2.1 all 36: model 1.0, baseline 2.1", (round(err.mean(), 1), round(base.mean(), 1)) == (1.0, 2.1))
check("5.2.2 one point of RDF at 12 P = 0.12 P", round(12 * 0.01, 2) == 0.12)

# ---------------------------------------------------------------- 5.3
s = pd.read_csv(D / "stuck_ferments.csv")
check("5.3.1 480 batches, 32 stuck, 6.7 percent",
      (len(s), (s.stuck == "stuck").sum(), round(100 * (s.stuck == "stuck").mean(), 1)) == (480, 32, 6.7))
str_, ste = s[s.split == "train"], s[s.split == "test"]
check("5.3.1 360 train, 120 test, 8 stuck in test",
      (len(str_), len(ste), (ste.stuck == "stuck").sum()) == (360, 120, 8))
check("5.3.1 train is the oldest 360", str_.pitch_date.max() < ste.pitch_date.min())
clf = make_pipeline(StandardScaler(), LogisticRegression()).fit(str_[md.STUCK_COLS], str_.stuck == "stuck")
risk = clf.predict_proba(ste[md.STUCK_COLS])[:, 1]
actual = (ste.stuck == "stuck").to_numpy()


def confusion(th):
    flag = risk > th
    return ((flag & actual).sum(), (flag & ~actual).sum(), (~flag & actual).sum(), (~flag & ~actual).sum())


tp, fp, fn, tn = confusion(0.5)
check("5.3.1 confusion 6, 5, 2, 107", (tp, fp, fn, tn) == (6, 5, 2, 107))
check("5.3.1 accuracy 94, never flag 93", (pct((tp + tn) / 120), pct(112 / 120)) == (94, 93))
check("5.3.2 precision 55, recall 75", (pct(tp / (tp + fp)), pct(tp / (tp + fn))) == (55, 75))
check("5.3.2 2.5 hours and 144 hours", (5 * 0.5, 2 * 3 * 24) == (2.5, 144))
tp3, fp3, fn3, _ = confusion(0.3)
check("5.3.2 threshold 0.3: recall rises, precision falls",
      tp3 / (tp3 + fn3) > 0.75 and tp3 / (tp3 + fp3) < tp / (tp + fp))

# ---------------------------------------------------------------- 5.5
o = pd.read_csv(D / "outlets.csv")
check("5.5 600 outlets, 372 reordered, 62 percent",
      (len(o), (o.reordered == "yes").sum(), pct((o.reordered == "yes").mean())) == (600, 372, 62))
orisk = md.outlet_risk(o)
top = o.iloc[np.argsort(-orisk, kind="stable")[:100]]
check("5.5 top 100 at risk: 78 lapsed", (top.reordered == "no").sum() == 78)
check("5.5 by chance 38 (228 of 600)", ((o.reordered == "no").sum(), round(100 * 228 / 600)) == (228, 38))

# ---------------------------------------------------------------- 6.2
rec = pd.read_csv(D / "recipes.csv")
k5 = KMeans(5, n_init=10, random_state=0).fit_predict(StandardScaler().fit_transform(
    rec[["og_plato", "ibu", "colour_ebc", "abv_pct"]]))
check("6.2 150 recipes into five groups", len(rec) == 150 and len(set(k5)) == 5)
x = StandardScaler().fit_transform(o[md.OUTLET_CLUSTER_COLS])
sizes = sorted(np.bincount(KMeans(3, n_init=10, random_state=0).fit_predict(x)), reverse=True)
check("6.2 three groups of 270, 210 and 120", sizes == [270, 210, 120])

# ---------------------------------------------------------------- 6.3
h = pd.read_csv(D / "ferm_healthy.csv").pivot(index="curve_id", columns="reading", values="plato")
n = pd.read_csv(D / "ferm_new.csv").pivot(index="curve_id", columns="reading", values="plato")
check("6.3 576 readings a curve, 115,200 in all", (h.shape[1], h.size) == (576, 115200) and h.shape[0] == 200)
outside = ((n - h.mean()).abs() > 4 * h.std()).mean(axis=1)
flags = outside[outside > 0.05].index
causes = pd.read_csv(D / "ferm_new_inspection.csv").set_index("curve_id").cause_on_inspection
check("6.3 40 new curves, three flagged", len(n) == 40 and len(flags) == 3)
check("6.3 causes: probe, glycol, slow yeast",
      sorted(causes[flags]) == ["glycol supply dip", "mislabelled probe", "slow yeast"])

# ---------------------------------------------------------------- 6.4 and 6.5
check("6.4 June 1,200 hl and January 850 hl",
      (round(1000 * (1 + md.SEASON[5])), round(1000 * (1 + md.SEASON[0]))) == (1200, 850))
check("6.5 MAPE example 100 / 1,200 = 8.3", round(100 * 100 / 1200, 1) == 8.3)
mv = pd.read_csv(D / "monthly_volume.csv")
naive, ml = md.backtest(mv)
check("6.5 36 months, seasonal naive 9, machine learning 7", len(mv) == 36 and (round(naive), round(ml)) == (9, 7))

# ---------------------------------------------------------------- 7
check("7.2 1,000 x 1,000 = 1,000,000", 1000 * 1000 == 1_000_000)
f = pd.read_csv(D / "filler_head7.csv")
check("7.3 (500 - 495) / 0.5 = 10 hours", (md.FILL_TARGET - md.FILL_LOW) / md.DRIFT_ML_H == 10)
ref = f[f.hour < 0].fill_ml
blocks = (f[f.hour >= 0].assign(block=lambda d: (d.hour * 4).astype(int))
          .groupby("block").fill_ml.apply(lambda x: x.iloc[:5].mean()))  # five packs every 15 minutes
lcl = ref.mean() - 3 * ref.std() / math.sqrt(5)
first_signal_h = blocks[blocks < lcl].index.min() / 4
check("7.3 chart signals by hour three", first_signal_h < 3)
check("7.3 every pack in spec to hour three", f[f.hour < 3].fill_ml.min() >= 495)
k = pd.read_csv(D / "kernels.csv")
check("7.7 a few hundred kernel pictures", len(k) == 400)

# ---------------------------------------------------------------- 8
c = pd.read_csv(D / "complaints.csv")
check("8.7 300 notes, five classes", len(c) == 300 and c.defect_class.nunique() == 5)
ctr, cte = c[c.split == "train"], c[c.split == "test"]
cm = md.complaint_model().fit(ctr.note, ctr.defect_class)
cp = cm.predict(cte.note)
is_d, flag_d = (cte.defect_class == "diacetyl").to_numpy(), cp == "diacetyl"
check("8.3 100 test notes, 8 diacetyl, 9 flagged, 6 right",
      (len(cte), is_d.sum(), flag_d.sum(), (is_d & flag_d).sum()) == (100, 8, 9, 6))
check("8.3 recall 75, precision 67", (pct(6 / 8), pct(6 / 9)) == (75, 67))
ln = pd.read_csv(D / "lab_notes.csv")
vec = TfidfVectorizer(stop_words="english")
svd = TruncatedSVD(4, random_state=0)
Z = normalize(svd.fit_transform(vec.fit_transform(ln.note)))


def search(q, top=5):
    sc = Z @ normalize(svd.transform(vec.transform([q]))).ravel()
    return list(ln.note.iloc[np.argsort(-sc)[:top]])


hits = search("fermentation stalled at 1.020 after a cold crash")
check("8.4 meaning search finds both stalled notes",
      "Gravity stuck, tank chilled early" in hits and "Yeast fell out, restarted with a warm-up" in hits)
check("8.4 keyword search for diacetyl misses the 2023 note",
      not ln.note.str.contains("diacetyl", case=False).iloc[3] and "Slick, butterscotch, held two days" in search("diacetyl"))

# ---------------------------------------------------------------- 9
OE, RDF9 = 13.0, 64.9
q = 100 - 0.005161 * OE * RDF9
re_ = OE * (100 - RDF9) / q
abw = 0.4839 * OE * RDF9 / q
ae = (re_ - 0.1808 * OE) / 0.8192
sg = 1 + ae / (258.6 - 227.1 * ae / 258.2)
abv = abw * sg / 0.79066
check("9.5 456.3 / 95.646", (round(OE * (100 - RDF9), 1), round(q, 3)) == (456.3, 95.646))
check("9.5 RE 4.77, ABW 4.27, AE 2.95, density 1.0115, ABV 5.46",
      (round(re_, 2), round(abw, 2), round(ae, 2), round(sg, 4), round(abv, 2)) == (4.77, 4.27, 2.95, 1.0115, 5.46))
check("9.5 apparent attenuation 77.3", round(100 * (1 - round(ae, 2) / OE), 1) == 77.3)
sg_w = 1 + OE / (258.6 - 227.1 * OE / 258.2)
mg_l_alpha = 150 * 0.10 * 10  # 150 g/hl of a 10 percent alpha hop = 150 mg/L of alpha acid
tinseth = 1.65 * 0.000125 ** (sg_w - 1) * (1 - math.exp(-0.04 * 60)) / 4.15 * mg_l_alpha
rager = (18.11 + 13.86 * math.tanh((60 - 31.32) / 18.27)) / 100 / (1 + max(0, sg_w - 1.050) / 0.2) * mg_l_alpha
check("9.5 Tinseth 34, Rager 46, gap 35 percent",
      (round(tinseth), round(rager), round(100 * (rager - tinseth) / tinseth)) == (34, 46, 35))
check("9.6 5.5 passes, 5.4 fails at 0.05",
      abs(5.5 - 5.46) <= 0.05 and abs(5.4 - 5.46) > 0.05)
g = pd.read_csv(D / "golden_set.csv")
check("9.8 ten question golden set", len(g) == 10)

# ---------------------------------------------------------------- 10
rx = pd.read_csv(D / "radar_extract.csv")
gc = rx.grade.value_counts()
check("10.1 1,015 entries: 447, 60, 21, 431, 56",
      (len(rx), gc["shipping"], gc["pilot"], gc["research"], gc["no AI claim"], gc["not graded"])
      == (1015, 447, 60, 21, 431, 56))
check("10.1 42 percent no claim", pct(431 / 1015) == 42)
ship = rx[rx.grade == "shipping"].theme.value_counts()
check("10.1 shipping 98, 64, 61, 45",
      (ship["Process and operations"], ship["Agriculture and crop"], ship["Sales, demand and pricing"],
       ship["Quality and inspection"]) == (98, 64, 61, 45))
sens = rx[rx.theme == "Sensory and recipe"]
check("10.1 sensory 17 of 70 pilots or research",
      (len(sens), sens.grade.isin(["pilot", "research"]).sum()) == (70, 17))
share = rx.assign(pr=rx.grade.isin(["pilot", "research"])).groupby("theme").pr.mean()
check("10.1 sensory the highest share", share.idxmax() == "Sensory and recipe")
check("10.1 about 35 mention generative AI", rx.mentions_genai.sum() == 35)
eq = rx[rx.theme == "Engineering and equipment"]
check("10.1 3 of 36 equipment makers ship", (len(eq), (eq.grade == "shipping").sum()) == (36, 3))

# ---------------------------------------------------------------- 11
ws = load_workbook(HERE / "sheets" / "ch11-pilot-payback.xlsx", data_only=False)["Payback"]
cells = {ws.cell(r, 1).value: ws.cell(r, 2).value for r in range(1, ws.max_row + 1)}
check("11.1 sheet holds formulas, not pasted values",
      all(str(cells[k]).startswith("=") for k in ("Loss today (hl)", "Net, built (USD a year)", "Payback, built (years)")))


def cell_value(r):
    """Evaluate a column B formula of the sheet make_sheets.py writes (our own file, so eval is safe).
    It handles plus, minus, times, divide, IF and B references only."""
    v = ws.cell(r, 2).value
    if not str(v).startswith("="):
        return v
    expr = str(v)[1:].replace('"never"', "None")
    expr = re.sub(r"IF\((.+?),(.+?),(.+)\)", r"((\2) if (\1) else (\3))", expr)
    return eval(re.sub(r"B(\d+)", lambda m: f"cell_value({m.group(1)})", expr))


rows = {ws.cell(r, 1).value: r for r in range(1, ws.max_row + 1)}
sheet = {k: cell_value(r) for k, r in rows.items() if k}
check("11.1 sheet formulas give 2,000; 4,050; minus 17,830; 1,970; 15.2; 2.3",
      (sheet["Loss today (hl)"], round(sheet["Banked, replacement (USD a year)"]),
       round(sheet["Net, bought (USD a year)"]), round(sheet["Net, built (USD a year)"]),
       round(sheet["Payback, built (years)"], 1), round(sheet["Payback, built, upper bound (years)"], 1))
      == (2000, 4050, -17830, 1970, 15.2, 2.3))
loss = 100000 * 0.02
banked, banked_hi = 100000 * 0.003 * 30 * 0.45, 100000 * 0.003 * 110 * 0.45
check("11.1 2,000 hl, USD 60,000 and 220,000", (loss, loss * 30, loss * 110) == (2000, 60000, 220000))
check("11.1 300 hl, USD 9,000 and 33,000", (100000 * 0.003, 300 * 30, 300 * 110) == (300, 9000, 33000))
check("11.1 banked 4,050 and 14,850", (round(banked), round(banked_hi)) == (4050, 14850))
check("11.1 bought: minus 17,830 and minus 7,030",
      (round(banked - 21880), round(banked_hi - 21880)) == (-17830, -7030) and 16800 + 3000 + 2080 == 21880)
check("11.1 built: 1,970 net, 15.2 years; 12,770 and 2.3 years",
      (round(banked - 2080), round(30000 / (banked - 2080), 1), round(banked_hi - 2080),
       round(30000 / (banked_hi - 2080), 1)) == (1970, 15.2, 12770, 2.3))

# ---------------------------------------------------------------- 15
lo = pd.read_csv(D / "plant_losses.csv").set_index("batch_id").loc["B24-150"]
ko = brews.set_index("batch_id").loc["B24-150", "knockout_volume"]
lost = lo[["trub_hl", "yeast_hl", "filter_hl", "filler_hl"]].sum()
check("15.5 knock out 500, pack 490, loss 10 hl, 2 percent",
      (ko, lo.packed_hl, lost, round(100 * lost / ko)) == (500, 490, 10, 2))

print(f"{len(done)} checks passed")
