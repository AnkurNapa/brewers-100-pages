"""Assert that every number the book prints from the Kestrel slice comes out of data/.

Run after make_data.py: python3 check_numbers.py
Each check states the chapter, the number as printed and the precision it is printed to.
"""
import pandas as pd

import kestrel as k

con = k.connect()
checks = []


def check(where, got, printed, places):
    ok = round(float(got), places) == round(float(printed), places)
    checks.append((where, round(float(got), places + 2), printed, ok))


def pct(n, d):
    return 100 * n / d


brew = k.load("brew").set_index("brew_id")
batch = k.load("batch").set_index("batch_id")
edges = k.q(con, "SELECT * FROM edge")
months = k.month_balance().set_index("month")
march = months.loc["2026-03"]
grav = k.gravity_sources(con).set_index("brew_id")
theory = k.theoretical_extract(con)

# chapter 2: six brews, three fills, four pack lots; 23 pallets from the first two runs of F07-26-034
check("2.2 brews", len(brew), 6, 0)
check("2.2 fills", len(batch), 3, 0)
pack = k.q(con, "SELECT lot_id FROM lot WHERE lot_type = 'pack'")
check("2.2 pack lots", len(pack), 4, 0)
pallets = k.q(con, "SELECT l.lot_id, COUNT(*) n, SUM(p.volume_hl) hl FROM package_unit p "
                   "JOIN lot l ON l.lot_key = p.pack_lot_key GROUP BY l.lot_id").set_index("lot_id")
check("2.4 can pallets L260412-C1-1", pallets.n["L260412-C1-1"], 14, 0)
check("2.4 bottle pallets L260413-B1-1", pallets.n["L260413-B1-1"], 9, 0)
check("2.4 can pallet hL", 3600 * 0.0033, 11.88, 2)
check("2.4 bottle pallet hL", 1920 * 0.0033, 6.34, 2)
check("2.3 malt a year t", brew.grist_kg["B26-0068"] * 350 / 1000, 1855, 0)

# chapter 3: three gravity sources on B26-0068 and the efficiency each gives
check("3.1 meter B26-0068", grav.inline_meter["B26-0068"], 12.3, 1)
check("3.1 lab B26-0068", grav.lab["B26-0068"], 12.0, 1)
check("3.1 brew sheet B26-0068", grav.brew_sheet["B26-0068"], 12.0, 1)
check("3.3 gap", grav.gap["B26-0068"], 0.3, 1)
check("3.3 SG lab", k.sg_from_plato(12.0), 1.04838, 5)
check("3.3 SG meter", k.sg_from_plato(12.3), 1.04964, 5)
check("3.3 extract lab kg", k.extract_kg(300, 12.0), 3767, 0)
check("3.3 extract meter kg", k.extract_kg(300, 12.3), 3866, 0)
check("3.3 extract gap kg", k.extract_kg(300, 12.3) - k.extract_kg(300, 12.0), 99, 0)
check("3.3 theoretical extract kg", theory["B26-0068"], 4070, 0)
check("3.3 efficiency meter", pct(k.extract_kg(300, 12.3), theory["B26-0068"]), 95.0, 1)
check("3.3 efficiency lab", pct(k.extract_kg(300, 12.0), theory["B26-0068"]), 92.6, 1)
lab_sample = k.q(con, "SELECT r.sampled_at_utc, r.entered_at_utc FROM result r JOIN sample s USING (sample_key) "
                      "WHERE s.sample_id = ? AND r.test_code = 'OG'", (grav.sample_id["B26-0068"],)).iloc[0]
latency = pd.Timestamp(lab_sample.entered_at_utc) - pd.Timestamp(lab_sample.sampled_at_utc)
check("3.4 latency minutes (8 h 40)", latency.total_seconds() / 60, 520, 0)
sampled_ist = pd.Timestamp(lab_sample.sampled_at_utc) + pd.Timedelta(hours=5, minutes=30)
check("3.4 sampled 07:00 IST", sampled_ist.hour * 60 + sampled_ist.minute, 7 * 60, 0)
second_fill = k.q(con, "SELECT start_utc FROM vessel_event WHERE event_type = 'fill' AND batch_key = 1 "
                       "ORDER BY start_utc").start_utc[1]
t = pd.Timestamp(second_fill) + pd.Timedelta(hours=5, minutes=30)
check("3.4 second brew fills 13:00 IST", t.hour * 60 + t.minute, 13 * 60, 0)
check("3.5 cellar loss hL", march.cellar_loss_hl, 209, 0)

# chapter 4: two fill steps on FV07 and one unmatched event
events = k.match_events(k.detect_events(k.wide_trace(k.load("tag_reading"))))
check("4.4 fill events on FV07", (events.event_type == "fill").sum(), 2, 0)
check("4.4 fill events belong to F07-26-034", (events[events.event_type == "fill"].batch_id == "F07-26-034").sum(),
      2, 0)
check("4.4 unmatched events", events.matched_to.isna().sum(), 1, 0)

# chapter 6: B26-0068 movements, the can run and its cost
check("6.4 malt to B26-0068 kg", edges[(edges.from_node == "M-26-0087") & (edges.to_node == "B26-0068")].quantity.sum(),
      5300, 0)
check("6.4 B26-0068 to F07-26-034 hL", edges[(edges.from_node == "B26-0068")].quantity.sum(), 300, 0)
run = edges[edges.to_node == "L260412-C1-1"]
check("6.4 bright beer to L260412-C1-1 hL", run[run.unit == "hL"].quantity.sum(), 166.32, 2)
check("6.4 cans to L260412-C1-1", run[run.unit == "each"].quantity.sum(), 50400, 0)
check("6.4 can cost USD", 50400 * 0.14, 7056, 0)
check("6.4 can cost a hL", 50400 * 0.14 / 166.32, 42.4, 1)
check("6.2 malt per hL wort USD", brew.grist_kg["B26-0068"] * 0.90 / 300, 15.90, 2)
check("6.3 cast per brew, yearly average", months.cast_hl.sum() / months.brews.sum(), 298.6, 1)

# chapter 7: units and the brew day
check("7.4 bags of 50 kg", 5300 / 50, 106, 0)
check("7.2 cans in one hL", 100 / 0.33, 303.03, 2)

# chapter 8: shares in the bridge, tank days for one lager fill
bb = k.load("brew_batch")
check("8.4 share B26-0068", bb[bb.brew_key == 1].share.iloc[0], 0.50, 2)
check("8.4 shares add to 1 for every fill", (bb.groupby("batch_key").share.sum().round(3) == 1).sum(), 3, 0)
ev = k.q(con, "SELECT event_type, start_utc, end_utc FROM vessel_event WHERE batch_key = 1 OR "
              "(batch_key IS NULL AND vessel_key = (SELECT vessel_key FROM vessel WHERE vessel_code = 'FV07'))")
check("8.2.1 fill to end of CIP days", (pd.Timestamp(ev[ev.event_type == "CIP"].end_utc.iloc[0]) -
                                        pd.Timestamp(ev[ev.event_type == "fill"].start_utc.min())).days, 30, 0)
check("8.2.2 AE in S260323-022", k.q(con, "SELECT value FROM result r JOIN sample s USING (sample_key) "
                                           "WHERE s.sample_id = 'S260323-022' AND test_code = 'AE'").value[0], 2.3, 1)

# chapter 9: the trace
fwd = k.q(con, (k.SQL / "lineage_forward.sql").read_text()).set_index("node").share
loop = k.trace(edges, "M-26-0087")
pallet_ids = set(k.load("package_unit").sscc)
hit = fwd[fwd.index.isin(pallet_ids)]
check("9.2 share 0087 into B26-0069", fwd["B26-0069"], 0.566, 3)
check("9.2 share 0091 into B26-0069",
      edges[(edges.from_node == "M-26-0091") & (edges.to_node == "B26-0069")].share.iloc[0], 0.434, 3)
check("9.2 F07-26-034 to BT02-26-031 hL", edges[edges.from_node == "F07-26-034"].quantity.sum(), 582, 0)
check("9.2 bottle pallet hL", 1920 * 0.0033, 6.336, 3)
check("9.3 share at F07-26-034", fwd["F07-26-034"], 0.783, 3)
check("9.3 pallets reached", len(hit), 23, 0)
check("9.3 every pallet at 0.783", (hit.round(3) == 0.783).sum(), 23, 0)
check("9.5 loop gives the same pallets", loop[loop.index.isin(pallet_ids)].round(3).eq(0.783).sum(), 23, 0)
check("9.5 loop equals CTE", (fwd - loop[fwd.index]).abs().max(), 0, 9)
check("9.3 F08-26-035 not reached", int("F08-26-035" in fwd.index), 0, 0)
packed = pallets.hl["L260412-C1-1"] + pallets.hl["L260413-B1-1"]
check("9.3 can lot hL", pallets.hl["L260412-C1-1"], 166.32, 2)
check("9.3 bottle lot hL", pallets.hl["L260413-B1-1"], 57.02, 2)
check("9.3 packed hL", packed, 223.34, 2)
check("9.3 in tank hL", 582 - packed, 358.66, 2)
ship = k.q(con, "SELECT l.lot_id, COUNT(*) n FROM movement m JOIN package_unit p ON p.package_unit_key = "
                "m.from_node_key JOIN lot l ON l.lot_key = p.pack_lot_key WHERE m.movement_type = 'ship' "
                "GROUP BY l.lot_id").set_index("lot_id").n
check("9.3 can pallets shipped", ship["L260412-C1-1"], 10, 0)
check("9.3 bottle pallets shipped", ship["L260413-B1-1"], 2, 0)
s = round(fwd["BT02-26-031"], 3)  # the book multiplies by the share as printed, 0.783
check("9.5.2 can run exposure hL", 166.32 * s, 130.23, 2)
check("9.5.2 bottle run exposure hL", 57.02 * s, 44.65, 2)
check("9.5.2 in tank exposure hL", 358.66 * s, 280.83, 2)
check("9.5.2 total exposure hL", 582 * s, 455.7, 1)
check("9.5.2 malt from 0087 kg", edges[edges.from_node == "M-26-0087"].quantity.sum(), 8300, 0)
back = k.q(con, (k.SQL / "lineage_backward.sql").read_text()).set_index("node").share
check("9.4 backward 0087", back["M-26-0087"], 0.783, 3)
check("9.4 backward 0091", back["M-26-0091"], 0.217, 3)
check("9.7 blend share", 400 / 600 * 0.783, 0.522, 3)

# chapter 10: the typical month and the cost per tank day
check("10.1 cast", march.cast_hl, 8700, 0)
check("10.1 dispatched", march.dispatched_hl, 8330, 0)
st = k.stage_table("2026-03").set_index("stage")
check("10.1 cellar out", st.out_hl["Cellar"], 8491, 0)
check("10.1 filtration out", st.out_hl["Filtration and bright beer tanks"], 8439, 0)
check("10.1 packed", st.out_hl["Packaging"], 8352, 0)
check("10.1 closure gap hL", march.closure_gap_hl, 22, 0)
check("10.2 total loss hL", march.known_loss_hl + march.closure_gap_hl, 370, 0)
check("10.2 total loss percent", pct(march.known_loss_hl + march.closure_gap_hl, march.cast_hl), 4.25, 2)
check("10.2 excess cellar loss hL", march.cast_hl * 0.005, 43.5, 1)
check("10.3 extract a hL", k.WATER_KG_PER_L * 12.0 * k.sg_from_plato(12.0), 12.56, 2)
check("10.4 tank days a year", months.tank_days_used.sum(), 4658, 0)
per_day = 176000 / (months.tank_days_used.sum() / 12)
check("10.4 overhead per tank day", per_day, 453, 0)
for beer, days, fill, hl in [("lager", 30, 13602, 23.7), ("pale ale", 16, 7255, 12.6), ("stout", 23, 10429, 18.2)]:
    check(f"10.4 overhead a fill {beer}", days * per_day, fill, 0)
    check(f"10.4 overhead a hL {beer}", days * per_day / 574.2, hl, 1)

# chapter 11 and Appendix D: check values
kpi = k.kpi_tables(con)
kb = kpi["kpi_brew"].set_index(["brew_key", "kpi_name"])
check("D1 extract efficiency", pct(*kb.loc[(1, "Extract efficiency"), ["numerator", "denominator"]]), 92.6, 1)
check("D2 wort volume yield", kb.loc[(1, "Wort volume yield")].numerator / kb.loc[(1, "Wort volume yield")].denominator,
      5.66, 2)
check("D2 brewhouse yield, European reading", pct(k.extract_kg(300, 12.0), brew.grist_kg["B26-0068"]), 71.1, 1)
check("D3 cast gravity deviation", kb.loc[(1, "Cast gravity deviation")].numerator, 0.0, 1)
check("D3 meter deviation", grav.inline_meter["B26-0068"] - 12.0, 0.3, 1)
check("D4 cast volume variance", pct(months.cast_hl.sum() / months.brews.sum() - 300, 300), -0.48, 2)
kf = kpi["kpi_fill"].set_index(["batch_key", "kpi_name"])
check("D5 apparent attenuation", pct(*kf.loc[(1, "Apparent attenuation"), ["numerator", "denominator"]]), 81.7, 1)
check("D6 cellar loss month", pct(march.cellar_loss_hl, march.cast_hl), 2.40, 2)
check("D6 cellar loss F07-26-034", pct(*kf.loc[(1, "Cellar loss"), ["numerator", "denominator"]]), 2.40, 2)
check("D7 filtration loss month", pct(march.filtration_loss_hl, march.cast_hl), 0.6, 1)
kbf = kpi["kpi_bright_fill"]
check("D7 filtration loss BT02-26-031", pct(kbf.numerator.iloc[0], kbf.denominator.iloc[0]), 0.6, 1)
check("D8 tank utilisation", pct(months.tank_days_used.sum(), 15 * 365), 85.1, 1)
end_ferm = k.q(con, "SELECT volume_hl FROM vessel_event WHERE event_type = 'fermentation end' AND batch_key = 1")
check("D9 value in tank", end_ferm.volume_hl[0] * 27, 16200, 0)
check("D9 cost of holding", 16200 * 0.12 * 30 / 365, 160, 0)
check("D10 unexplained loss", pct(march.closure_gap_hl, march.cast_hl), 0.25, 2)
check("D10 known loss hL", march.known_loss_hl, 348, 0)
ls = kpi["kpi_line_shift"]
b1 = ls[(ls.equipment_key == 2) & (ls.kpi_name == "Line speed loss")]
check("D12 line speed loss, nameplate", pct(b1.numerator.sum(), b1.denominator.sum()), 20, 0)
shift = k.load("bronze_linectl_shift").set_index("pack_lot_id").loc["L260413-B1-1"]
check("D12 packs an hour", shift.packs_filled / (shift.run_min / 60), 28800, 0)
check("D12 line speed loss, recipe speed", pct(32000 - 28800, 32000), 10, 0)
packed_hl = march.cast_hl - march.known_loss_hl
check("D13 beer loss per hL packed", march.packaging_loss_hl * 100 / packed_hl, 1.04, 2)
fc = k.load("bronze_linectl_fill_check")
cans = fc[fc.pack_lot_id.str.contains("-C1-")]
check("D15 fill giveaway ml", (cans.measured_ml - cans.declared_ml).mean(), 4, 0)
check("D15 fill giveaway percent", pct(4, 330), 1.2, 1)
check("11.3 dispatch yield", pct(march.dispatched_hl, march.cast_hl), 95.7, 1)
check("11.4 pooled rate", pct(80, 3000), 2.67, 2)

# chapter 14 and 15
check("14.1 cellar loss over dispatched", pct(march.cellar_loss_hl, march.dispatched_hl), 2.51, 2)
lot_count = len(k.load("lot"))
check("15.5 about 40 lots (36 to 44)", int(36 <= lot_count <= 44), 1, 0)
days = pd.to_datetime(k.load("brew").mash_in_utc) + pd.Timedelta(hours=5, minutes=30)
check("15.5 brew days", days.dt.date.nunique(), 3, 0)
fvs = k.q(con, "SELECT COUNT(DISTINCT e.vessel_key) n FROM vessel_event e JOIN vessel v USING (vessel_key) "
               "WHERE v.vessel_type = 'fermenter'").n[0]
check("15.5 fermenters", fvs, 6, 0)
check("15.5 packaging lines", k.load("bronze_linectl_shift").equipment_code.nunique(), 2, 0)

report = pd.DataFrame(checks, columns=["where", "computed", "printed", "ok"])
print(report.to_string(index=False))
failed = report[~report.ok]
assert failed.empty, f"{len(failed)} numbers do not match:\n{failed.to_string(index=False)}"
print(f"\nall {len(report)} printed numbers reproduce from data/")
