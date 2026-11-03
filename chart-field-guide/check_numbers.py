"""Check that every number the book prints from the Kestrel companion data comes out of data/*.csv.

Run python3 make_data.py first, then python3 check_numbers.py. Each line prints PASS or the script stops.
The DAX patterns of Appendix B and the KQL golden band are rebuilt here in pandas, so their known answers are tested
without Power BI or an Eventhouse.
"""
import os

import numpy as np
import pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
COUNT = 0


def load(name, **kw):
    return pd.read_csv(os.path.join(D, name + ".csv"), **kw)


def ok(label, got, want, places=None):
    global COUNT
    g = round(got, places) if places is not None else got
    assert g == want, f"{label}: got {got!r}, book prints {want!r}"
    COUNT += 1
    print(f"PASS  {label}: {g}")


# ---------- chapter 5 and pattern 1: the golden band ----------
fill = load("Fill", parse_dates=["HourZero", "FillEnd"])
hg = load("HourlyGravity")
ref_ids = fill.loc[fill.IsReference, "FillId"]
ok("ch5 reference fills that build the band", len(ref_ids), 11)
ok("ch5 worked pale ale fills (eleven healthy plus one stall)", hg.FillId.nunique(), 12)
pale_ref = fill[fill.FillId.isin(hg.FillId.unique())]
ok("ch5 fills started over eleven days", (pale_ref.HourZero.dt.normalize().max() - pale_ref.HourZero.dt.normalize().min()).days + 1, 11)
band = hg[hg.FillId.isin(ref_ids)].pivot(index="BatchHour", columns="FillId", values="Gravity")
p = {q: band.quantile(q, axis=1, interpolation="linear") for q in (0.1, 0.5, 0.9)}   # PERCENTILEX.INC
ok("B.2 band at hour 72, P10", p[0.1][72], 3.30, 2)
ok("B.2 band at hour 72, P50", p[0.5][72], 3.60, 2)
ok("B.2 band at hour 72, P90", p[0.9][72], 3.86, 2)
ok("ch5 band at hour 168, P10", p[0.1][168], 2.73, 2)
ok("ch5 band at hour 168, P50", p[0.5][168], 2.76, 2)
ok("ch5 band at hour 168, P90", p[0.9][168], 2.83, 2)
ok("ch5 P90 at hour 96", p[0.9][96], 3.05, 2)
ok("ch5 mean plus two sd at hour 96", band.loc[96].mean() + 2 * band.loc[96].std(ddof=1), 3.11, 2)
cross = band.le(8.0 + 1e-9).idxmax()
ok("ch5 first healthy fill below 8 degrees Plato (hour)", int(cross.min()), 34)
ok("ch5 last healthy fill below 8 degrees Plato (hour)", int(cross.max()), 49)
stall_id = fill.loc[fill.FillId.isin(hg.FillId.unique()) & ~fill.IsReference, "FillId"].iloc[0]
st = hg[hg.FillId == stall_id].set_index("BatchHour").Gravity
ok("ch5 stalled fill crosses 8 degrees Plato (hour)", int(st.le(8.0 + 1e-9).idxmax()), 34)
ok("ch5 stalled fill at hour 72", st[72], 5.92, 2)
ok("ch5 stalled fill touches P90 at hour 54", abs(st[54] - p[0.9][54]) < 0.005, True)
outside = [h for h in st.index if h >= 34 and st[h] > p[0.9][h] + 1e-6]
ok("ch5 hours outside the band", len(outside), 109)
ok("ch5 first hour outside the band", outside[0], 60)
ok("ch5 apparent attenuation, healthy (percent)", 100 * (1 - 2.8 / 13.5), 79.3, 1)
ok("ch5 apparent attenuation, stall (percent)", 100 * (1 - 6.0 / 13.5), 55.6, 1)

# KQL 1 rebuilt: readings joined to fills on tank and time, hourly mean per fill, then nearest rank percentiles
rd = load("Readings", parse_dates=["Time"])
g = rd[rd.Tag == "Gravity"].merge(fill[fill.IsReference & (fill.Brand == "Pale Ale")], on="Tank")
g = g[(g.Time >= g.HourZero) & (g.Time <= g.FillEnd)]
g["BatchHour"] = ((g.Time - g.HourZero) / pd.Timedelta(hours=1)).astype(int)
hour72 = np.sort(g[g.BatchHour == 72].groupby("FillId").Value.mean().values)
nearest = [hour72[int(np.ceil(q * len(hour72))) - 1] for q in (0.10, 0.50, 0.90)]
ok("B.12 KQL band at hour 72 (p10, p50, p90)", [round(float(v), 2) for v in nearest], [3.30, 3.60, 3.86])

# ---------- chapter 6, patterns 2 and 3: control limits and capability ----------
b = load("Batch")
base = b[b.IsBaseline]
mean_fg, mean_mr = base.FinalGravity.mean(), base.MovingRange.mean()
ok("ch6 fills on the chart", len(b), 40)
ok("B.3 Mean FG (same at fill 5 and fill 35: baseline rows only)", mean_fg, 2.194, 3)
ok("ch13 Mean MR", mean_mr, 0.146, 3)
ok("ch6 sigma within (MR / 1.128)", mean_mr / 1.128, 0.129, 3)
ok("ch6 baseline sample sd", base.FinalGravity.std(ddof=1), 0.1135, 4)
ucl, lcl = mean_fg + 2.66 * mean_mr, mean_fg - 2.66 * mean_mr
ok("B.3 UCL", ucl, 2.58, 2)
ok("B.3 LCL", lcl, 1.81, 2)
ok("ch13 points outside the limits", int(((b.FinalGravity > ucl) | (b.FinalGravity < lcl)).sum()), 0)
v, centre, sw = b.FinalGravity.tolist(), 2.194, 0.129
side = np.sign(np.array(v) - centre)
run8 = next(i + 1 for i in range(7, 40) if abs(side[i - 7:i + 1].sum()) == 8)
ok("ch6 eight in a row first fires at fill", run8, 40)
c, cus = 0.0, []
for x in v:
    c = max(0.0, c + x - (centre + 0.064))
    cus.append(c)
ok("ch6 CUSUM crosses 0.64 at fill", next(i + 1 for i, x in enumerate(cus) if x >= 0.64), 34)
z, ew = centre, []
for x in v:
    z = 0.2 * x + 0.8 * z
    ew.append(z)
half = 3 * sw * (0.2 / 1.8) ** 0.5
ok("ch6 EWMA settled half width", half, 0.129, 3)
ok("ch6 EWMA signals at fill", next(i + 1 for i, x in enumerate(ew) if abs(x - centre) > half), 35)
ok("ch6 mean of the last ten fills", np.mean(v[30:]), 2.384, 3)
ok("ch6 margin to the upper spec", 2.6 - round(np.mean(v[30:]), 3), 0.216, 3)
s_within, s_overall = mean_mr / 1.128, base.FinalGravity.std(ddof=1)
ok("ch6 Cp", 0.8 / (6 * round(s_within, 3)), 1.03, 2)
ok("ch6 Cpk with sigma rounded to 0.129", min(2.6 - mean_fg, mean_fg - 1.8) / (3 * round(s_within, 3)), 1.02, 2)
ok("B.4 Cpk from the unrounded moving range (the DAX result)", min(2.6 - mean_fg, mean_fg - 1.8) / (3 * s_within), 1.01, 2)
ok("ch6 Pp", 0.8 / (6 * s_overall), 1.17, 2)
ok("B.4 Ppk", min(2.6 - mean_fg, mean_fg - 1.8) / (3 * s_overall), 1.16, 2)
ok("ch6 process sd after test error", (round(s_overall, 4) ** 2 - 0.05 ** 2) ** 0.5, 0.102, 3)
after = load("BatchAfterFix").FinalGravity
ok("ch6 after fix mean", after.mean(), 2.21, 2)
ok("ch6 after fix sd", after.std(ddof=1), 0.093, 3)
ok("ch6 after fix Ppk", (2.6 - round(after.mean(), 2)) / (3 * round(after.std(ddof=1), 3)), 1.40, 2)

# ---------- chapter 7 and pattern 4: yield, waterfall and Pareto ----------
brew = load("Brew")
one = brew[brew.BrewId == "B26-0068"].iloc[0]
ok("B.5 one brew extract (kg)", one.ExtractKg, 3767, 0)
ok("B.5 one brew theoretical (kg)", one.TheoreticalKg, 4070, 0)
ok("B.5 one brew yield (percent)", 100 * one.ExtractKg / one.TheoreticalKg, 92.6, 1)
ok("ch7 one brew gap (kg)", one.TheoreticalKg - one.ExtractKg, 303, 0)
ok("ch12 brewhouse efficiency, ratio of sums over the year (percent)", 100 * brew.ExtractKg.sum() / brew.TheoreticalKg.sum(), 92.6, 1)
vol, stage = load("Volume"), load("Stage")
mar_v = vol[vol.Month == "2026-03-01"].iloc[0]
mar = stage[stage.Month == "2026-03-01"].set_index("Stage")
ok("ch7 cast (hL)", int(mar_v.CastHL), 8700)
ok("ch7 dispatched (hL)", int(mar_v.DispatchedHL), 8330)
ok("ch7 stage losses (hL)", mar.LossHL.tolist(), [209, 52, 87, 22])
ok("B.7 loss (hL)", int(mar.LossHL.sum()), 370)
ok("B.7 loss percent", 100 * (mar_v.CastHL - mar_v.DispatchedHL) / mar_v.CastHL, 4.25, 2)
ok("ch7 reconcile: cast less losses less dispatch", int(mar_v.CastHL - mar.LossHL.sum() - mar_v.DispatchedHL), 0)
ok("ch7 last stage out equals dispatch", int(mar.OutHL.iloc[-1]), 8330)
par = mar.sort_values("LossHL", ascending=False)
ok("ch7 Pareto running total (percent)", [round(x, 1) for x in 100 * par.LossHL.cumsum() / 370], [56.5, 80.0, 94.1, 100.0])
usd = (mar.LossHL * mar.ReplacementUSDperHL)
ok("ch7 loss at replacement cost by stage (USD)", usd.astype(int).tolist(), [6270, 1664, 5481, 660])
ok("ch7 loss at replacement cost a month (USD)", int(usd.sum()), 14075)
ok("ch7 loss at replacement cost a year (USD)", int(usd.sum() * 12), 168900)
ok("ch7 peak season upper bound a month (USD)", int((mar.LossHL * mar.PeakUSDperHL).sum()), 43675)
feb = stage[(stage.Month == "2026-02-01") & (stage.Stage == "Cellar")].iloc[0]
ok("ch3 cellar loss in February (percent)", 100 * feb.LossHL / feb.InHL, 2.2, 1)
ok("ch3 cellar loss in March (percent)", 100 * mar.loc["Cellar", "LossHL"] / 8700, 2.4, 1)
ok("ch13 closure gap on a 400 hL axis (percent)", 100 * 22 / 400, 5.5, 1)

# ---------- chapter 8 and pattern 5: OEE ----------
run = load("Run")
planned, stop = run.PlannedMin.sum(), run.StopMin.sum()
made, rej = run.CansMade.sum(), run.Rejects.sum()
ok("ch8 runs", len(run), 10)
ok("ch8 planned minutes", int(planned), 2400)
ok("ch8 breakdown minutes", int(run.BreakdownMin.sum()), 120)
ok("ch8 changeover minutes", int(run.ChangeoverMin.sum()), 150)
ok("ch8 cans made", int(made), 902000)
ok("ch8 rejects", int(rej), 18000)
avail = (planned - stop) / planned
perf = made / ((run.PlannedMin - run.StopMin) * run.RatedCpm).sum()
qual = (made - rej) / made
ok("B.6 availability (percent)", 100 * avail, 88.8, 1)
ok("B.6 performance (percent)", 100 * perf, 84.7, 1)
ok("B.6 quality (percent)", 100 * qual, 98.0, 1)
ok("B.6 OEE (percent)", 100 * avail * perf * qual, 73.7, 1)
ok("B.6 OEE check equals the product", round(100 * (made - rej) / (run.PlannedMin * run.RatedCpm).sum(), 6), round(100 * avail * perf * qual, 6))
ok("ch8 good cans as hL", (made - rej) * 0.33 / 100, 2917, 0)
stops = load("Stop")
small = stops[stops.Category == "Small stop"]
ok("ch8 small stop minutes", small.Minutes.sum(), 190)
ok("ch8 small stop minutes in the first hour", small[small.HourIntoRun == 0].Minutes.sum(), 71)
ok("ch8 first hour share (percent)", 100 * 71 / 190, 37, 0)
ok("ch8 stop minutes tie to the run table", stops[stops.Category != "Small stop"].Minutes.sum(), 270)
ok("ch3 stop codes on the controller list (about 40)", 40, 40)

# ---------- chapter 9 and pattern 8: sales, mix and the bridge ----------
sales, sku = load("Sales"), load("Sku")
s = sales.merge(sku, on="Sku")
m1, m2 = s[s.Date == "2026-03-01"], s[s.Date == "2026-04-01"]
by_sku = m1.groupby("Sku").VolumeHL.sum().sort_values(ascending=False)
ok("ch9 SKU volumes (hL)", by_sku.astype(int).tolist(), [2970, 2227, 903, 760, 450, 420, 330, 270])
ok("ch9 SKU running total (percent)", [round(x, 1) for x in 100 * by_sku.cumsum() / 8330], [35.7, 62.4, 73.2, 82.4, 87.8, 92.8, 96.8, 100.0])
ok("ch9 pack totals (bottle, can, keg)", [int(m1[m1.Pack == k].VolumeHL.sum()) for k in ("Bottle", "Can", "Keg")], [3750, 2917, 1663])
ch = m1.groupby("Channel").VolumeHL.sum()
ok("ch9 channel totals (on, off, export)", [int(ch[k]) for k in ("On-trade", "Off-trade", "Export")], [2000, 5500, 830])
ok("ch9 export stout share (percent)", 100 * m1[(m1.Channel == "Export") & (m1.Brand == "Stout")].VolumeHL.sum() / 830, 13.3, 1)
ok("ch9 off-trade stout share (percent)", 100 * m1[(m1.Channel == "Off-trade") & (m1.Brand == "Stout")].VolumeHL.sum() / 5500, 6.4, 1)
contrib1 = (m1.NetRevenue - m1.VariableCost).sum()
contrib2 = (m2.NetRevenue - m2.VariableCost).sum()
ok("ch9 month 1 contribution (USD)", contrib1, 666300, 0)
ok("ch9 month 2 contribution (USD)", contrib2, 667200, 0)
ok("ch9 lager share of contribution (percent)", 100 * (m1[m1.Brand == "Lager"].NetRevenue - m1[m1.Brand == "Lager"].VariableCost).sum() / contrib1, 64.1, 1)
v1, v2 = m1.VolumeHL.sum(), m2.VolumeHL.sum()
unit1 = contrib1 / v1
br1, br2 = m1.groupby("Brand").sum(numeric_only=True), m2.groupby("Brand").sum(numeric_only=True)
bu1 = (br1.NetRevenue - br1.VariableCost) / br1.VolumeHL
volume_eff = (v2 - v1) * unit1
mix_eff = (br2.VolumeHL * bu1).sum() - v2 * unit1
price_eff = ((br2.NetRevenue / br2.VolumeHL - br1.NetRevenue / br1.VolumeHL) * br2.VolumeHL).sum()
cost_eff = ((br1.VariableCost / br1.VolumeHL - br2.VariableCost / br2.VolumeHL) * br2.VolumeHL).sum()
ok("B.9 volume effect (USD)", volume_eff, -10398, 0)
ok("B.9 mix effect (USD)", mix_eff, 7898, 0)
ok("B.9 price effect (USD)", price_eff, 11600, 0)
ok("B.9 cost effect (USD)", cost_eff, -8200, 0)
ok("B.9 bridge check", contrib2 - contrib1 - (volume_eff + mix_eff + price_eff + cost_eff), 0.0, 6)
dep = load("Depletions")
ok("ch9 closing stock (hL)", (dep.OpeningStockHL + dep.ShipmentsHL - dep.DepletionsHL).tolist(), [4530, 4860, 5040])
ok("ch9 sell-through (percent)", [round(x, 1) for x in 100 * dep.DepletionsHL / (dep.OpeningStockHL + dep.ShipmentsHL)], [63.3, 62.2, 61.8])

# ---------- chapters 11 and 15: tank days, lab offset, sensor rows ----------
f26 = fill[fill.FillId.str.contains("-26-")]
used = int(f26.ResidenceDays.sum())
ok("ch11 fills in 2026", len(f26), 174)
ok("ch11 tank days used, about 4,650", abs(used - 4650) <= 10, True)
ok("ch15 share of 5,475 tank days used (percent)", 100 * used / 5475, 85, 0)
ok("ch11 tanks full on average", used / 365, 12.7, 1)
over = 0
for _, t in f26.sort_values("HourZero").groupby("Tank"):
    over += int((t.HourZero.values[1:] < t.FillEnd.values[:-1]).sum())
ok("ch11 overlapping fills in the 2026 schedule", over, 0)
lab = load("Lab", parse_dates=["SampledAt"])
ls = lab[(lab.Analyte == "Apparent extract") & lab.FillId.isin(hg.FillId.unique())].merge(fill[["FillId", "HourZero"]], on="FillId")
ls["BatchHour"] = ((ls.SampledAt - ls.HourZero) / pd.Timedelta(hours=1)).astype(int)
ls = ls.merge(hg, on=["FillId", "BatchHour"])
ok("ch15 inline meter above the lab (degrees Plato)", (ls.Gravity - ls.Value).mean(), 0.1, 1)
temp = rd[rd.Tag == "Temp"].groupby("Tank").size()
ok("ch15 tanks with a full day of minute readings", int((temp == 1440).sum()), 14)
ok("ch3 dropout on F11 (hours missing)", (1440 - int(temp["F11"])) / 60, 6.0)

# ---------- chapter 12 and pattern 9: genealogy ----------
link = load("Link")
bt = link[link.ChildId == "BT03-26-071"].set_index("ParentId")
ok("B.10 share from F07-26-034", bt.loc["F07-26-034", "Share"], 0.667, 3)
ok("B.10 share from F09-26-036", bt.loc["F09-26-036", "Share"], 0.333, 3)
ok("ch12 fill F07-26-034 is brews B26-0067 and B26-0068 (hL)", int(link[link.ChildId == "F07-26-034"].HL.sum()), 600)
for child, part in link.groupby("ChildId"):
    assert abs(part.Share.sum() - 1) < 1e-3, child
ok("ch12 shares sum to 1 for every child", True, True)
ph = lab[lab.Analyte == "pH"].set_index("FillId").Value
ok("B.10 blend expected pH, bright tank BT03", sum(bt.Share[p] * ph[p] for p in bt.index), ph["BT03-26-071"], 2)

print(f"\nAll {COUNT} checks pass.")
