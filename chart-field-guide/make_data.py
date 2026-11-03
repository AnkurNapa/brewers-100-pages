"""Write every Kestrel Brewing CSV in data/ from fixed seeds. Synthetic data only.

Run: python3 make_data.py
Table and column names follow Appendix B.1 of The Brewer's Chart Field Guide.
"""
import csv
import os
import random
import sys
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "kestrel"))
import ch05_curves as C5  # noqa: E402  eleven healthy pale ale fills plus one stall (seed 26)
import ch06_fills as C6   # noqa: E402  forty lager final gravities (seed 26)

DATA = os.path.join(HERE, "data")
YEAR0 = datetime(2026, 1, 1)
BRANDS = {"Lager": 30, "Pale Ale": 16, "Stout": 23}          # residence in tank days (series bible)
OG = {"Lager": 12.0, "Pale Ale": 13.5, "Stout": 14.0}         # degrees Plato (series bible)
PRICE = {"Lager": 140, "Pale Ale": 180, "Stout": 170}         # USD a hL, net (series bible)
FILLS_2026 = 174                                              # 14.5 fills a month x 12
MIX = {"Lager": 127, "Pale Ale": 34, "Stout": 13}             # 73.2, 19.6 and 7.2 percent of 174


def write(name, header, rows):
    with open(os.path.join(DATA, name + ".csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def ts(d):
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def sg(plato):
    """Specific gravity from degrees Plato (MBAA polynomial, as the series uses)."""
    return 1 + plato / (258.6 - 227.1 * plato / 258.2)


# ---------- fills: twelve 2025 reference pale ale fills, then the 2026 schedule ----------
def reference_fills():
    rng = random.Random(26)
    starts = list(range(11))                 # eleven days, as figure 5.1
    rng.shuffle(starts)
    tanks = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12]
    t0 = datetime(2025, 10, 6, 14, 0)
    rows = [(tanks[k], t0 + timedelta(days=starts[k]), C5.HEALTHY[k], True) for k in range(11)]
    rows.append((9, t0 + timedelta(days=5, hours=12), C5.STALLED, False))   # the stalled fill sits in F09
    rows.sort(key=lambda r: r[1])
    out = []
    for i, (tank, hz, curve, ref) in enumerate(rows):
        fid = f"F{tank:02d}-25-{301 + i:03d}"
        out.append(dict(FillId=fid, Tank=f"F{tank:02d}", Brand="Pale Ale", HourZero=hz,
                        FillEnd=hz + timedelta(days=16), IsReference=ref, curve=curve, Seq=None))
    return out


def schedule_2026():
    rng = random.Random(2026)
    brands = [b for b, n in MIX.items() for _ in range(n)]
    rng.shuffle(brands)
    for must in (33, 35):                    # fills 34 and 36 are the chapter 12 blend parents, both lager
        if brands[must] != "Lager":
            j = next(i for i in range(60, FILLS_2026) if brands[i] == "Lager")
            brands[must], brands[j] = brands[j], brands[must]
    out = []
    for n in range(1, FILLS_2026 + 1):
        tank = (n - 34 + 6) % 15 + 1         # rotation that puts fill 34 in F07 and fill 36 in F09
        hz = YEAR0 + timedelta(days=round((n - 1) * 365 / FILLS_2026), hours=14)
        b = brands[n - 1]
        out.append(dict(FillId=f"F{tank:02d}-26-{n:03d}", Tank=f"F{tank:02d}", Brand=b, HourZero=hz,
                        FillEnd=hz + timedelta(days=BRANDS[b]), IsReference=False, curve=None, Seq=n))
    return out


REF = reference_fills()
SCHED = schedule_2026()
FILLS = REF + SCHED


def brews_of(f):
    n = f["Seq"]
    return (f"B26-{2 * n - 1:04d}", f"B26-{2 * n:04d}") if n else ("", "")


def make_fill_tank_date():
    write("Fill", ["FillId", "Tank", "Brand", "Brew1", "Brew2", "HourZero", "FillEnd", "ResidenceDays", "IsReference"],
          [[f["FillId"], f["Tank"], f["Brand"], *brews_of(f), ts(f["HourZero"]), ts(f["FillEnd"]),
            (f["FillEnd"] - f["HourZero"]).days, f["IsReference"]] for f in FILLS])
    write("Tank", ["Tank", "TankType", "CapacityHL"], [[f"F{t:02d}", "Unitank", 600] for t in range(1, 16)])
    rows, d = [], date(2026, 1, 1)
    while d.year == 2026:
        iso = d.isocalendar()
        rows.append([d.isoformat(), d.year, d.month, d.strftime("%b"), f"{iso[0]}-W{iso[1]:02d}", d.strftime("%a")])
        d += timedelta(days=1)
    write("Date", ["Date", "Year", "MonthNo", "Month", "BrewWeek", "Weekday"], rows)


# ---------- gravity: hourly table for the DAX band, 10 minute readings for the KQL band ----------
def make_gravity():
    hourly, readings = [], []
    rng = random.Random(15)
    for f in REF:
        for h, g in zip(C5.HOURS, f["curve"]):
            hourly.append([f["FillId"], h, round(g, 4)])
            e1, e2 = rng.uniform(0.005, 0.02), rng.uniform(0.005, 0.02)
            for j, noise in enumerate((0, e1, -e1, e2, -e2, 0)):   # zero sum, so each hour averages to its value
                t = f["HourZero"] + timedelta(hours=h, minutes=10 * j)
                readings.append([f["Tank"], "Gravity", ts(t), round(g + noise, 4)])
    write("HourlyGravity", ["FillId", "BatchHour", "Gravity"], hourly)
    return readings


def tank_brand_at(tank, t):
    for f in SCHED:
        if f["Tank"] == tank and f["HourZero"] <= t < f["FillEnd"]:
            return f["Brand"]
    return None


def make_readings(gravity_rows):
    """One day of minute temperature readings on all 15 tanks; F11 drops out for six hours."""
    rng = random.Random(36)
    base = {"Lager": 10.0, "Pale Ale": 18.0, "Stout": 19.0, None: 15.0}   # local values, degrees Celsius
    day0 = datetime(2026, 4, 14)
    rows = []
    for t in range(1, 16):
        tank = f"F{t:02d}"
        b = base[tank_brand_at(tank, day0 + timedelta(hours=12))]
        for m in range(1440):
            if tank == "F11" and 120 <= m < 480:          # 02:00 to 08:00 missing
                continue
            rows.append([tank, "Temp", ts(day0 + timedelta(minutes=m)), round(b + rng.gauss(0, 0.15), 2)])
    write("Readings", ["Tank", "Tag", "Time", "Value"], gravity_rows + rows)


# ---------- lager control chart fills (chapter 6) ----------
def make_batch():
    lagers = [f for f in SCHED if f["Brand"] == "Lager"][:40]
    rows, prev = [], None
    for i, (f, v) in enumerate(zip(lagers, C6.V), start=1):
        mr = "" if prev is None else round(abs(v - prev), 6)
        rows.append([i, f["FillId"], "Lager", round(v, 6), mr, i <= 20])
        prev = v
    write("Batch", ["FillSequence", "FillId", "Brand", "FinalGravity", "MovingRange", "IsBaseline"], rows)
    write("BatchAfterFix", ["FillSequence", "FinalGravity"], [[i, round(v, 6)] for i, v in enumerate(C6.AFTER, 1)])
    return lagers


# ---------- brews and extract yield (chapter 7) ----------
def make_brew():
    rng = random.Random(7)
    rows, noise = [], []
    for f in SCHED:
        for bid in brews_of(f):
            noise.append(rng.gauss(0, 0.006))
    months = [(f["HourZero"] - timedelta(hours=h)).month for f in SCHED for h in (26, 2)]
    for m in set(months):                                          # centre the noise in each month
        idx = [j for j, mm in enumerate(months) if mm == m]
        mu = sum(noise[j] for j in idx) / len(idx)
        for j in idx:
            noise[j] -= mu
    i = 0
    for f in SCHED:
        b = f["Brand"]
        nominal = 300 * 0.9982 * OG[b] * sg(OG[b])
        theo = 4070 if b == "Lager" else nominal / 0.926     # 5,300 kg x 0.768 as printed; pale ale and stout grist derived, local
        for k, bid in enumerate(brews_of(f)):
            cast = f["HourZero"] - timedelta(hours=26 if k == 0 else 2)
            e = 0 if bid == "B26-0068" else noise[i]
            rows.append([bid, f["FillId"], b, cast.date().isoformat(), 300, OG[b], round(nominal * (1 + e), 1), round(theo, 1)])
            i += 1
    write("Brew", ["BrewId", "FillId", "Brand", "CastDate", "CastHL", "OriginalPlato", "ExtractKg", "TheoreticalKg"], rows)


# ---------- genealogy (chapter 12) and lab results ----------
def make_link_lab(lagers):
    f34 = next(f for f in SCHED if f["Seq"] == 34)
    f36 = next(f for f in SCHED if f["Seq"] == 36)
    bt_day = max(f34["FillEnd"], f36["FillEnd"]) + timedelta(days=1)
    pack_day = bt_day + timedelta(days=1)
    lot = pack_day.strftime("L%y%m%d-C1-")
    bt_a, bt_b = "BT03-26-071", "BT04-26-072"                     # bright tank ID format is local to the companion
    links = []
    for f in (f34, f36):
        for bid in brews_of(f):
            links.append([f["FillId"], bid, 300, 0.5, "fill"])
    links += [[bt_a, f34["FillId"], 400, round(400 / 600, 4), "blend"], [bt_a, f36["FillId"], 200, round(200 / 600, 4), "blend"],
              [bt_b, f34["FillId"], 200, round(200 / 600, 4), "blend"], [bt_b, f36["FillId"], 400, round(400 / 600, 4), "blend"],
              [lot + "1", bt_a, 594, 1.0, "pack"], [lot + "2", bt_b, 594, 1.0, "pack"]]
    write("Link", ["ChildId", "ParentId", "HL", "Share", "LinkType"], links)

    rng = random.Random(45)
    seq = {}
    rows = []

    def add(fid, analyte, value, sampled, source="Lab"):
        key = sampled.strftime("%y%m%d")
        seq[key] = seq.get(key, 0) + 1
        lag = rng.choice([1, 2, 3, 4, 6, 26, 50])                  # hours from sample to entry; 26 and 50 are late
        rows.append([f"S{key}-{seq[key]:03d}", fid, analyte, value, ts(sampled), ts(sampled + timedelta(hours=lag)), source])

    for f in REF:                                                 # 08:00 and 18:00 samples on each pale ale fill
        d = f["HourZero"].replace(hour=0)
        while d <= f["HourZero"] + timedelta(hours=168):
            for hh in (8, 18):
                t = d + timedelta(hours=hh)
                bh = (t - f["HourZero"]).total_seconds() / 3600
                if 0 <= bh <= 168:
                    add(f["FillId"], "Apparent extract", round(f["curve"][int(bh)] - 0.10 + rng.gauss(0, 0.03), 2), t)
            d += timedelta(days=1)
    for f, v in zip(lagers, C6.V):
        add(f["FillId"], "Apparent extract", round(v, 3), f["FillEnd"] - timedelta(hours=4))
    add(f34["FillId"], "pH", 4.32, f34["FillEnd"] - timedelta(hours=3))
    add(f36["FillId"], "pH", 4.44, f36["FillEnd"] - timedelta(hours=3))
    add(bt_a, "pH", 4.36, bt_day + timedelta(hours=10))
    add(bt_b, "pH", 4.40, bt_day + timedelta(hours=10))
    rows.sort(key=lambda r: r[4])
    write("Lab", ["SampleId", "FillId", "Analyte", "Value", "SampledAt", "EnteredAt", "Source"], rows)
    moments = [ts(datetime(2025, 10, 6) + timedelta(hours=6 * i)) for i in range(4 * 24)]
    write("AsOf", ["Moment"], [[m] for m in moments])


# ---------- can line runs and stops (chapter 8) ----------
STOP_CODES = ["Can jam at infeed", "Lid feed empty", "Seamer jam", "Fill height reject burst", "Conveyor backup at packer",
              "Depalletiser fault", "Case packer jam", "Shrink film change", "Date coder fault", "Pasteuriser full",
              "Rinser fault", "Low CO2 pressure", "Bright tank low level", "Fallen can at filler", "Lid magazine refill",
              "Checkweigher reject burst", "Tray former jam", "Palletiser wait", "Operator away", "Glue unit low",
              "Air pressure low", "Cap sensor fault", "Can dent alarm", "Seam check stop", "Fill valve leak",
              "Guide rail jam", "Accumulation table full", "Inspector reset", "Lane divider jam", "Label sensor misread",
              "Seamer chuck wear", "Filler bowl level", "Vacuum pump trip", "Drive overload", "PLC fault",
              "Pasteuriser breakdown", "Conveyor motor failure", "Seamer bearing failure", "Filler valve failure", "Changeover"]


def make_runs():
    rng = random.Random(8)
    starts = [datetime(2026, 3, 2, 6) + timedelta(days=round(i * 2.8)) for i in range(10)]
    bd = [0] * 10
    for _ in range(120):
        bd[rng.randrange(10)] += 1
    runtime = [240 - 15 - b for b in bd]
    perf = [rng.uniform(0.80, 0.89) for _ in range(10)]
    cans = [round(r * 500 * p, -2) for r, p in zip(runtime, perf)]
    cans[-1] += 902000 - sum(cans)
    rej = [round(c * 18000 / 902000) for c in cans]
    rej[-1] += 18000 - sum(rej)
    runs = []
    for i in range(10):
        runs.append([starts[i].strftime("L%y%m%d-C1-1"), "C1", starts[i].date().isoformat(), 240, 15 + bd[i], bd[i], 15, 500, int(cans[i]), rej[i]])
    write("Run", ["RunId", "Line", "Date", "PlannedMin", "StopMin", "BreakdownMin", "ChangeoverMin", "RatedCpm", "CansMade", "Rejects"], runs)

    # small stop minutes by run and hour into the run: the figure 8.3 draw (seed 83)
    r83 = random.Random(83)
    w = [r83.uniform(0.4, 1.6) for _ in range(10)]
    grid = [[0] * 4 for _ in range(10)]
    for c, tot in enumerate([71, 48, 38, 33]):
        for _ in range(tot):
            grid[r83.choices(range(10), w)[0]][c] += 1
    weights = [1 / (k + 1) for k in range(34)]                    # small stop codes, a long tail
    stops = []
    for i, run in enumerate(runs):
        rid, t0 = run[0], starts[i]
        stops.append([rid, ts(t0), 15, "Changeover", "Changeover", 0])
        left, t = bd[i], 30
        while left > 0:
            m = min(left, rng.choice([6, 8, 10, 12, 15]))
            stops.append([rid, ts(t0 + timedelta(minutes=t)), m, rng.choice(STOP_CODES[34:39]), "Breakdown", t // 60])
            left -= m
            t += 47
        for hr in range(4):
            for k in range(grid[i][hr]):                            # one minute of small stops as two 30 second stops
                for half in range(2):
                    at = t0 + timedelta(minutes=60 * hr + rng.uniform(0, 59.5))
                    stops.append([rid, ts(at), 0.5, rng.choices(STOP_CODES[:34], weights)[0], "Small stop", hr])
    stops.sort(key=lambda s: (s[0], s[1]))
    write("Stop", ["RunId", "StopStart", "Minutes", "StopReason", "Category", "HourIntoRun"], stops)


# ---------- cast, dispatch and stage losses by month (chapters 7, 12, 13) ----------
STAGES = [("Cellar", 209, 30, 110), ("Filtration and bright beer", 52, 32, 112), ("Packaging", 87, 63, 143), ("Unexplained", 22, 30, 110)]


def make_volume():
    rng = random.Random(12)
    vol, stage, months = [], [], []
    for m in range(1, 13):
        disp = 8200 if m == 4 else 8330
        if m == 3:                                                 # the Kestrel month of chapters 7, 12, 13 and 15
            cast, losses = 8700, [209, 52, 87, 22]
        else:
            pct = [s[1] / 8700 * (1 + rng.gauss(0, 0.06)) for s in STAGES]
            if m == 2:
                pct[0] = 0.022                                     # the 2.2 percent month of chapter 3
            cast = round(disp / (1 - sum(pct)))
            losses = [round(cast * p) for p in pct[:3]]
            losses.append(cast - disp - sum(losses))
        month = date(2026, m, 1).isoformat()
        vol.append([month, cast, disp])
        left = cast
        for k, ((name, _, rc, peak), loss) in enumerate(zip(STAGES, losses), start=1):
            stage.append([month, name, k, left, left - loss, loss, rc, peak])
            left -= loss
        assert left == disp
        months.append((m, disp))
    write("Volume", ["Month", "CastHL", "DispatchedHL"], vol)
    write("Stage", ["Month", "Stage", "StageOrder", "InHL", "OutHL", "LossHL", "ReplacementUSDperHL", "PeakUSDperHL"], stage)

    rows = []
    for m, disp in months:
        days = [date(2026, m, d) for d in range(1, 32) if _valid(2026, m, d)]
        wts = [0 if d.weekday() == 6 else (0.5 if d.weekday() == 5 else 1) * rng.uniform(0.85, 1.15) for d in days]
        vals = [round(disp * w / sum(wts), 1) for w in wts]
        last = max(i for i, w in enumerate(wts) if w > 0)
        vals[last] = round(vals[last] + disp - sum(vals), 1)
        rows += [[d.isoformat(), v] for d, v in zip(days, vals)]
    write("Daily", ["Date", "DispatchedHL"], rows)


def _valid(y, m, d):
    try:
        date(y, m, d)
        return True
    except ValueError:
        return False


# ---------- sales (chapter 9) ----------
SPLIT = {  # March hL by brand, pack and channel; ties to tables 9.2 and 9.3
    ("Lager", "Bottle"): {"On-trade": 397, "Off-trade": 2273, "Export": 300},
    ("Lager", "Can"): {"Off-trade": 1927, "Export": 300},
    ("Lager", "Keg"): {"On-trade": 903},
    ("Pale Ale", "Keg"): {"On-trade": 560, "Off-trade": 200},
    ("Pale Ale", "Bottle"): {"Off-trade": 400, "Export": 50},
    ("Pale Ale", "Can"): {"Off-trade": 350, "Export": 70},
    ("Stout", "Bottle"): {"On-trade": 140, "Off-trade": 130, "Export": 60},
    ("Stout", "Can"): {"Off-trade": 220, "Export": 50},
}
ACCOUNT = {"On-trade": "ACC-ON-01", "Off-trade": "ACC-OFF-01", "Export": "ACC-EXP-01"}


def make_sales():
    write("Sku", ["Sku", "Brand", "Pack"], [[f"{b} {p.lower()}", b, p] for b, p in SPLIT])
    april = {"Lager": 5800, "Pale Ale": 1780, "Stout": 620}
    rows = []
    for month, scale_to, price_up, vcost in (("2026-03-01", None, 0, 70), ("2026-04-01", april, 2, 71)):
        for brand in ("Lager", "Pale Ale", "Stout"):
            cells = [(p, ch, v) for (b, p), chs in SPLIT.items() if b == brand for ch, v in chs.items()]
            total = sum(v for _, _, v in cells)
            vols = [v if scale_to is None else round(v * scale_to[brand] / total, 2) for _, _, v in cells]
            if scale_to:
                vols[-1] = round(vols[-1] + scale_to[brand] - sum(vols), 2)
            price = PRICE[brand] + (price_up if brand == "Lager" else 0)
            for (p, ch, _), v in zip(cells, vols):
                rows.append([month, f"{brand} {p.lower()}", ACCOUNT[ch], ch, v, round(v * price, 2), round(v * vcost, 2)])
    write("Sales", ["Date", "Sku", "Account", "Channel", "VolumeHL", "NetRevenue", "VariableCost"], rows)
    write("Depletions", ["Month", "Distributor", "OpeningStockHL", "ShipmentsHL", "DepletionsHL"],
          [["2026-07-01", "All distributors", 4000, 8330, 7800], ["2026-08-01", "All distributors", 4530, 8330, 8000],
           ["2026-09-01", "All distributors", 4860, 8330, 8150]])


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    make_fill_tank_date()
    make_readings(make_gravity())
    lagers = make_batch()
    make_brew()
    make_link_lab(lagers)
    make_runs()
    make_volume()
    make_sales()
    for n in sorted(os.listdir(DATA)):
        print(f"{n:22s} {os.path.getsize(os.path.join(DATA, n)):>9,d} bytes")
