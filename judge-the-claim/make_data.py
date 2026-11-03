"""Writes every CSV in data/ from fixed seeds. Synthetic Kestrel Brewing data only.

Run: python3 make_data.py
"""
import csv
import math
import datetime as dt
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def write(name, header, rows):
    with open(os.path.join(DATA, name), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def split(total, parts, rng, spread=0.08):
    """Split a total into parts with one decimal place that add back exactly."""
    w = [rng.uniform(1 - spread, 1 + spread) for _ in range(parts)]
    vals = [round(total * x / sum(w), 1) for x in w]
    vals[-1] = round(total - sum(vals[:-1]), 1)
    return vals


# The vendor case inputs, Appendix B (series bible v4). Every notebook reads these.
INPUTS = [
    ("B1", "volume_hL_a_year", 100000),
    ("B2", "cellar_loss_rate", 0.024),
    ("B3", "share_recovered_claim", 0.20),
    ("B4", "value_lost_hL_replacement_usd", 30),
    ("B5", "licence_usd_a_month", 1400),
    ("B6", "cloud_bill_usd_a_month", 250),
    ("B9", "value_lost_hL_upper_bound_usd", 110),
    ("B12", "excess_cellar_loss_rate", 0.005),
    ("B15", "p_banked", 0.45),
    ("B18", "install_usd", 6000),
    ("", "data_prep_hours", 120),
    ("", "contractor_rate_usd_an_hour", 50),
    ("", "people_hours_a_week_first_13_weeks", 4),
    ("", "people_hours_a_week_after", 1),
    ("", "loaded_rate_usd_an_hour", 40),
    ("", "exit_hours", 30),
    ("", "selling_price_usd_a_hL", 150),
    ("", "pilot_fee_usd", 9000),
    ("", "usd_to_inr_book", 90),
    ("", "eur_to_usd_book", 1.10),
]

# Twelve months to October 2026. The last quarter matches chapter 7.1 exactly.
MONTHS = [  # month, cast hL, lost hL
    ("2025-11", 8200, 180), ("2025-12", 7600, 152), ("2026-01", 7400, 148),
    ("2026-02", 7600, 160), ("2026-03", 8400, 193), ("2026-04", 8800, 220),
    ("2026-05", 9300, 242), ("2026-06", 10000, 280), ("2026-07", 10200, 285),
    ("2026-08", 8000, 200), ("2026-09", 9500, 228), ("2026-10", 9500, 220),
]
BAD_WEEK = dt.date(2026, 5, 11)  # the yeast crop week of chapter 2.2.1, 3.6 percent


def monthly_and_weekly():
    write("kestrel_monthly_loss.csv", ["month", "cast_hL", "lost_hL", "loss_rate_pct"],
          [(m, c, l, round(100 * l / c, 3)) for m, c, l in MONTHS])
    rng = random.Random(2401)
    start = dt.date(2025, 11, 3)
    weeks = [start + dt.timedelta(days=7 * i) for i in range(52)]
    rows = []
    for m, cast, lost in MONTHS:
        wk = [d for d in weeks if d.strftime("%Y-%m") == m]
        casts = split(cast, len(wk), rng)
        if m == BAD_WEEK.strftime("%Y-%m"):
            i = wk.index(BAD_WEEK)
            bad = round(casts[i] * 0.036, 1)
            rest = split(lost - bad, len(wk) - 1, rng, 0.05)
            losts = rest[:i] + [bad] + rest[i:]
        else:
            losts = split(lost, len(wk), rng, 0.05)
        for d, c, l in zip(wk, casts, losts):
            rows.append((d.isoformat(), m, c, l, round(100 * l / c, 2)))
    write("weekly_loss_sheet.csv", ["week_start", "month", "cast_hL", "lost_hL", "loss_rate_pct"], rows)


def fill_records(seed=32):
    """Lager fills on the twelve 600 hL fermenters in six matched pairs, twelve months.

    Loss = 2.4 + a shared week effect + a tank effect. Single fills spread about 0.6 points;
    the gap inside a pair spreads about 0.4 (chapter 11.5)."""
    rng = random.Random(seed)
    rows, start = [], dt.date(2025, 11, 3)
    for pair in range(1, 7):
        tanks = (2 * pair - 1, 2 * pair)
        for cycle in range(12):
            day = start + dt.timedelta(days=30 * cycle + rng.randint(0, 4))
            shared = rng.gauss(0, 0.53)
            for t in tanks:
                loss = round(2.4 + shared + rng.gauss(0, 0.283), 2)
                cast = round(600 + rng.uniform(-6, 6), 1)
                out = round(cast * (1 - loss / 100), 1)
                fid = f"F{t:02d}-{day:%y}-{cycle + 1:03d}"
                rows.append((fid, f"FV{t:02d}", pair, cycle + 1, day.isoformat(), cast, out,
                             round(100 * (cast - out) / cast, 2)))
    write("fill_records.csv", ["fill_id", "tank", "pair", "cycle", "fill_start", "hL_into_fermenter",
                               "hL_at_filter_inlet", "loss_pct"], rows)


def pilot_gaps(seed=1105):
    """The chapter 12 pilot: six pairs, two fills a tank in each 60 day block.
    First look averages 0.41 points over 12 gaps; all 24 gaps average 0.44."""
    rng = random.Random(seed)
    rows = []
    for phase, cycles, target in (("first_look", (1, 2), 0.41), ("extension", (3, 4), 0.47)):
        gaps = [rng.gauss(0, 0.4) for _ in range(12)]
        shift = target - sum(gaps) / 12
        gaps = [round(g + shift, 2) for g in gaps]
        gaps[-1] = round(target * 12 - sum(gaps[:-1]), 2)
        k = 0
        for pair in range(1, 7):
            for cyc in cycles:
                control = round(2.4 + rng.gauss(0, 0.5), 2)
                rows.append((pair, cyc, phase, control, round(control - gaps[k], 2), gaps[k]))
                k += 1
    write("pilot_pair_gaps.csv", ["pair", "cycle", "phase", "control_loss_pct", "pilot_loss_pct",
                                  "gap_points"], rows)


def vendor_counts():
    """Anonymised counts from the author's review of public websites, 24 September 2026.
    Counts only: no vendor names, no rows that identify a vendor."""
    rows = [
        ("Beer AI vendors at shipping or pilot stage", 116),
        ("Sell to breweries", 95),
        ("Make a quantified claim", 50),
        ("Offer a calculator", 14),
        ("Explain any part of how savings are worked out", 23),
        ("Of those 23 also make a quantified claim", 20),
        ("Explain it properly (inputs shown with costs deducted plus a conservative case)", 3),
        ("Of those 3 also make a quantified claim", 2),
        ("Offer a guarantee or pilot or trial", 22),
        ("Tie the price to the result", 3),
        ("Publish a price", 13),
        ("Price on request", 49),
    ]
    write("vendor_counts.csv", ["measure", "count"], rows)


QUESTIONS = ["Baseline named and dated", "Formula shown", "Inputs are the buyer's own",
             "Fee deducted", "Conservative case", "Ramp up modelled",
             "Measured by someone else", "Price tied to result"]


def scores():
    """Chapter 4.4 claims A to C. The owner's points match the book; the head brewer differs."""
    owner = {"A": [0] * 8, "B": [1, 1, 0, 0, 0, 0, 0, 0], "C": [1, 1, 1, 1, 1, 1, 0, 0]}
    brewer = {"A": [0] * 8, "B": [1, 1, 1, 0, 0, 0, 1, 0], "C": [1, 1, 1, 1, 1, 0, 0, 0]}
    rows = []
    for scorer, table in (("owner", owner), ("head brewer", brewer)):
        for claim, pts in table.items():
            for i, pt in enumerate(pts):
                rows.append((claim, i + 1, QUESTIONS[i], scorer, pt, "call note or web address"))
    write("ch04_scores.csv", ["claim", "question", "text", "scorer", "point", "source"], rows)


RED = ["Percentage with no unit", "Up to", "Case study with no period", "Case study from another industry",
       "Potential presented as result", "Benchmark from our customers", "Price only after the demo",
       "No stated data need", "Trial that proves nothing", "AI powered and nothing else"]
GREEN = ["Open calculator", "Named dated baseline", "Separate count of what would have happened anyway",
         "Study that cuts its own benefits", "Money at risk"]


def first_call():
    """Two constructed vendors answered on the first call (chapter 6)."""
    v1 = ([1, 1, 1, 0, 1, 1, 1, 1, 0, 0], [0, 0, 0, 0, 1])
    v2 = ([0, 1, 0, 0, 0, 0, 1, 0, 0, 0], [1, 1, 0, 0, 1])
    rows = []
    for vendor, (red, green) in (("Vendor 1", v1), ("Vendor 2", v2)):
        rows += [(vendor, "red", f, x) for f, x in zip(RED, red)]
        rows += [(vendor, "green", f, x) for f, x in zip(GREEN, green)]
    write("ch06_first_call.csv", ["vendor", "flag_type", "flag", "present"], rows)


def ch05_templates():
    rng = random.Random(505)
    # Vision: 200 seeded bad packs plus a shift of good packs (chapter 5.1)
    defects = ["low fill", "lifted label", "missing crown", "skewed label", "foreign object"]
    catch = {"low fill": 0.98, "lifted label": 0.80, "missing crown": 0.99, "skewed label": 0.90,
             "foreign object": 0.85}
    rows = [(f"S{i + 1:03d}", "seeded bad", d, int(rng.random() < catch[d]))
            for i, d in enumerate(rng.choice(defects) for _ in range(200))]
    write("ch05_seeded_packs.csv", ["pack_id", "kind", "defect", "rejected"], rows)
    # Downtime: one month of filler stops from the line control system (chapter 5.2)
    rows, t = [], dt.datetime(2026, 9, 1, 6, 0)
    logged = [rng.uniform(600, 7200) for _ in range(40)]
    logged = [round(x * 40 * 3600 / sum(logged)) for x in logged]
    logged[-1] = 40 * 3600 - sum(logged[:-1])
    micro = [rng.randint(3, 30) for _ in range(4800)]
    micro = [max(1, round(x * 22 * 3600 / sum(micro))) for x in micro]
    micro[-1] = 22 * 3600 - sum(micro[:-1])
    stops = [(s, 1) for s in logged] + [(s, 0) for s in micro]
    rng.shuffle(stops)
    step = 30 * 24 * 3600 / len(stops)
    for i, (sec, op) in enumerate(stops):
        rows.append(((t + dt.timedelta(seconds=round(i * step))).isoformat(), sec, op))
    write("ch05_filler_stops.csv", ["stop_start", "duration_s", "logged_by_operator"], rows)
    # Copilot: a fifty question test set, scored by the shift leader (chapter 5.3)
    cats = ["malt certificate field", "SOP step", "spec limit", "fault code", "calculation"]
    rows = [(f"Q{i + 1:02d}", cats[i % 5], int(rng.random() < 0.88), int(rng.random() < 0.82))
            for i in range(50)]
    write("ch05_copilot_test_set.csv", ["question_id", "category", "cites_document", "correct"], rows)
    # Forecast: weekly lager dispatch with a held out final 26 weeks (chapter 5.4)
    rows, base = [], 1400
    for w in range(156):
        season = 1 + 0.25 * math.sin(2 * math.pi * (w - 13) / 52)
        actual = round(base * season * rng.gauss(1, 0.10))
        rows.append([w + 1, actual])
    for r in rows:
        w = r[0] - 1
        naive = rows[w - 52][1] if w >= 52 else ""
        season = 1 + 0.25 * math.sin(2 * math.pi * (w - 13) / 52)
        model = round(base * season * rng.gauss(1, 0.06)) if w >= 52 else ""
        r += [naive, model, "held_out" if w >= 130 else "train"]
    write("ch05_weekly_sales.csv", ["week", "actual_hL", "naive_same_week_last_year", "vendor_forecast",
                                    "period"], rows)


def inputs():
    write("kestrel_inputs.csv", ["cell", "item", "value"], INPUTS)


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    inputs()
    monthly_and_weekly()
    fill_records()
    pilot_gaps()
    vendor_counts()
    scores()
    first_call()
    ch05_templates()
    print("wrote", ", ".join(sorted(os.listdir(DATA))))
