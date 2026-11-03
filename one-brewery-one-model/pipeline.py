"""The companion pipeline: land the Kestrel slice in bronze, conform it in silver, publish gold.

Run: python3 pipeline.py
It builds out/kestrel.db twice from a clean start and proves the second run changes no rows
(chapter 13.5). SQLite stands in for the lakehouse and the warehouse; the layer rules are the same.
"""
import hashlib
import sqlite3
from datetime import datetime, timezone

import pandas as pd

import kestrel as k

DB = k.OUT / "kestrel.db"

GOLD_KEYS = {
    "item": ["item_key"], "vessel": ["vessel_key"], "calendar_day": ["date"],
    "recipe_version": ["recipe_version_key"], "spec": ["spec_key"], "brew": ["brew_key"], "batch": ["batch_key"],
    "vessel_event": ["event_key"], "lot": ["lot_key"], "sample": ["sample_key"], "movement": ["movement_key"],
    "package_unit": ["package_unit_key"], "result": ["result_key"], "brew_batch": ["brew_key", "batch_key"],
    "tag_reading": ["tag", "reading_utc"], "equipment": ["equipment_key"], "site": ["site_key"],
    "xref": ["source_system", "source_key", "valid_from"], "unit_factor": ["from_unit"], "shift": ["shift_name"],
    "tag_map": ["tag", "valid_from"], "precedence": ["measurement_code", "source", "valid_from"],
    "kpi_dictionary": ["name", "version"],
}


def upsert(con, table, df, keys):
    """Merge on the natural key. A row is written only when it is new or one of its values changed,
    so running the same window twice writes nothing."""
    df = df.astype(object).where(pd.notna(df), None)
    cols = list(df.columns)
    quoted = ", ".join(f'"{c}"' for c in cols)
    con.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({quoted}, PRIMARY KEY ({", ".join(keys)}))')
    others = [c for c in cols if c not in keys]
    if others:
        sets = ", ".join(f'"{c}" = excluded."{c}"' for c in others)
        diff = " OR ".join(f'"{table}"."{c}" IS NOT excluded."{c}"' for c in others)
        tail = f"DO UPDATE SET {sets} WHERE {diff}"
    else:
        tail = "DO NOTHING"
    con.executemany(f'INSERT INTO "{table}" ({quoted}) VALUES ({", ".join("?" * len(cols))}) '
                    f'ON CONFLICT ({", ".join(keys)}) {tail}',
                    [tuple(str(v) if isinstance(v, pd.Timestamp) else v for v in row) for row in df.values])


def bronze(con):
    """Append only. Each file lands once, with four added columns; a file already landed is skipped."""
    con.execute("CREATE TABLE IF NOT EXISTS load_log (source_file TEXT, file_hash TEXT, load_run_id INTEGER, "
                "extracted_utc TEXT, PRIMARY KEY (source_file, file_hash))")
    run_id = con.execute("SELECT COALESCE(MAX(load_run_id), 0) + 1 FROM load_log").fetchone()[0]
    landed = 0
    for path in sorted(k.DATA.glob("*.csv")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if con.execute("SELECT 1 FROM load_log WHERE source_file = ? AND file_hash = ?",
                       (path.name, digest)).fetchone():
            continue
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        df = k.load(path.stem)
        name = path.stem if path.stem.startswith("bronze_") else f"bronze_extract_{path.stem}"
        source = name.split("_")[1]
        df = df.assign(_source_system=source, _extracted_utc=now, _source_file=path.name, _load_run_id=run_id)
        df.to_sql(name, con, index=False, if_exists="append")
        con.execute("INSERT INTO load_log VALUES (?, ?, ?, ?)", (path.name, digest, run_id, now))
        landed += 1
    return landed


def from_bronze(con, name):
    """The latest landing of one bronze table, without the four load columns."""
    df = pd.read_sql_query(f'SELECT * FROM "{name}" WHERE _load_run_id = (SELECT MAX(_load_run_id) FROM "{name}")',
                           con)
    return df.drop(columns=[c for c in df.columns if c.startswith("_")])


def silver(con):
    tags = from_bronze(con, "bronze_extract_tag_reading")
    tmap = from_bronze(con, "bronze_extract_tag_map")
    tmap = tmap[tmap.valid_to.isna()][["tag", "vessel", "measurement", "unit"]]
    upsert(con, "silver_tag_reading", tags.merge(tmap, on="tag", how="left"), ["tag", "reading_utc"])

    events = k.match_events(k.detect_events(k.wide_trace(tags)))
    upsert(con, "silver_vessel_event", events, ["vessel", "event_type", "start_utc"])

    res = from_bronze(con, "bronze_extract_result")
    smp = from_bronze(con, "bronze_extract_sample")[["sample_key", "sample_id", "vessel_key", "batch_key",
                                                      "match_method"]]
    upsert(con, "silver_sample_result", res.merge(smp, on="sample_key"), ["result_key"])

    gm = from_bronze(con, "bronze_erp_goods_movement")
    xr = from_bronze(con, "bronze_extract_xref")
    xr = xr[(xr.source_system == "erp") & (xr.entity == "item")][["source_key", "surrogate_key"]]
    gm = gm.merge(xr.rename(columns={"source_key": "item_code", "surrogate_key": "item_key"}), on="item_code",
                  how="left")
    upsert(con, "silver_goods_movement", gm, ["doc_no"])

    upsert(con, "silver_order_phase", from_bronze(con, "bronze_brewsheet_brew"), ["brew_id"])
    xi = from_bronze(con, "bronze_extract_xref")
    upsert(con, "silver_xref_item", xi[xi.entity == "item"], ["source_system", "source_key", "valid_from"])
    upsert(con, "silver_precedence", from_bronze(con, "bronze_extract_precedence"),
           ["measurement_code", "source", "valid_from"])
    return events, gm


def gold(con, events, gm):
    for table, keys in GOLD_KEYS.items():
        upsert(con, table, from_bronze(con, f"bronze_extract_{table}"), keys)
    con.executescript((k.SQL / "views.sql").read_text())
    upsert(con, "lineage_path", k.lineage_path(con), ["start_node", "node", "depth"])
    upsert(con, "source_comparison", k.source_comparison(con), ["sample_key", "measurement"])
    for name, df in k.kpi_tables(con).items():
        upsert(con, name, df, list(df.columns[: (3 if name == "kpi_line_shift" else 1)]) + ["kpi_name"])
    q = k.run_checks(con)
    extra = [dict(row_ref=f"event:{e.vessel}:{e.event_type}:{e.start_utc}", check_failed="join",
                  reason_code="NO_MATCH", date=str(e.start_utc)[:10], owner="Head brewer")
             for _, e in events[events.matched_to.isna()].iterrows()]
    extra += [dict(row_ref=f"erp:{g.doc_no}:{g.item_code}", check_failed="join", reason_code="NO_XREF",
                   date=g.posted_date, owner="Data steward") for _, g in gm[gm.item_key.isna()].iterrows()]
    q = pd.concat([q, pd.DataFrame(extra)], ignore_index=True)
    upsert(con, "silver_quarantine", q, ["row_ref", "check_failed"])
    upsert(con, "quarantine", q, ["row_ref", "check_failed"])


def fingerprint(con):
    """Row count and a hash of the sorted rows of every silver and gold table."""
    out = {}
    names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table' "
                                       "AND name NOT LIKE 'bronze_%' AND name <> 'load_log' ORDER BY name")]
    for n in names:
        rows = sorted(map(repr, con.execute(f'SELECT * FROM "{n}"').fetchall()))
        out[n] = (len(rows), hashlib.sha256("\n".join(rows).encode()).hexdigest()[:12])
    return out


def run(db=DB):
    """One chained run: bronze, then silver, then gold. Returns rows landed and rows changed."""
    con = sqlite3.connect(db)
    before = con.total_changes
    landed = bronze(con)
    after_bronze = con.total_changes
    events, gm = silver(con)
    gold(con, events, gm)
    con.commit()
    changed = con.total_changes - after_bronze
    prints = fingerprint(con)
    con.close()
    return dict(files_landed=landed, bronze_rows=after_bronze - before, silver_gold_rows_changed=changed,
                fingerprint=prints)


if __name__ == "__main__":
    k.OUT.mkdir(exist_ok=True)
    if DB.exists():
        DB.unlink()
    first = run()
    second = run()
    print(f"run 1: {first['files_landed']} files landed, {first['bronze_rows']} bronze rows, "
          f"{first['silver_gold_rows_changed']} silver and gold rows written")
    print(f"run 2: {second['files_landed']} files landed, {second['bronze_rows']} bronze rows, "
          f"{second['silver_gold_rows_changed']} silver and gold rows written")
    assert second["files_landed"] == 0 and second["bronze_rows"] == 0
    assert second["silver_gold_rows_changed"] == 0
    assert first["fingerprint"] == second["fingerprint"]
    print(f"second run changed no rows across {len(second['fingerprint'])} silver and gold tables")
