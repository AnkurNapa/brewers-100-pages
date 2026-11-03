"""Shared helpers for the One Brewery, One Model companion.

The notebooks, pipeline.py and check_numbers.py import from here so that one rule
lives in one place. Every figure is Kestrel's and synthetic.
"""
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SQL = ROOT / "sql"
OUT = ROOT / "out"

# The 14 core tables and the ten reference and control tables of Appendix C (quarantine is built, not loaded)
CORE = ["item", "vessel", "calendar_day", "recipe_version", "spec", "brew", "batch", "vessel_event", "lot",
        "sample", "movement", "package_unit", "result", "brew_batch"]
REFERENCE = ["tag_reading", "equipment", "site", "xref", "unit_factor", "shift", "tag_map", "precedence",
             "kpi_dictionary"]
WATER_KG_PER_L = 0.9982  # density of water at 20 degrees C


def load(name):
    """Read one CSV from data/. An SSCC is a code, not a number, so it keeps its leading zeros."""
    return pd.read_csv(DATA / f"{name}.csv", dtype={"sscc": str, "order_ref": str, "item_code": str})


def connect(path=":memory:"):
    """A SQLite database holding every Appendix C table from data/ plus the node and edge views."""
    con = sqlite3.connect(path)
    for name in CORE + REFERENCE:
        load(name).to_sql(name, con, index=False, if_exists="replace")
    con.executescript((SQL / "views.sql").read_text())
    return con


def q(con, sql, params=()):
    return pd.read_sql_query(sql, con, params=params)


# ---------------------------------------------------------------- gravity and extract (chapters 3 and 10)
def sg_from_plato(p):
    """Specific gravity from degrees Plato by the MBAA polynomial, unrounded (chapter 7.2).
    At 12.0 degrees Plato it gives 1.04838; the book prints 1.0484."""
    return 1 + p / (258.6 - (p / 258.2) * 227.1)


def extract_kg(volume_hl, plato):
    """Extract in a volume of wort: litres x SG x water density x Plato / 100."""
    return volume_hl * 100 * sg_from_plato(plato) * WATER_KG_PER_L * plato / 100


def theoretical_extract(con):
    """Extract the grist could give, per brew, from each malt lot's certificate (chapter 10.3)."""
    coa = load("bronze_supplier_coa")
    malt = q(con, """
        SELECT b.brew_id, l.lot_id, m.quantity AS kg
        FROM movement m JOIN brew b ON b.brew_key = m.to_node_key AND m.to_node_type = 'brew'
        JOIN lot l ON l.lot_key = m.from_node_key AND m.from_node_type = 'lot'
        WHERE l.lot_type = 'malt'""").merge(coa, on="lot_id")
    malt["extract_kg"] = malt.kg * (malt.fine_grind_extract_pct - malt.fine_coarse_diff_pct) / 100 * \
        (1 - malt.moisture_pct / 100)
    return malt.groupby("brew_id").extract_kg.sum()


def gravity_sources(con):
    """Cast gravity per brew from the three sources: lab result, inline meter and brew sheet (chapter 3)."""
    # a cast wort sample belongs to the latest brew cast into its fill before it was pulled
    lab = q(con, """
        SELECT s.sample_id, r.value AS lab, s.sampled_at_utc,
               (SELECT b.brew_id FROM movement m JOIN brew b ON b.brew_key = m.from_node_key
                WHERE m.movement_type = 'produce' AND m.to_node_key = s.batch_key
                  AND m.posted_utc <= s.sampled_at_utc
                ORDER BY m.posted_utc DESC LIMIT 1) AS brew_id
        FROM sample s JOIN result r ON r.sample_key = s.sample_key
        WHERE r.test_code = 'OG' AND r.is_current = 1""")
    meter = q(con, """
        SELECT b.brew_id, AVG(t.value) AS inline_meter
        FROM movement m JOIN brew b ON b.brew_key = m.from_node_key
        JOIN tag_reading t ON t.tag = 'BRH.WL01.DT01.PV'
          AND t.reading_utc >= m.posted_utc AND t.reading_utc < datetime(m.posted_utc, '+55 minutes')
        WHERE m.movement_type = 'produce' AND t.quality_flag = 'good'
        GROUP BY b.brew_id""")
    sheet = load("bronze_brewsheet_brew")[["brew_id", "gravity_plato"]].rename(
        columns={"gravity_plato": "brew_sheet"})
    out = lab[["brew_id", "sample_id", "lab"]].merge(meter, on="brew_id").merge(sheet, on="brew_id")
    out["gap"] = (out.inline_meter - out.lab).round(2)
    return out


def gravity_of_record(con, sources=None):
    """Apply the signed precedence table: rank 1 wins; a missing rank 1 falls to rank 2 with a flag."""
    sources = gravity_sources(con) if sources is None else sources
    prec = q(con, "SELECT source, rank FROM precedence WHERE measurement_code = 'WORT_GRAVITY' "
                  "AND valid_to IS NULL ORDER BY rank")
    picked = []
    for _, row in sources.iterrows():
        for i, src in enumerate(prec.source):
            if pd.notna(row[src]):
                picked.append((row.brew_id, row[src], src, i > 0))
                break
    return pd.DataFrame(picked, columns=["brew_id", "plato", "source", "fallback_flag"])


# ---------------------------------------------------------------- events from tags (chapter 4.4)
FILL_RISE_HL, RISE_WINDOW_MIN, HOLD_MIN, HOLD_TOL_HL = 5, 10, 3, 0.5
CIP_CONDUCTIVITY = 20


def wide_trace(readings, vessel="FV07"):
    """One row per minute, one column per signal, for one fermenter."""
    names = {f"CEL.{vessel}.LT01.PV": "level", f"CEL.{vessel}.TT01.PV": "temp", f"CEL.{vessel}.XV01.PV": "inlet",
             f"CEL.{vessel}.XV02.PV": "outlet", f"CEL.{vessel}.CT01.PV": "cond"}
    r = readings[readings.tag.isin(names)].copy()
    r["t"] = pd.to_datetime(r.reading_utc)
    return r.pivot_table(index="t", columns="tag", values="value").rename(columns=names)


def _segments(mask):
    """Runs of consecutive minutes where mask is true, as (first, last) timestamps."""
    times = mask[mask].index
    if len(times) == 0:
        return []
    breaks = np.where(np.diff(times.values) != np.timedelta64(1, "m"))[0]
    starts = [times[0]] + [times[i + 1] for i in breaks]
    ends = [times[i] for i in breaks] + [times[-1]]
    return list(zip(starts, ends))


def detect_events(w, vessel="FV07"):
    """Kestrel's working rule: a fill starts when the inlet is open and the level rises by at least
    5 hL in 10 minutes; it ends when the valve closes and the level holds for 3 minutes.
    A transfer is the mirror on the outlet. A CIP is a conductivity jump."""
    events = []
    minute = pd.Timedelta(minutes=1)
    for etype, valve, sign in [("fill", "inlet", 1), ("transfer out", "outlet", -1)]:
        for first, last in _segments(w[valve] == 1):
            seg = w.loc[first:last]
            ahead = w.level.reindex(seg.index + RISE_WINDOW_MIN * minute).values
            moving = seg.index[sign * (ahead - seg.level.values) >= FILL_RISE_HL]
            if len(moving) == 0:
                continue
            start = moving[0]
            end = last
            after = w.loc[last + minute:last + 60 * minute, "level"]
            for t in after.index:
                window = after.loc[t:t + (HOLD_MIN - 1) * minute]
                if len(window) == HOLD_MIN and window.max() - window.min() < HOLD_TOL_HL:
                    end = t
                    break
            events.append(dict(vessel=vessel, event_type=etype, start_utc=start, end_utc=end,
                               volume_hl=round(abs(w.level[end] - w.level[start]), 1),
                               rule_version=f"{etype.split()[0]}-v1"))
    for first, last in _segments(w.cond > CIP_CONDUCTIVITY):
        events.append(dict(vessel=vessel, event_type="CIP", start_utc=first, end_utc=last, volume_hl=None,
                           rule_version="cip-v1"))
    return pd.DataFrame(events).sort_values("start_utc").reset_index(drop=True)


def match_events(events):
    """Match detected events to the brew sheet (fills) and the transfer log (transfers) by vessel and time.
    A CIP has no batch. Anything else unmatched goes to a person, never to a guess."""
    ist = pd.Timedelta(hours=5, minutes=30)
    tol = pd.Timedelta(minutes=15)
    sheet = load("bronze_brewsheet_brew")
    sheet["vessel"] = "FV" + sheet.fill_id.str[1:3]
    start = pd.to_datetime(sheet.brew_date_ist + " " + sheet.start_ist)
    end = pd.to_datetime(sheet.brew_date_ist + " " + sheet.end_ist)
    sheet["end_utc"] = end.where(end > start, end + pd.Timedelta(days=1)) - ist
    log = load("bronze_transferlog_transfer")
    log["start_utc"] = pd.to_datetime(log.start_ist) - ist
    batch = load("batch")  # a transfer belongs to the fill open in that vessel when it started
    out = []
    for _, e in events.iterrows():
        match, ref = None, None
        if e.event_type == "fill":
            hit = sheet[(sheet.vessel == e.vessel) & ((sheet.end_utc - e.end_utc).abs() <= tol)]
            if len(hit):
                match, ref = hit.fill_id.iloc[0], hit.brew_id.iloc[0]
        elif e.event_type == "transfer out":
            hit = log[(log.from_vessel == e.vessel) & ((log.start_utc - e.start_utc).abs() <= tol)]
            if len(hit):
                ref = hit.transfer_id.iloc[0]
                open_fill = batch[(pd.to_datetime(batch.fill_start_utc) <= e.start_utc) &
                                  (pd.to_datetime(batch.empty_utc) >= e.start_utc)]
                match = open_fill.batch_id.iloc[0] if len(open_fill) else None
        else:
            ref = "no batch (CIP)"
        out.append(dict(e, batch_id=match, matched_to=ref))
    return pd.DataFrame(out)


# ---------------------------------------------------------------- lineage (chapter 9)
def trace_loop(edges, start, cap=12, backward=False):
    """The notebook form of the lineage query: one level per pass, like the T-SQL WHILE loop.
    Returns the summed share for every node reached."""
    a, b = ("to_node", "from_node") if backward else ("from_node", "to_node")
    path = edges.loc[edges[a] == start, [b, "share"]].rename(columns={b: "node"})
    path["depth"] = 1
    d = 1
    while d < cap:
        newest = path[path.depth == d]
        nxt = newest.merge(edges, left_on="node", right_on=a)
        if nxt.empty:
            break
        nxt = pd.DataFrame({"node": nxt[b], "share": nxt.share_x * nxt.share_y, "depth": d + 1})
        path = pd.concat([path, nxt], ignore_index=True)
        d += 1
    return path


def trace(edges, start, cap=12, backward=False):
    return trace_loop(edges, start, cap, backward).groupby("node").share.sum()


# ---------------------------------------------------------------- data quality (chapter 12)
SAMPLE_ID = re.compile(r"^S\d{6}-\d{3}$")
OWNERS = {"completeness": "QA lead", "range": "QA lead", "join": "Data steward", "freshness": "Data steward",
          "balance": "Plant manager"}


def run_checks(con):
    """Kestrel's five checks. Returns the quarantine table: row_ref, check_failed, reason_code, date, owner."""
    rows = []

    def fail(ref, check, reason, date):
        rows.append(dict(row_ref=ref, check_failed=check, reason_code=reason, date=str(date)[:10],
                         owner=OWNERS[check]))

    # 1 completeness: every fill has its apparent extract before transfer
    done = q(con, """
        SELECT b.batch_id, e.start_utc,
               (SELECT COUNT(*) FROM sample s JOIN result r ON r.sample_key = s.sample_key
                WHERE s.batch_key = b.batch_key AND r.test_code = 'AE' AND r.is_current = 1
                  AND s.sampled_at_utc < e.start_utc) AS ae_results
        FROM batch b JOIN vessel_event e ON e.batch_key = b.batch_key AND e.event_type = 'transfer out'""")
    for _, r in done[done.ae_results == 0].iterrows():
        fail(f"batch:{r.batch_id}", "completeness", "NO_AE_BEFORE_TRANSFER", r.start_utc)
    # 2 range: cast gravity inside the recipe band; meter 0.0 to 0.2 above the lab
    src = gravity_sources(con)
    rec = q(con, "SELECT b.brew_id, b.mash_in_utc, r.og_plato FROM brew b "
                 "JOIN recipe_version r USING (recipe_version_key)")
    src = src.merge(rec, on="brew_id")
    for _, r in src.iterrows():
        if abs(r.lab - r.og_plato) > 1.0:
            fail(f"result:{r.sample_id}:OG", "range", "CAST_GRAVITY_OUT_OF_BAND", r.mash_in_utc)
        if not (-1e-9 <= r.gap <= 0.2 + 1e-9):
            fail(f"tag:BRH.WL01.DT01.PV:{r.brew_id}", "range", "METER_LAB_GAP", r.mash_in_utc)
    # 3 join: pack lot to fill, ID patterns, orphan samples
    orphan_lots = q(con, """
        SELECT l.lot_id, l.created_utc FROM lot l WHERE l.lot_type = 'pack' AND NOT EXISTS (
          SELECT 1 FROM movement p JOIN movement t ON t.to_node_type = 'lot' AND t.to_node_key = p.from_node_key
          WHERE p.to_node_type = 'pack_lot' AND p.to_node_key = l.lot_key AND t.from_node_type = 'batch')""")
    for _, r in orphan_lots.iterrows():
        fail(f"lot:{r.lot_id}", "join", "PACK_LOT_WITHOUT_FILL", r.created_utc)
    samples = q(con, "SELECT sample_id, batch_key, sampled_at_utc FROM sample")
    for _, r in samples.iterrows():
        if not SAMPLE_ID.match(r.sample_id):
            fail(f"sample:{r.sample_id}", "join", "BAD_ID_PATTERN", r.sampled_at_utc)
        if pd.isna(r.batch_key):
            fail(f"sample:{r.sample_id}", "join", "NO_EVENT", r.sampled_at_utc)
    # 4 freshness: no cellar tag silent more than 5 minutes; lab results entered within 24 hours
    tags = q(con, "SELECT tag, reading_utc FROM tag_reading WHERE tag LIKE 'CEL.%'")
    tags["t"] = pd.to_datetime(tags.reading_utc)
    tags["day"] = tags.t.dt.date
    tags = tags.sort_values(["tag", "t"])
    tags["silent_min"] = tags.groupby(["tag", "day"]).t.diff().dt.total_seconds() / 60
    for _, r in tags[tags.silent_min > 5].iterrows():
        fail(f"tag:{r.tag}:{r.reading_utc}", "freshness", "TAG_SILENT", r.reading_utc)
    late = q(con, """
        SELECT s.sample_id, r.test_code, r.sampled_at_utc FROM result r JOIN sample s USING (sample_key)
        WHERE (julianday(r.entered_at_utc) - julianday(r.sampled_at_utc)) * 24 > 24""")
    for _, r in late.iterrows():
        fail(f"result:{r.sample_id}:{r.test_code}", "freshness", "LATE_ENTRY", r.sampled_at_utc)
    # 5 balance: the month closes within 0.5 percent of wort cast
    for _, m in month_balance().iterrows():
        if m.closure_gap_pct >= 0.5:
            fail(f"month:{m.month}", "balance", "CLOSURE_GAP", m.month + "-01")
    return pd.DataFrame(rows, columns=["row_ref", "check_failed", "reason_code", "date", "owner"])


# ---------------------------------------------------------------- mass balance (chapter 10)
def month_balance():
    m = load("vessel_event_month")
    m["known_loss_hl"] = m.cellar_loss_hl + m.filtration_loss_hl + m.packaging_loss_hl
    m["change_in_stock_hl"] = (m.closing_tank_hl - m.opening_tank_hl).round(1)
    m["closure_gap_hl"] = (m.cast_hl - m.dispatched_hl - m.known_loss_hl - m.change_in_stock_hl).round(1)
    m["closure_gap_pct"] = (100 * m.closure_gap_hl / m.cast_hl).round(2)
    return m


def stage_table(month):
    """In, known loss and out for each stage of one month."""
    m = month_balance().set_index("month").loc[month]
    cellar_out = m.cast_hl - m.cellar_loss_hl
    filt_out = cellar_out - m.filtration_loss_hl
    packed = filt_out - m.packaging_loss_hl
    return pd.DataFrame([
        ("Cellar", m.cast_hl, m.cellar_loss_hl, cellar_out),
        ("Filtration and bright beer tanks", cellar_out, m.filtration_loss_hl, filt_out),
        ("Packaging", filt_out, m.packaging_loss_hl, packed),
        ("Dispatched", packed, None, m.dispatched_hl),
    ], columns=["stage", "in_hl", "known_loss_hl", "out_hl"])


# ---------------------------------------------------------------- KPI tables (chapter 13.4)
def kpi_tables(con, version="1.0"):
    """Numerator and denominator at each grain. Ratios are never stored."""
    out = {}
    rec = q(con, "SELECT b.brew_key, b.brew_id, b.wort_cast_hl, b.grist_kg, r.og_plato, r.cast_hl AS recipe_hl "
                 "FROM brew b JOIN recipe_version r USING (recipe_version_key)")
    grav = gravity_of_record(con).set_index("brew_id").plato
    theo = theoretical_extract(con)
    rows = []
    for _, b in rec.iterrows():
        p = grav[b.brew_id]
        rows += [(b.brew_key, "Extract efficiency", extract_kg(b.wort_cast_hl, p), theo[b.brew_id]),
                 (b.brew_key, "Wort volume yield", b.wort_cast_hl * 100, b.grist_kg),
                 (b.brew_key, "Cast gravity deviation", p - b.og_plato, 1),
                 (b.brew_key, "Cast volume variance", b.wort_cast_hl - b.recipe_hl, b.recipe_hl)]
    out["kpi_brew"] = pd.DataFrame(rows, columns=["brew_key", "kpi_name", "numerator", "denominator"])

    fills = q(con, """
        SELECT b.batch_key,
          (SELECT SUM(volume_hl) FROM vessel_event e WHERE e.batch_key = b.batch_key AND e.event_type = 'fill') AS cast,
          (SELECT volume_hl FROM vessel_event e WHERE e.batch_key = b.batch_key AND e.event_type = 'transfer out')
            AS sent,
          (SELECT volume_hl FROM vessel_event e WHERE e.batch_key = b.batch_key AND e.event_type = 'bright fill')
            AS bright
        FROM batch b""")
    og = q(con, """
        SELECT bb.batch_key, bb.share, b.brew_id FROM brew_batch bb JOIN brew b USING (brew_key)""")
    og["og"] = og.brew_id.map(grav)
    og = (og.og * og.share).groupby(og.batch_key).sum()
    ae = q(con, """
        SELECT s.batch_key, r.value FROM result r JOIN sample s USING (sample_key)
        WHERE r.test_code = 'AE' AND r.is_current = 1 ORDER BY s.sampled_at_utc""").groupby("batch_key").value.last()
    rows = []
    for _, f in fills.iterrows():
        rows.append((f.batch_key, "Cellar loss", f.cast - f.sent, f.cast))
        if f.batch_key in ae.index:
            rows.append((f.batch_key, "Apparent attenuation", og[f.batch_key] - ae[f.batch_key], og[f.batch_key]))
    out["kpi_fill"] = pd.DataFrame(rows, columns=["batch_key", "kpi_name", "numerator", "denominator"])

    bright = q(con, """
        SELECT l.lot_key AS bright_fill_key, m.from_node_key AS batch_key FROM lot l
        JOIN movement m ON m.to_node_type = 'lot' AND m.to_node_key = l.lot_key AND m.from_node_type = 'batch'
        WHERE l.lot_type = 'bright_fill'""").merge(fills, on="batch_key")
    out["kpi_bright_fill"] = pd.DataFrame(
        [(r.bright_fill_key, "Filtration and bright tank loss", r.sent - r.bright, r.cast) for _, r in bright.iterrows()],
        columns=["bright_fill_key", "kpi_name", "numerator", "denominator"])

    shifts = load("bronze_linectl_shift")
    checks = load("bronze_linectl_fill_check")
    checks["over_ml"] = checks.measured_ml - checks.declared_ml
    lots = q(con, "SELECT lot_key AS pack_lot_key, lot_id FROM lot WHERE lot_type = 'pack'")
    rows = []
    for _, lt in lots.iterrows():
        s = shifts[shifts.pack_lot_id == lt.lot_id]
        c = checks[checks.pack_lot_id == lt.lot_id]
        filled, rejected = s.packs_filled.sum(), s.packs_rejected.sum()
        good = filled - rejected
        lost_l = rejected * 0.33 + good * c.over_ml.mean() / 1000 + s.flush_l.sum()
        rows += [(lt.pack_lot_key, "Beer loss per hL packed", lost_l, good * 0.0033),
                 (lt.pack_lot_key, "Reject rate", rejected, filled),
                 (lt.pack_lot_key, "Fill giveaway", c.over_ml.sum(), len(c))]
    out["kpi_pack_lot"] = pd.DataFrame(rows, columns=["pack_lot_key", "kpi_name", "numerator", "denominator"])

    eq = q(con, "SELECT equipment_key, equipment_code FROM equipment")
    s = shifts.merge(eq, on="equipment_code")
    rows = []
    for _, r in s.iterrows():
        rated = r.run_min / 60 * r.rated_per_hour
        key = (r.equipment_key, r.shift_date, r.shift_name)
        rows += [key + ("OEE availability", r.run_min, r.planned_min),
                 key + ("OEE performance", r.packs_filled, rated),
                 key + ("OEE quality", r.packs_filled - r.packs_rejected, r.packs_filled),
                 key + ("Line speed loss", rated - r.packs_filled, rated)]
    out["kpi_line_shift"] = pd.DataFrame(rows, columns=["equipment_key", "shift_date", "shift_name", "kpi_name",
                                                        "numerator", "denominator"])
    for df in out.values():
        key = df.columns[0]
        df[key] = df[key].astype(int)
        df["dictionary_version"] = version
    return out


def lineage_path(con, cap=12):
    """One row per start node, node reached and depth, for every input lot (chapter 13.4)."""
    edges = q(con, "SELECT * FROM edge")
    starts = q(con, "SELECT lot_id FROM lot WHERE lot_type NOT IN ('pack', 'bright_fill')").lot_id
    parts = []
    for s in starts:
        p = trace_loop(edges, s, cap)
        if len(p):
            p = p.groupby(["node", "depth"], as_index=False).share.sum()
            p.insert(0, "start_node", s)
            parts.append(p)
    return pd.concat(parts, ignore_index=True)[["start_node", "node", "share", "depth"]]


def source_comparison(con):
    """One row per lab sample and other source: the meter and lab pair behind the gap check (chapter 3)."""
    g = gravity_sources(con)
    keys = q(con, "SELECT sample_key, sample_id FROM sample")
    g = g.merge(keys, on="sample_id")
    return pd.DataFrame({"sample_key": g.sample_key, "measurement": "WORT_GRAVITY", "lab_value": g.lab,
                         "meter_value": g.inline_meter, "gap": g.gap})
