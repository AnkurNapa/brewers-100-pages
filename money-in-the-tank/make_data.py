"""Write every CSV in data/ for The Money in the Tank companion.

All data is synthetic Kestrel Brewing data from fixed seeds. No real brewery's numbers.
Run: python3 make_data.py
"""
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"


def sg_from_plato(p):
    """Specific gravity from degrees Plato (the reference polynomial used in chapter 5.1)."""
    return 1 + p / (258.6 - (p / 258.2) * 227.1)


def extract_kg(plato, volume_hl):
    """Kilograms of extract in a volume of wort: hL x 0.9982 x degrees Plato x SG."""
    return volume_hl * 0.9982 * plato * sg_from_plato(plato)


# ---------------------------------------------------------------- minimum dataset (chapters 3, 4, 6)
# Losses per month in hL for the beer cast that month, followed to dispatch.
# January is the month printed in chapter 3.2; the quarter is the table in chapter 6.2.
STEP_TOTALS = {
    "fermentation": [104, 104, 105],
    "conditioning": [44, 43, 44],
    "heel": [35, 35, 34],
    "transfer": [26, 26, 26],
    "filter": [52, 52, 53],
    "package": [87, 87, 87],
    "closure": [22, 22, 22],
}
COST = {"cast": 24.00, "fermentation": 27.00, "conditioning": 29.50, "filter": 32.00, "package": 63.00, "dispatch": 63.00}
FILLS_A_MONTH = 15  # 14 fills of two brews plus one fill of one brew: 29 brews, 8,700 hL


def split_tenths(total_tenths, weights, rng, forced=None):
    """Split a whole number of tenths of a hL across fills so the parts add back exactly."""
    forced = forced or {}
    out = np.zeros(len(weights), dtype=int)
    free = [i for i in range(len(weights)) if i not in forced]
    for i, v in forced.items():
        out[i] = v
    rest = total_tenths - sum(forced.values())
    w = np.array([weights[i] for i in free], dtype=float)
    out[free] = rng.multinomial(rest, w / w.sum())
    return out


def minimum_dataset():
    rng = np.random.default_rng(3)
    rows, brew_no = [], 0
    for m in range(3):
        month_start = date(2026, m + 1, 1)
        fill_tenths = [6000] * (FILLS_A_MONTH - 1) + [3000]
        weights = [v * rng.lognormal(0, 0.25) for v in fill_tenths]
        loss = {}
        for step, totals in STEP_TOTALS.items():
            forced = {}
            if step == "transfer" and m == 1:
                forced = {6: 50}  # one February transfer loses 5.0 hL: the notebook flags it
            if step == "fermentation" and m == 2:
                forced = {3: 72}  # fill F07-26-034 loses 7.2 hL in fermentation, as in Appendix C
            loss[step] = split_tenths(totals[m] * 10, weights, rng, forced)
        for k in range(FILLS_A_MONTH):
            seq = m * FILLS_A_MONTH + k + 1
            vessel = f"FV{(seq - 1 + 3) % 15 + 1:02d}"
            batch = f"F{vessel[2:]}-26-{seq:03d}"
            cast_day = month_start + timedelta(days=k)
            brews = 2 if fill_tenths[k] == 6000 else 1
            brew_ids = []
            for _ in range(brews):
                brew_no += 1
                bid = f"B26-{brew_no:04d}"
                brew_ids.append(bid)
                kettle = round(300 * 1.028 + rng.normal(0, 0.4), 1)
                rows.append([batch, bid, "cast", vessel, cast_day, cast_day, kettle, 300.0, None, 20, 12.0, 12.0, "flow", COST["cast"]])
            parent = "|".join(brew_ids)
            v = fill_tenths[k]
            f_out = v - loss["fermentation"][k]
            c_out = f_out - loss["conditioning"][k] - loss["heel"][k]
            fl_in = c_out - loss["transfer"][k]
            fl_out = fl_in - loss["filter"][k]
            p_out = fl_out - loss["package"][k]
            d_out = p_out - loss["closure"][k]
            d = lambda n: cast_day + timedelta(days=n)
            rows += [
                [batch, parent, "fermentation", vessel, d(0), d(8), v / 10, f_out / 10, None, 20, 12.0, 12.0, "flow", COST["fermentation"]],
                [batch, parent, "conditioning", vessel, d(8), d(26), f_out / 10, c_out / 10, loss["heel"][k] / 10, 20, 12.0, 12.0, "level", COST["conditioning"]],
                [batch, parent, "filter", "FLT01", d(26), d(26), fl_in / 10, fl_out / 10, None, 20, 12.0, 12.0, "flow", COST["filter"]],
                [batch, parent, "package", "PACK", d(27), d(28), fl_out / 10, p_out / 10, None, 20, 12.0, 12.0, "counter", COST["package"]],
                [batch, parent, "dispatch", "GATE", d(29), d(35), p_out / 10, d_out / 10, None, 20, 12.0, 12.0, "counter", COST["dispatch"]],
            ]
    cols = ["batch_id", "brew_id", "stage", "vessel_id", "date_in", "date_out", "volume_in_hl", "volume_out_hl", "heel_hl",
            "volume_temp_c", "gravity_in_p", "gravity_out_p", "measure_source", "cost_usd_per_hl"]
    df = pd.DataFrame(rows, columns=cols)
    # cost needs two decimals, so write that column as text
    df["cost_usd_per_hl"] = df["cost_usd_per_hl"].map(lambda x: f"{x:.2f}")
    df.to_csv(DATA / "minimum_dataset.csv", index=False, float_format="%.1f")


# ---------------------------------------------------------------- 60 brews (chapter 5)
def brewhouse_brews():
    # Same seed and draw order as the figure 5.2 script, so the line matches the printed figure.
    random.seed(52)
    eff = []
    for b in range(1, 61):
        base = 92.6 if b <= 30 else 92.6 - 0.6 * (b - 30) / 30
        n = max(-0.18, min(0.18, random.gauss(0, 0.09)))
        eff.append(round(base + n, 2))
    eff[-1] = 92.0
    rng = random.Random(5)
    theoretical = 5300 * (81.0 - 1.0) / 100 * (1 - 0.04)
    rows = []
    for b in range(1, 61):
        e = eff[b - 1]
        target = theoretical * e / 100
        lo, hi = 10.0, 14.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if extract_kg(mid, 300.0) < target:
                lo = mid
            else:
                hi = mid
        plato = round((lo + hi) / 2, 4)
        lauter = 94.0 + rng.gauss(0, 0.05)
        conversion = round(e / lauter * 100, 2)
        gap = 1.30 if b <= 30 else 1.30 + 0.12 * (b - 30) / 30
        rows.append([f"B26-{100 + b:04d}", date(2026, 4, 1) + timedelta(days=b - 1), 5300, 81.0, 1.0, 4.0, 300.0, 20,
                     plato, conversion, round(gap, 3), round(2.0 + rng.gauss(0, 0.1), 2)])
    cols = ["brew_id", "brew_date", "grist_kg", "malt_fine_extract_dry_pct", "fine_coarse_diff_pct", "malt_moisture_pct",
            "cast_volume_hl", "cast_temp_c", "cast_gravity_p", "conversion_eff_pct", "mill_roll_gap_mm", "last_runnings_p"]
    pd.DataFrame(rows, columns=cols).to_csv(DATA / "brewhouse_brews.csv", index=False)


# ---------------------------------------------------------------- fill weights (chapter 7)
def fill_weights():
    rng = np.random.default_rng(7)
    day_means = [333.6, 334.5, 333.9, 334.2, 334.4, 333.7, 333.7]  # figure 7.2
    shift_offset = {"A": -0.2, "B": -0.2, "C": 0.4}
    heads = 40
    rows = []
    for i, mean in enumerate(day_means):
        day = date(2026, 3, 2) + timedelta(days=i)
        for shift, off in shift_offset.items():
            noise = rng.normal(0, 1.2, heads)
            noise[16] += 1.5  # filler head 17 runs high
            noise -= noise.mean()
            for h in range(heads):
                rows.append([day, day.strftime("%a"), shift, h + 1, round(mean + off + noise[h], 2)])
    pd.DataFrame(rows, columns=["date", "day", "shift", "filler_head", "fill_ml"]).to_csv(DATA / "fill_weights.csv", index=False)


# ---------------------------------------------------------------- effluent (chapter 8)
def effluent_daily():
    rng = np.random.default_rng(8)
    spikes = {date(2026, 1, 20): 120.0, date(2026, 2, 11): 196.0, date(2026, 2, 26): 90.0, date(2026, 3, 17): 260.0}
    rows = []
    for i in range(90):
        day = date(2026, 1, 1) + timedelta(days=i)
        hl = round(120 + rng.normal(0, 10), 1) if day.weekday() == 6 else round(300 + rng.normal(0, 20), 1)
        m3 = round(hl * 0.36 * (1 + rng.normal(0, 0.03)), 1)
        base_kg = hl * 0.72
        if day in spikes:
            load = base_kg + spikes[day]
        else:
            load = base_kg * (1 + rng.normal(0, 0.03))
        rows.append([day, hl, m3, round(load / m3 * 1000, 3)])
    pd.DataFrame(rows, columns=["date", "packaged_hl", "effluent_m3", "cod_mg_l"]).to_csv(DATA / "effluent_daily.csv", index=False)


# ---------------------------------------------------------------- tank occupancy (chapter 9)
BEERS = pd.DataFrame(
    [["Lager", 6100, 28, 2, 140, 70], ["Pale ale", 1630, 14, 2, 180, 70], ["Stout", 600, 21, 2, 170, 70]],
    columns=["beer", "dispatched_hl_month", "days_in_tank", "turnaround_days", "net_price_usd_hl", "variable_cost_usd_hl"],
)


def tank_occupancy():
    rng = random.Random(9)
    fills = []
    fills += [("Lager", 28, 30)] * 128
    fills += [("Pale ale", 15, 16)] * 27 + [("Pale ale", 16, 16)] * 7
    fills += [("Stout", 22, 23)] * 8 + [("Stout", 23, 23)] * 5
    rng.shuffle(fills)
    reasons = ["waiting for a bright tank"] * 5 + ["diacetyl rest ran long"] * 2 + ["lab hold", "slow fermentation", "waiting for a filling slot"]
    free = {f"FV{t:02d}": date(2026, 1, 1) + timedelta(days=rng.randint(0, 14)) for t in range(1, 16)}
    rows = []
    for seq, (beer, planned, actual) in enumerate(fills, start=1):
        tank = min(free, key=free.get)
        start = free[tank]
        end = start + timedelta(days=actual)
        reason = rng.choice(reasons) if actual > planned else ""
        rows.append([f"F{tank[2:]}-26-{seq:03d}", tank, beer, start, end, actual, planned, reason])
        free[tank] = end + timedelta(days=rng.choice([0, 0, 1, 1, 2, 3]))
    cols = ["batch_code", "tank", "beer", "occupied_from", "occupied_to", "days", "planned_days", "overrun_reason"]
    pd.DataFrame(rows, columns=cols).sort_values(["occupied_from", "tank"]).to_csv(DATA / "tank_occupancy.csv", index=False)


# ---------------------------------------------------------------- cost ledger (chapter 10)
def cost_ledger():
    pd.DataFrame(
        [["Materials", "Lager", "yes", 105000], ["Materials", "Pale ale", "yes", 47000],
         ["Packaging", "Bottle and keg store", "yes", 164000], ["Packaging", "Can line", "yes", 84000],
         ["Direct labour", "Plant", "yes", 48000], ["Utilities", "Plant", "yes", 56000],
         ["Overhead", "Plant", "yes", 176000], ["Freight", "Plant", "no, cost to serve", 56000]],
        columns=["line", "cost_centre", "in_cogs", "usd_march"],
    ).to_csv(DATA / "cost_ledger_march.csv", index=False)
    pd.DataFrame(
        [["Lager", 6000, 20, 30, 140], ["Pale ale", 2000, 7, 16, 180]],
        columns=["brand", "hl_sold", "brews", "tank_days_a_fill", "net_price_usd_hl"],
    ).to_csv(DATA / "march_brands.csv", index=False)
    pd.DataFrame(
        [["Lager", "Bottle", 4470, 36.0], ["Lager", "Keg", 1530, 2.0], ["Pale ale", "Can", 2000, 42.0]],
        columns=["brand", "pack", "hl_sold", "packaging_standard_usd_hl"],
    ).to_csv(DATA / "march_brand_pack.csv", index=False)


# ---------------------------------------------------------------- ledger, fixes and shocks (chapters 11 to 13)
def ledger_fixes_shocks():
    pd.DataFrame(
        [[1, "Extract (scenario)", 12040, "kg of malt", 0.90, 0.90, 0, "5.5"],
         [2, "Cellar", None, "hL excess, from minimum_dataset.csv", 30, 110, 0, "6.5"],
         [3, "Filtration", 157, "hL excess", 32, 112, 0, "7.1"],
         [4, "Fill giveaway", 424, "hL", 32, 112, 0, "7.5"],
         [5, "Packaging rejects (can line)", 280, "hL in 84,848 cans", 32, 143, 11879, "7.3"],
         [6, "Beer to drain", None, "inside rows 2, 3 and 5", None, None, 0, "8.1"],
         [7, "Water and effluent", 100000, "hL dispatched at USD 0.132 a hL", 0.132, 0.132, 0, "8.2"],
         [8, "Line minutes", 6000, "minutes of utilities", 1.00, 1.00, 0, "7.4"],
         [9, "Tank days, cash held", 290, "overrun tank days", round(600 * 27 * 0.12 / 365, 7), round(600 * 27 * 0.12 / 365, 7), 0, "9.4"]],
        columns=["row", "loss", "quantity", "unit", "replacement_usd_per_unit", "upper_bound_usd_per_unit", "material_usd", "from_chapter"],
    ).to_csv(DATA / "loss_drivers.csv", index=False)
    pd.DataFrame(
        [["A", "Cellar", "Heel and cone dump SOP, a flow meter on transfers", 15000, 55000, 0.60, 6000, "Yes, minimum dataset", "One SOP", "Low", "Yes"],
         ["B", "Giveaway", "Fill target cut by 2 ml, weigh checks", 6784, 23744, 0.70, 2500, "Yes, check weigher", "One SOP", "Low", "Yes"],
         ["C", "Water", "Conductivity sensor and valve on CIP pushes, ratio 4.5 to 4.0", 13200, 13200, 0.45, 18000, "Partly, no meter on pushes", "One instrument", "Low", "Next quarter"],
         ["D", "Line minutes", "Stop counter, reason codes, link to the plant system", 6000, 6000, 0.35, 40000, "No, stops are not coded", "Three: counter, plant link, reason screen", "Medium", "No"],
         ["E", "Waiting days", "Book the bright tank and the diacetyl check ahead", 59752, 59752, 0.40, 3000, "Yes, occupancy table and brew plan", "One schedule rule", "Low, the beer is unchanged", "Yes"],
         ["F", "Lager price", "Raise lager by USD 1.00 a hL", 73200, 73200, 0.30, 3000, "Yes", "None", "High, customers", "Owner's call"]],
        columns=["fix", "name", "what_changes", "value_usd", "upper_bound_value_usd", "probability", "cost_usd", "data_ready", "change_load", "blast_radius", "this_quarter"],
    ).to_csv(DATA / "fixes.csv", index=False)
    pd.DataFrame(
        [["Extract", "malt_only", None, None, None, None, 0, 10836],
         ["Cellar", "beer", 500, 15.90, 4.00, 10.10, 0, None],
         ["Filtration", "beer", 157, 15.90, 4.00, 12.10, 0, None],
         ["Can line", "beer", 704, 15.90, 4.00, 12.10, 11879, None],
         ["Cash in tank days", "follows_carried_cost", None, 15.90, 4.00, 7.10, 0, 1545]],
        columns=["line", "method", "beer_hl", "malt_usd_hl", "energy_usd_hl", "other_usd_hl", "can_material_usd", "base_usd"],
    ).to_csv(DATA / "shock_inputs.csv", index=False)
    pd.DataFrame(
        [["Base", 0, 0, 0], ["Stress", 20, 30, 15], ["Opportunity", -10, -15, -8]],
        columns=["scenario", "malt_pct", "energy_pct", "aluminium_pct"],
    ).to_csv(DATA / "shock_scenarios.csv", index=False)


def main():
    DATA.mkdir(exist_ok=True)
    minimum_dataset()
    brewhouse_brews()
    fill_weights()
    effluent_daily()
    BEERS.to_csv(DATA / "beers.csv", index=False)
    tank_occupancy()
    cost_ledger()
    ledger_fixes_shocks()
    for p in sorted(DATA.glob("*.csv")):
        print(f"{p.name:28s} {p.stat().st_size:>8,d} bytes")


if __name__ == "__main__":
    main()
