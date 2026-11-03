"""Assert that every number the book prints from the companion data comes out of it, to the precision printed.

Run after make_data.py: python3 check_numbers.py
"""
from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parent / "data"
checks = 0


def eq(label, got, want, nd=0):
    global checks
    checks += 1
    assert round(got, nd) == round(want, nd), f"{label}: got {got!r}, book prints {want!r}"


def annuity(rate, years=3):
    return sum(1 / (1 + rate) ** t for t in range(1, years + 1))


# ---------------------------------------------------------------- minimum dataset: chapters 3, 4 and 6
md = pd.read_csv(D / "minimum_dataset.csv")
cast_month = md[md.stage == "fermentation"].set_index("batch_id")["date_in"].str[:7]
md["month"] = md.batch_id.map(cast_month)
jan = md[md.month == "2026-01"].groupby("stage")[["volume_in_hl", "volume_out_hl"]].sum()
cast = jan.loc["fermentation", "volume_in_hl"]
cellar = cast - jan.loc["filter", "volume_in_hl"]
filt = jan.loc["filter", "volume_in_hl"] - jan.loc["filter", "volume_out_hl"]
pack = jan.loc["package", "volume_in_hl"] - jan.loc["package", "volume_out_hl"]
closure = jan.loc["dispatch", "volume_in_hl"] - jan.loc["dispatch", "volume_out_hl"]
eq("3.2 cast", cast, 8700)
eq("3.2 cellar out", jan.loc["filter", "volume_in_hl"], 8491)
eq("3.2 filter out", jan.loc["filter", "volume_out_hl"], 8439)
eq("3.2 packaged", jan.loc["package", "volume_out_hl"], 8352)
eq("3.2 dispatched", jan.loc["dispatch", "volume_out_hl"], 8330)
for label, v, hl, pct in [("cellar", cellar, 209, 2.40), ("filter", filt, 52, 0.60), ("packaging", pack, 87, 1.00), ("closure", closure, 22, 0.25)]:
    eq(f"3.2 {label} hL", v, hl)
    eq(f"3.2 {label} percent", 100 * v / cast, pct, 2)
gap = cellar + filt + pack + closure
eq("3.2 total gap", gap, 370)
eq("3.2 gap percent", 100 * gap / cast, 4.25, 2)
eq("3.2 replacement", cellar * 30 + (gap - cellar) * 32, 11422)
eq("3.2 upper bound", cellar * 110 + (gap - cellar) * 112, 41022)
excess_f = filt - round(0.0045 * cast)
eq("3.3 filter normal", 0.0045 * cast, 39)
eq("3.3 filter excess", excess_f, 13)
eq("3.3 excess USD", excess_f * 32, 416)
eq("3.3 excess upper bound", excess_f * 112, 1456)
eq("4.4 gate gap", cast - 240 - jan.loc["package", "volume_out_hl"], 108)
eq("4.4 gate percent", 100 * 108 / cast, 1.24, 2)
eq("15.1 gate after tracing", cast - 313 - jan.loc["package", "volume_out_hl"], 35)
eq("15.1 gate after percent", 100 * 35 / cast, 0.40, 2)

w = md[md.stage != "cast"].pivot(index="batch_id", columns="stage", values=["volume_in_hl", "volume_out_hl", "heel_hl"])
qcast = w.volume_in_hl.fermentation.sum()
steps = [
    (w.volume_in_hl.fermentation - w.volume_out_hl.fermentation).sum(),
    (w.volume_in_hl.conditioning - w.volume_out_hl.conditioning - w.heel_hl.conditioning).sum(),
    w.heel_hl.conditioning.sum(),
    (w.volume_out_hl.conditioning - w.volume_in_hl["filter"]).sum(),
]
normal = [1.00, 0.32, 0.30, 0.30]
excess = [max(0, round(s - qcast * n / 100)) for s, n in zip(steps, normal)]
eq("6.2 quarter cast", qcast, 26100)
for s, want in zip(steps, [313, 131, 104, 78]):
    eq("6.2 step loss", s, want)
for e, want in zip(excess, [52, 47, 26, 0]):
    eq("6.2 step excess", e, want)
for s, n, pct in zip(steps, normal, [1.20, 0.50, 0.40, 0.30]):
    eq("6.2 step loss percent", 100 * s / qcast, pct, 2)
eq("6.2 volume in, conditioning", qcast - steps[0], 25787)
eq("6.2 volume in, heel", qcast - sum(steps[:2]), 25656)
eq("6.2 volume in, transfer", qcast - sum(steps[:3]), 25552)
eq("6.2 total loss", sum(steps), 626)
eq("6.2 total excess", sum(excess), 125)
eq("6.2 excess percent", 100 * sum(excess) / qcast, 0.48, 2)
eq("6.4 reached filter", qcast - sum(steps), 25474)
eq("6.4 carried wort cost", 24 / ((qcast - sum(steps)) / qcast), 24.59, 2)
eq("6.5 step valued quarter", excess[0] * 27 + (excess[1] + excess[2]) * 29.5, 3557.50, 2)
eq("6.5 step valued year", 4 * (excess[0] * 27 + (excess[1] + excess[2]) * 29.5), 14230)
year_excess = 4 * sum(excess)
eq("6.5 year excess", year_excess, 500)
eq("6.5 replacement", year_excess * 30, 15000)
eq("6.5 upper bound", year_excess * 110, 55000)
eq("6.6 fills in the quarter", len(w), 45)  # the book says "about 43"

# ---------------------------------------------------------------- 60 brews: chapter 5
b = pd.read_csv(D / "brewhouse_brews.csv")
sg = lambda p: 1 + p / (258.6 - (p / 258.2) * 227.1)
theo = b.grist_kg * (b.malt_fine_extract_dry_pct - b.fine_coarse_diff_pct) / 100 * (1 - b.malt_moisture_pct / 100)
eff = 100 * b.cast_volume_hl * 0.9982 * b.cast_gravity_p * sg(b.cast_gravity_p) / theo
eq("5.1 SG at 12.0", sg(12.0), 1.0484, 4)  # the polynomial gives 1.04838; the book prints 1.0484
eq("5.1 kg a hL", 0.9982 * 12 * sg(12.0), 12.56, 2)
eq("5.1 cast extract", 300 * 0.9982 * 12 * sg(12.0), 3767)
eq("5.1 theoretical", theo.iloc[0], 4070)
eq("5.1 kg lost", theo.iloc[0] - 300 * 0.9982 * 12 * sg(12.0), 303)
eq("5.2 brews 1 to 30 efficiency", eff[:30].mean(), 92.6, 1)
eq("5.2 conversion", b.conversion_eff_pct[:30].mean(), 98.5, 1)
eq("5.2 lauter", (100 * eff / b.conversion_eff_pct)[:30].mean(), 94.0, 1)
eq("5.5 brew 60", eff.iloc[-1], 92.0, 1)
malt = 5300 * 104500 / 300
eq("5.4 annual malt", malt, 1846167)
eq("5.4 one point kg", malt * (0.926 / 0.916 - 1), 20155)
eq("5.4 one point USD", round(malt * (0.926 / 0.916 - 1)) * 0.9, 18140)
drift_kg = round(malt * (round(eff[:30].mean(), 1) / round(eff.iloc[-1], 1) - 1))
eq("5.5 drift kg", drift_kg, 12040)
eq("5.5 drift USD", drift_kg * 0.9, 10836)

# ---------------------------------------------------------------- fill weights: chapter 7
f = pd.read_csv(D / "fill_weights.csv")
for got, want in zip(f.groupby("date").fill_ml.mean(), [333.6, 334.5, 333.9, 334.2, 334.4, 333.7, 333.7]):
    eq("7.2 daily mean", got, want, 1)
over = round(f.fill_ml.mean() - 330, 1)
eq("7.2 overfill", over, 4.0, 1)
cans_m = round(35000 / 0.33 * 100 / 1e6, 1)
give = round(cans_m * 1e6 * over / 100000)
eq("7.2 cans million", cans_m, 10.6, 1)
eq("7.2 giveaway hL", give, 424)
eq("7.2 hL per ml", cans_m * 1e6 / 1e5, 106)
eq("7.5 replacement", give * 32, 13568)
eq("7.5 upper bound", give * 112, 47488)
eq("7.5 price", give * 150, 63600)
eq("7.5 INR", give * 32 * 90, 1221120)
eq("7.5 EUR", give * 32 / 1.1, 12335)
eq("7.5 per ml", give * 32 / over, 3392)
eq("7.5 halved USD", give / 2 * 32, 6784)
eq("7.5 halved upper bound", give / 2 * 112, 23744)

# ---------------------------------------------------------------- effluent: chapter 8
e = pd.read_csv(D / "effluent_daily.csv")
e["cod_kg"] = e.effluent_m3 * e.cod_mg_l / 1000
e["excess"] = e.cod_kg - (e.cod_kg / e.packaged_hl).median() * e.packaged_hl
spike = e.loc[e.date == "2026-02-11", "excess"].iloc[0]
eq("8.2 spike kg", spike, 195)
eq("8.2 spike hL", spike / 13, 15)
eq("8.2 spike USD", round(spike / 13) * 32, 480)
eq("8.2 spike upper bound", round(spike / 13) * 112, 1680)

# ---------------------------------------------------------------- tank days: chapter 9
occ = pd.read_csv(D / "tank_occupancy.csv")
beers = pd.read_csv(D / "beers.csv").set_index("beer")
contrib = beers.net_price_usd_hl - beers.variable_cost_usd_hl
occ["c"] = 574.2 * occ.beer.map(contrib)
per_day = occ.groupby("beer").c.sum() / occ.groupby("beer").days.sum()
for k, want in [("Lager", 1340), ("Pale ale", 3948), ("Stout", 2497)]:
    eq(f"9.2 {k} per tank day", per_day[k], want)
eq("9.2 ratio", per_day["Pale ale"] / per_day["Lager"], 2.9, 1)
eq("9.2 lager INR", round(per_day["Lager"]) * 90, 120600)
eq("9.2 lager EUR", round(per_day["Lager"]) / 1.1, 1218)
y = beers.copy()
y["cast"] = 12 * y.dispatched_hl_month * 1.045
y["fills"] = y.cast / 600
y["td"] = y.fills * (y.days_in_tank + y.turnaround_days)
for k, c, fl, td in [("Lager", 76494, 127.5, 3825), ("Pale ale", 20440, 34.1, 545), ("Stout", 7524, 12.5, 288)]:
    eq(f"9.1 {k} cast", y.cast[k], c)
    eq(f"9.1 {k} fills", y.fills[k], fl, 1)
    eq(f"9.1 {k} tank days", y.td[k], td)
eq("9.1 total cast", y.cast.sum(), 104458)
eq("9.1 total fills", y.fills.sum(), 174.1, 1)
eq("9.1 tank days", y.td.sum(), 4658)
eq("9.1 utilisation", 100 * y.td.sum() / 5475, 85.1, 1)
blended = 100000 * 80 / round(y.td.sum())
eq("9.2 blended", blended, 1717)
plan = occ.groupby("beer")[["planned_days", "days"]].mean()
for k, p in [("Lager", 28.0), ("Pale ale", 15.2), ("Stout", 22.4)]:
    eq(f"9.3 {k} planned", plan.planned_days[k], p, 1)
lost = (plan.days - plan.planned_days) * y.fills
for k, want in [("Lager", 255), ("Pale ale", 27), ("Stout", 8)]:
    eq(f"9.3 {k} days lost", lost[k], want)
eq("9.3 total lost", lost.sum(), 290)
eq("9.3 plan use", round(y.td.sum()) - 290, 4368)
eq("9.3 plan share", 100 * 4368 / 5475, 79.8, 1)
hld = y.fills * 600 * y.days_in_tank
eq("9.4 lager hL-days", hld["Lager"], 2141832)
eq("9.4 hL-days", hld.sum(), 2585999)
eq("9.4 value-days", round(hld.sum()) * 27, 69821973)
eq("9.4 average cash", hld.sum() * 27 / 365, 191293)
eq("9.4 cost of money", 0.12 * hld.sum() * 27 / 365, 22955)
eq("9.4 lager share", 100 * hld["Lager"] / hld.sum(), 83)
eq("9.4 overrun cash", 290 * 600 * 27 / 365 * 0.12, 1545)
eq("9.5 days sold", round(y.fills.sum(), 1) * 0.2, 34.8, 1)
eq("9.5 contribution", 34.8 * round(blended), 59752)

# ---------------------------------------------------------------- true COGS: chapter 10
L = pd.read_csv(D / "cost_ledger_march.csv")
br = pd.read_csv(D / "march_brands.csv").set_index("brand")
pk = pd.read_csv(D / "march_brand_pack.csv").set_index("pack")
hl = br.hl_sold.sum()
cogs = L[L.in_cogs == "yes"].usd_march.sum()
eq("10.1 COGS", cogs, 680000)
eq("10.1 per hL", cogs / hl, 85.00, 2)
eq("10.1 per hL cast", cogs / (1.045 * hl), 81.34, 2)
eq("10.1 INR", cogs / hl * 90, 7650)
eq("10.1 EUR", cogs / hl / 1.1, 77.27, 2)
pool = L.loc[L.line == "Overhead", "usd_march"].sum()
eq("10.2 per brew", pool / br.brews.sum(), 6518.52, 2)
eq("10.2 per hL-day", pool / (br.hl_sold * br.tank_days_a_fill).sum(), 0.8302, 4)
brew = pool / br.brews.sum() * br.brews / br.hl_sold
td = pool / (br.hl_sold * br.tank_days_a_fill).sum() * br.tank_days_a_fill
eq("10.2 lager by brew", brew["Lager"], 21.73, 2)
eq("10.2 ale by brew", brew["Pale ale"], 22.81, 2)
eq("10.2 lager by tank day", td["Lager"], 24.91, 2)
eq("10.2 ale by tank day", td["Pale ale"], 13.28, 2)
lu = L.loc[L.line.isin(["Direct labour", "Utilities"]), "usd_march"].sum() / hl
mat = lambda brand: L.loc[(L.line == "Materials") & (L.cost_centre == brand), "usd_march"].sum() / br.hl_sold[brand]
store = L.loc[L.cost_centre == "Bottle and keg store", "usd_march"].sum()
bk = pk.loc[["Bottle", "Keg"]]
pack_cost = store * bk.packaging_standard_usd_hl / (bk.hl_sold * bk.packaging_standard_usd_hl).sum()
can = L.loc[L.cost_centre == "Can line", "usd_march"].sum() / pk.hl_sold["Can"]
bottle = mat("Lager") + pack_cost["Bottle"] + lu + td["Lager"]
keg = mat("Lager") + pack_cost["Keg"] + lu + td["Lager"]
ale = mat("Pale ale") + can + lu + td["Pale ale"]
lager = (bottle * pk.hl_sold["Bottle"] + keg * pk.hl_sold["Keg"]) / br.hl_sold["Lager"]
eq("10.3 lager bottle", bottle, 91.41, 2)
eq("10.3 lager keg", keg, 57.41, 2)
eq("10.5 ale true cost", ale, 91.78, 2)
eq("10.5 lager true cost", lager, 82.74, 2)
eq("10.5 lager direct", lager - td["Lager"], 57.83, 2)
eq("10.5 ale direct", ale - td["Pale ale"], 78.50, 2)
eq("10.5 lager margin", 140 - lager, 57.26, 2)
eq("10.5 ale margin", 180 - ale, 88.22, 2)
eq("10.5 lager March margin", (140 - lager) * 6000, 343566)
eq("10.5 ale March margin", (180 - ale) * 2000, 176434)
eq("10.5 lager INR", lager * 90, 7447)
eq("10.5 lager EUR", lager / 1.1, 75.22, 2)
eq("10.5 paper ratio", 95 / 55, 1.73, 2)
eq("10.5 true ratio", (180 - ale) / (140 - lager), 1.54, 2)

# ---------------------------------------------------------------- ledger: chapter 11
dr = pd.read_csv(D / "loss_drivers.csv").set_index("row")
dr.loc[2, "quantity"] = year_excess
dr = dr.dropna(subset=["quantity"])
rep = (dr.quantity * dr.replacement_usd_per_unit + dr.material_usd).round(0)
ub = (dr.quantity * dr.upper_bound_usd_per_unit).round(0)
for r, a, u in [(1, 10836, 10836), (2, 15000, 55000), (3, 5024, 17584), (4, 13568, 47488), (5, 20839, 40040), (7, 13200, 13200), (8, 6000, 6000), (9, 1545, 1545)]:
    eq(f"11.1 row {r} replacement", rep[r], a)
    eq(f"11.1 row {r} upper bound", ub[r], u)
eq("11.1 total", rep.sum(), 86012)
eq("11.1 upper total", ub.sum(), 191693)
eq("11.1 INR", rep.sum() * 90, 7741080)
eq("11.1 EUR", rep.sum() / 1.1, 78193)
eq("11.1 per hL", rep.sum() / 100000, 0.86, 2)
eq("11.2 beer hL", dr.quantity[[2, 3, 4, 5]].sum(), 1361)
eq("11.2 beer replacement", rep[[2, 3, 4, 5]].sum(), 54431)
eq("11.2 beer upper bound", ub[[2, 3, 4, 5]].sum(), 160112)
eq("11.2 beer at price", dr.quantity[[2, 3, 4, 5]].sum() * 150, 204150)
eq("11.3 rows 1 to 5", rep[[1, 2, 3, 4, 5]].sum(), 65267)
eq("11.3 not explained", 128000 - rep[[1, 2, 3, 4, 5]].sum(), 62733)
eq("11.3 share", 100 * 62733 / 128000, 49)
top3 = rep.nlargest(3).sum()
eq("11.4 top three", top3, 49407)
eq("11.4 share", 100 * top3 / rep.sum(), 57.4, 1)

# ---------------------------------------------------------------- fixes: chapters 12 and 15
fx = pd.read_csv(D / "fixes.csv").set_index("fix")
fx["exp"] = fx.value_usd * fx.probability
fx["pb"] = fx.cost_usd / (fx.exp / 12)
fx["npv"] = fx.exp * annuity(0.12) - fx.cost_usd
eq("12.2 annuity", annuity(0.12), 2.4018, 4)
for k, ex, pb, npv in [("A", 9000, 8.0, 15616), ("B", 4749, 6.3, 8906), ("C", 5940, 36.4, -3733), ("D", 2100, 228.6, -34956), ("E", 23901, 1.5, 54406), ("F", 21960, 1.6, 49744)]:
    eq(f"12.3 {k} expected", fx.exp[k], ex)
    eq(f"12.3 {k} payback", fx.pb[k], pb, 1)
    eq(f"12.3 {k} NPV", fx.npv[k], npv)
eq("12.2 A per month", fx.exp["A"] / 12, 750)
for t, want in [(1, 8036), (2, 7175), (3, 6406)]:
    eq("12.2 A discounted year", 9000 / 1.12 ** t, want)
eq("12.2 A NPV INR", round(fx.npv["A"]) * 90, 1405440)
eq("12.2 A NPV EUR", round(fx.npv["A"]) / 1.1, 14196)
eq("12.2 A upper NPV", 55000 * 0.6 * annuity(0.12) - 6000, 73260)
eq("12.2 A upper payback", 6000 / (33000 / 12), 2.2, 1)
eq("12.2 A at 0.30", 4500 * annuity(0.12) - 6000, 4808)
eq("12.2 A at 20 percent", 9000 * annuity(0.20) - 6000, 12958)
assert "".join(fx.sort_values("value_usd", ascending=False).index) == "FEACBD"
assert "".join(fx.sort_values("pb").index) == "EFBACD"
assert "".join(fx.sort_values("probability", ascending=False).index) == "BACEDF"
checks += 3
for k, want in [("E", 20901), ("A", 3000), ("B", 2249)]:
    eq(f"15.2 {k} net year one", fx.exp[k] - fx.cost_usd[k], want)
eq("15.3 days freed", round(290 / 12, 1) - 15.0, 9.2, 1)
eq("15.3 indicated", 9.2 * 0.2 * 1717, 3159)
eq("14.2 cellar saving", (round(500 / 12, 1) - 29.2) * 30, 375)

# ---------------------------------------------------------------- shocks: chapter 13
si = pd.read_csv(D / "shock_inputs.csv").set_index("line")
sc = pd.read_csv(D / "shock_scenarios.csv").set_index("scenario")


def lines(mp, ep, ap):
    m, en, a = 1 + mp / 100, 1 + ep / 100, 1 + 0.6 * ap / 100
    out = {}
    for n, r in si.iterrows():
        per = r.malt_usd_hl * m + r.energy_usd_hl * en + r.other_usd_hl
        out[n] = round(r.base_usd * m if r.method == "malt_only" else r.base_usd * per / 27 if r.method == "follows_carried_cost" else r.beer_hl * per + r.can_material_usd * a)
    return pd.Series(out)


T = {s: lines(*sc.loc[s]) for s in sc.index}
for s, want in [("Base", [10836, 15000, 5024, 34407, 1545]), ("Stress", [13003, 17190, 5712, 38560, 1796]), ("Opportunity", [9752, 13905, 4680, 32295, 1420])]:
    for got, wv in zip(T[s], want):
        eq(f"13.1 {s} line", got, wv)
base, stress, opp = (T[s].sum() for s in ["Base", "Stress", "Opportunity"])
eq("13.1 base", base, 66812)
eq("13.1 stress", stress, 76261)
eq("13.1 opportunity", opp, 62052)
eq("13.1 stress adds", stress - base, 9449)
eq("13.1 stress percent", 100 * (stress - base) / base, 14.1, 1)
eq("13.1 opportunity trims", base - opp, 4760)
eq("13.1 INR", base * 90, 6013080)
eq("13.1 EUR", base / 1.1, 60738)
for n, want in [("Cellar", 14.6), ("Filtration", 13.7), ("Can line", 12.1), ("Cash in tank days", 16.2), ("Extract", 20.0)]:
    eq(f"13.3 {n} change", 100 * (T["Stress"][n] / T["Base"][n] - 1), want, 1)
eq("13.2 translated", base * 0.95 / 1.1, 57701)
eq("13.2 translation drop", base / 1.1 - base * 0.95 / 1.1, 3037)
eq("13.2 transaction", base * 90 * 0.4 * 0.05, 120262)
eq("13.4 three years", 20000 * annuity(0.12), 48037)
eq("13.4 value", 0.5 * 20000 * annuity(0.12) - 8000, 16018)
eq("13.4 at 16 percent", 0.5 * 20000 * annuity(0.16) - 8000, 14459)
eq("13.4 at 0.7", 0.7 * 20000 * annuity(0.12) - 8000, 25626)

print(f"All {checks} checks pass.")
