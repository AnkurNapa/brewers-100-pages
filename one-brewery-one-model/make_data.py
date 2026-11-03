"""Write every CSV in data/ for One Brewery, One Model.

Kestrel Brewing is synthetic. Every row here is invented for teaching.
Run: python3 make_data.py
The random parts (month noise) use a fixed seed, so every run writes the same files.
"""
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
SEED = 26
IST = timedelta(hours=5, minutes=30)  # India Standard Time, no daylight saving


def ist(m, d, h=0, mi=0, y=2026):
    """A local Kestrel time (IST) turned into UTC."""
    return datetime(y, m, d, h, mi) - IST


def fmt(t):
    return t.strftime("%Y-%m-%d %H:%M:%S") if t is not None else None


def write(name, rows, cols=None):
    df = pd.DataFrame(rows, columns=cols)
    for c in df.columns:  # keys and flags stay whole numbers even where some are empty
        if (c.endswith("_key") or c.endswith("_flag")) and df[c].dtype == float:
            df[c] = df[c].astype("Int64")
    df.to_csv(DATA / f"{name}.csv", index=False)
    return df


def sscc(serial):
    """18 digit SSCC: extension 0, GS1's own example company prefix 0614141, serial, check digit."""
    body = "0" + "0614141" + f"{serial:09d}"
    total = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed(body)))
    return body + str((10 - total % 10) % 10)


# ---------------------------------------------------------------- master data
SITE = 1
site = [dict(site_key=SITE, site_code="KES", site_name="Kestrel Brewing (synthetic)",
             valid_from="2020-01-01", valid_to=None)]

items = [
    (1001, "PILS-MALT", "Pilsner malt", "malt", "kg", None),
    (1002, "PALE-MALT", "Pale ale malt", "malt", "kg", None),
    (1003, "CRYS-MALT", "Crystal malt", "malt", "kg", None),
    (1010, "HOP-BITTER", "Bittering hop pellets", "hops", "kg", None),
    (1011, "HOP-AROMA", "Aroma hop pellets", "hops", "kg", None),
    (1020, "YEAST-LAG", "Lager yeast slurry", "yeast", "kg", None),
    (1021, "YEAST-ALE", "Ale yeast slurry", "yeast", "kg", None),
    (1030, "CO2", "Carbon dioxide", "co2", "kg", None),
    (1040, "CAN-330", "Empty can 330 ml", "can", "each", 0.0033),
    (1041, "BTL-330", "Empty bottle 330 ml", "bottle", "each", 0.0033),
    (1042, "CROWN", "Crown cork", "crown", "each", None),
    (1043, "LABEL-LAG", "Lager bottle label", "label", "each", None),
    (1050, "WORT-LAG", "Lager wort", "wort", "hL", None),
    (1051, "WORT-PA", "Pale ale wort", "wort", "hL", None),
    (1060, "BEER-LAG", "Kestrel Lager, beer", "beer", "hL", None),
    (1061, "BEER-PA", "Kestrel Pale Ale, beer", "beer", "hL", None),
    (1070, "SKU-LAG-CAN", "Kestrel Lager 330 ml can", "product", "hL", 0.0033),
    (1071, "SKU-LAG-BTL", "Kestrel Lager 330 ml bottle", "product", "hL", 0.0033),
    (1072, "SKU-PA-CAN", "Kestrel Pale Ale 330 ml can", "product", "hL", 0.0033),
]
item = [dict(item_key=k, item_code=c, item_name=n, item_type=t, base_unit=u, fill_volume_hl=f,
             valid_from="2024-01-01", valid_to=None, source_system="erp") for k, c, n, t, u, f in items]

vessel = []
vkey = {}
key = 1
for code, vtype, cap, loss in [("MT01", "mash tun", 330, None), ("KT01", "kettle", 330, None),
                                ("WP01", "whirlpool", 330, None)]:
    vessel.append(dict(vessel_key=key, vessel_code=code, vessel_type=vtype, capacity_hl=cap,
                       normal_loss_pct=loss, site_key=SITE, valid_from="2020-01-01", valid_to=None,
                       source_system="erp"))
    vkey[code] = key
    key += 1
for n in range(1, 16):
    code = f"FV{n:02d}"
    if code == "FV10":  # FV10 was replaced in 2025: same code on the floor, new key, old row closed
        vessel.append(dict(vessel_key=key, vessel_code=code, vessel_type="fermenter", capacity_hl=600,
                           normal_loss_pct=1.9, site_key=SITE, valid_from="2020-01-01",
                           valid_to="2025-06-30", source_system="erp"))
        key += 1
        vessel.append(dict(vessel_key=key, vessel_code=code, vessel_type="fermenter", capacity_hl=600,
                           normal_loss_pct=1.9, site_key=SITE, valid_from="2025-07-01", valid_to=None,
                           source_system="erp"))
    else:
        vessel.append(dict(vessel_key=key, vessel_code=code, vessel_type="fermenter", capacity_hl=600,
                           normal_loss_pct=1.9, site_key=SITE, valid_from="2020-01-01", valid_to=None,
                           source_system="erp"))
    vkey[code] = key
    key += 1
for n in range(1, 5):
    code = f"BT{n:02d}"
    vessel.append(dict(vessel_key=key, vessel_code=code, vessel_type="bright beer tank", capacity_hl=600,
                       normal_loss_pct=0.6, site_key=SITE, valid_from="2020-01-01", valid_to=None,
                       source_system="erp"))
    vkey[code] = key
    key += 1

equipment = [
    dict(equipment_key=1, equipment_code="C1", equipment_type="can line filler", site_key=SITE,
         valid_from="2020-01-01", valid_to=None),
    dict(equipment_key=2, equipment_code="B1", equipment_type="bottle line filler", site_key=SITE,
         valid_from="2020-01-01", valid_to=None),
    dict(equipment_key=3, equipment_code="FLT01", equipment_type="filter", site_key=SITE,
         valid_from="2020-01-01", valid_to=None),
    dict(equipment_key=4, equipment_code="CEN01", equipment_type="centrifuge", site_key=SITE,
         valid_from="2020-01-01", valid_to=None),
]

# Synthetic public holidays: Republic Day, Independence Day and Gandhi Jayanti
HOLIDAYS = {"2026-01-26", "2026-08-15", "2026-10-02"}
calendar_day = []
d = datetime(2026, 1, 1)
while d.year == 2026:
    fy_start = 2026 if d.month >= 4 else 2025
    period = (d.month - 4) % 12 + 1
    calendar_day.append(dict(date=d.strftime("%Y-%m-%d"), iso_week=d.isocalendar()[1],
                             brew_day_flag=int(d.weekday() < 6),
                             financial_period=f"FY{fy_start}-{(fy_start + 1) % 100:02d} P{period:02d}",
                             public_holiday_flag=int(d.strftime("%Y-%m-%d") in HOLIDAYS)))
    d += timedelta(days=1)

recipe_version = [
    dict(recipe_version_key=1, recipe_code="LAG", version=2, og_plato=12.0, apparent_extract_plato=2.2,
         ibu=18, colour_ebc=7, cast_hl=300, valid_from="2025-01-01", valid_to="2025-12-31"),
    dict(recipe_version_key=2, recipe_code="LAG", version=3, og_plato=12.0, apparent_extract_plato=2.2,
         ibu=18, colour_ebc=7, cast_hl=300, valid_from="2026-01-01", valid_to=None),
    dict(recipe_version_key=3, recipe_code="PA", version=2, og_plato=13.5, apparent_extract_plato=2.8,
         ibu=38, colour_ebc=14, cast_hl=300, valid_from="2025-06-01", valid_to=None),
]

spec_rows = [
    # item, test, low, high, unit, version, from, to
    (1060, "IBU", 17, 19, "IBU", 2, "2025-01-01", "2025-12-31"),
    (1060, "OG", 11.8, 12.2, "degrees Plato", 3, "2026-01-01", None),
    (1060, "AE", 1.8, 2.6, "degrees Plato", 3, "2026-01-01", None),
    (1060, "IBU", 16, 20, "IBU", 3, "2026-01-01", None),
    (1060, "EBC", 6, 8, "EBC", 3, "2026-01-01", None),
    (1060, "PH", 4.2, 4.5, "pH", 3, "2026-01-01", None),
    (1060, "DO", None, 50, "ppb", 3, "2026-01-01", None),
    (1061, "OG", 13.3, 13.7, "degrees Plato", 2, "2025-06-01", None),
    (1061, "AE", 2.4, 3.2, "degrees Plato", 2, "2025-06-01", None),
    (1061, "IBU", 34, 42, "IBU", 2, "2025-06-01", None),
    (1061, "EBC", 12, 16, "EBC", 2, "2025-06-01", None),
    (1061, "PH", 4.2, 4.5, "pH", 2, "2025-06-01", None),
    (1061, "DO", None, 50, "ppb", 2, "2025-06-01", None),
]
spec = [dict(spec_key=i + 1, item_key=r[0], test_code=r[1], low=r[2], high=r[3], unit=r[4], version=r[5],
             valid_from=r[6], valid_to=r[7]) for i, r in enumerate(spec_rows)]


def spec_for(item_key, test, when):
    day = when.strftime("%Y-%m-%d")
    for s in spec:
        if s["item_key"] == item_key and s["test_code"] == test and s["valid_from"] <= day and \
                (s["valid_to"] is None or day <= s["valid_to"]):
            return s
    return None


unit_factor = [
    dict(from_unit="kg", to_base_unit="kg", factor=1, intercept=0),
    dict(from_unit="t", to_base_unit="kg", factor=1000, intercept=0),
    dict(from_unit="bag50", to_base_unit="kg", factor=50, intercept=0),
    dict(from_unit="lb", to_base_unit="kg", factor=0.45359237, intercept=0),
    dict(from_unit="hL", to_base_unit="hL", factor=1, intercept=0),
    dict(from_unit="L", to_base_unit="hL", factor=0.01, intercept=0),
    dict(from_unit="bbl_us", to_base_unit="hL", factor=1.17348, intercept=0),
    dict(from_unit="can330", to_base_unit="hL", factor=0.0033, intercept=0),
    dict(from_unit="degF", to_base_unit="degC", factor=5 / 9, intercept=-160 / 9),
    dict(from_unit="degC", to_base_unit="degC", factor=1, intercept=0),
]

shift = [dict(shift_name="A", start_time="06:00", end_time="14:00"),
         dict(shift_name="B", start_time="14:00", end_time="22:00"),
         dict(shift_name="C", start_time="22:00", end_time="06:00")]

tag_map = [
    dict(tag="CEL.FV07.TT01.PV", vessel="FV07", measurement="Beer temperature", unit="degrees C",
         interval="1 min", valid_from="2024-03-01", valid_to=None),
    dict(tag="CEL.FV07.LT01.PV", vessel="FV07", measurement="Liquid level", unit="hL",
         interval="1 min", valid_from="2024-03-01", valid_to=None),
    dict(tag="CEL.FV07.PT01.PV", vessel="FV07", measurement="Head pressure", unit="bar",
         interval="1 min", valid_from="2024-03-01", valid_to=None),
    dict(tag="CEL.FV07.XV01.PV", vessel="FV07", measurement="Inlet valve open", unit="state",
         interval="1 min", valid_from="2024-03-01", valid_to=None),
    dict(tag="CEL.FV07.XV02.PV", vessel="FV07", measurement="Outlet valve open", unit="state",
         interval="1 min", valid_from="2024-03-01", valid_to=None),
    dict(tag="CEL.FV07.CT01.PV", vessel="FV07", measurement="Return line conductivity", unit="mS/cm",
         interval="1 min", valid_from="2024-03-01", valid_to=None),
    dict(tag="BRH.KT01.TT02.PV", vessel="Kettle 1", measurement="Wort temperature", unit="degrees C",
         interval="10 s", valid_from="2023-06-15", valid_to="2025-09-30"),
    dict(tag="BRH.WL01.DT01.PV", vessel="Wort line", measurement="Wort gravity (inline meter)",
         unit="degrees Plato", interval="1 min", valid_from="2024-03-01", valid_to=None),
]

precedence_rows = [
    ("WORT_GRAVITY", "lab", 1, "QA lead"), ("WORT_GRAVITY", "inline_meter", 2, "QA lead"),
    ("WORT_GRAVITY", "brew_sheet", 3, "QA lead"),
    ("AE_TRANSFER", "lab", 1, "QA lead"), ("AE_TRANSFER", "inline_meter", 2, "QA lead"),
    ("TRANSFER_VOLUME", "flow_meter", 1, "Finance controller"),
    ("TRANSFER_VOLUME", "erp", 2, "Finance controller"),
    ("TRANSFER_VOLUME", "tank_dip", 3, "Finance controller"),
    ("FV_TEMPERATURE", "historian", 1, "Head brewer"), ("FV_TEMPERATURE", "operator_log", 2, "Head brewer"),
    ("IBU", "lab", 1, "QA lead"), ("COLOUR", "lab", 1, "QA lead"), ("PH", "lab", 1, "QA lead"),
    ("REJECT_COUNT", "line_controller", 1, "Packaging manager"),
    ("REJECT_COUNT", "erp", 2, "Packaging manager"),
    ("STOCK_QUANTITY", "erp", 1, "Finance controller"),
    ("STOCK_QUANTITY", "physical_count", 2, "Finance controller"),
]
precedence = [dict(measurement_code=m, source=s, rank=r, valid_from="2026-01-01", valid_to=None, signed_by=w)
              for m, s, r, w in precedence_rows]

# ---------------------------------------------------------------- the slice: six brews, three fills
# brew id, recipe key, mash in (IST), fill, planned grist, actual grist, lab OG, meter OG, brew sheet OG
BREWS = [
    ("B26-0068", 2, (3, 12, 2, 50), "F07-26-034", 5300, 5300, 12.0, 12.3, 12.0),
    ("B26-0069", 2, (3, 12, 9, 10), "F07-26-034", 5300, 5300, 12.1, 12.2, 12.0),
    ("B26-0070", 2, (3, 13, 2, 50), "F08-26-035", 5300, 5300, 12.0, 12.1, 12.0),
    ("B26-0071", 2, (3, 13, 9, 10), "F08-26-035", 5300, 5300, 11.9, 12.0, 12.0),
    ("B26-0072", 3, (3, 14, 2, 50), "F09-26-036", 6000, 6000, 13.5, 13.6, 13.5),
    ("B26-0073", 3, (3, 14, 21, 40), "F09-26-036", 6000, 6040, 13.6, 13.7, 13.5),
]
KNOCKOUT_AFTER_MASH_IN = timedelta(hours=3, minutes=50)
FILL_MINUTES = 55
CAST_HL = 300.0

brew, brew_key = [], {}
for i, (bid, rv, mi, fill, plan, act, *_r) in enumerate(BREWS, start=1):
    brew.append(dict(brew_key=i, brew_id=bid, order_ref=f"26{int(bid[-4:]):05d}", recipe_version_key=rv,
                     vessel_key=vkey["KT01"], mash_in_utc=fmt(ist(*mi)), wort_cast_hl=CAST_HL,
                     grist_kg=act, source_system="brew_sheet"))
    brew_key[bid] = i


def knockout(bid):
    mi = [b for b in BREWS if b[0] == bid][0][2]
    return ist(*mi) + KNOCKOUT_AFTER_MASH_IN


# fill id, vessel, beer item, transfer (IST), bright tank fill id, bright vessel
FILLS = [
    ("F07-26-034", "FV07", 1060, (4, 10, 8, 0), "BT02-26-031", "BT02"),
    ("F08-26-035", "FV08", 1060, (4, 11, 8, 0), "BT04-26-032", "BT04"),
    ("F09-26-036", "FV09", 1061, (3, 28, 8, 0), "BT01-26-026", "BT01"),
]
CELLAR_LOSS, FILTRATION_LOSS = 0.024, 0.006
batch, batch_key, vessel_event = [], {}, []
ev = 1


def add_event(vessel_code, bkey, etype, start, end, vol, temp, source, rule):
    global ev
    vessel_event.append(dict(event_key=ev, vessel_key=vkey[vessel_code], batch_key=bkey, event_type=etype,
                             start_utc=fmt(start), end_utc=fmt(end), volume_hl=vol, temperature_c=temp,
                             source=source, rule_version=rule))
    ev += 1


for i, (fid, fv, beer, tr, btid, bt) in enumerate(FILLS, start=1):
    brews = [b[0] for b in BREWS if b[3] == fid]
    start = knockout(brews[0])
    tr_start = ist(*tr)
    tr_end = tr_start + (timedelta(hours=3, minutes=20) if fid == "F07-26-034" else timedelta(hours=3))
    batch.append(dict(batch_key=i, batch_id=fid, vessel_key=vkey[fv], item_key=beer, fill_start_utc=fmt(start),
                      empty_utc=fmt(tr_end), closed_flag=1, close_reason_code="TRANSFERRED",
                      source_system="cellar_log"))
    batch_key[fid] = i
    detected = fid == "F07-26-034"
    for b in brews:
        ko = knockout(b)
        add_event(fv, i, "fill", ko, ko + timedelta(minutes=FILL_MINUTES), CAST_HL, 10.0,
                  "detected from tags" if detected else "typed on the brew sheet", "fill-v1" if detected else None)
    fill_hl = CAST_HL * len(brews)
    days = 30 if beer == 1060 else 13
    add_event(fv, i, "fermentation end", start + timedelta(days=days - 20 if beer == 1060 else days - 6),
              None, fill_hl, 12.0 if beer == 1060 else 18.0, "typed on the cellar log", None)
    if beer == 1061:
        add_event(fv, i, "dry hop", ist(3, 20, 10, 0), ist(3, 20, 10, 30), None, 18.0,
                  "typed on the cellar log", None)
    out_hl = round(fill_hl * (1 - CELLAR_LOSS), 2)
    add_event(fv, i, "transfer out", tr_start, tr_end, out_hl, 0.5, "typed on the transfer log", None)
    cip = tr_end.replace(hour=2, minute=30) + timedelta(days=1)  # 08:00 IST next day
    add_event(fv, None, "CIP", cip, cip + timedelta(hours=2), None, 80.0,
              "detected from tags" if detected else "typed on the CIP log", "cip-v1" if detected else None)
    add_event(bt, i, "bright fill", tr_start + timedelta(minutes=30), tr_end + timedelta(minutes=10),
              round(fill_hl * (1 - CELLAR_LOSS - FILTRATION_LOSS), 2), 0.0, "typed on the transfer log", None)
for fv, day in [("FV10", 15), ("FV11", 16), ("FV12", 17)]:
    add_event(fv, None, "CIP", ist(3, day, 9, 0), ist(3, day, 11, 0), None, 80.0, "typed on the CIP log", None)

brew_batch = []
for b in BREWS:
    n = len([x for x in BREWS if x[3] == b[3]])
    brew_batch.append(dict(brew_key=brew_key[b[0]], batch_key=batch_key[b[3]], wort_in_hl=CAST_HL,
                           share=round(CAST_HL / (CAST_HL * n), 4)))

# ---------------------------------------------------------------- lots (about 40)
lot, lot_key = [], {}


def add_lot(lid, ikey, ltype, qty, created, supplier=None, source="erp"):
    k = len(lot) + 1
    lot.append(dict(lot_key=k, lot_id=lid, item_key=ikey, lot_type=ltype, quantity_base=qty,
                    created_utc=fmt(created), supplier_lot_no=supplier, source_system=source))
    lot_key[lid] = k


for lid, ik, q, day, sup in [("M-26-0083", 1001, 25000, (2, 20), "SUP-A 26/0311"),
                              ("M-26-0087", 1001, 25000, (3, 2), "SUP-A 26/0398"),
                              ("M-26-0089", 1002, 20000, (3, 4), "SUP-B 7741"),
                              ("M-26-0090", 1003, 2000, (3, 4), "SUP-B 7742"),
                              ("M-26-0091", 1001, 25000, (3, 9), "SUP-A 26/0421")]:
    add_lot(lid, ik, "malt", q, ist(day[0], day[1], 10, 0), sup)
for n, ik in zip(range(41, 49), [1010, 1010, 1011, 1011, 1010, 1011, 1010, 1011]):
    add_lot(f"H-26-{n:04d}", ik, "hops", 250, ist(2, 25, 10, 0), f"HOPCO {n}A")
for lid, ik in [("Y-26-0012", 1020), ("Y-26-0013", 1020), ("Y-26-0014", 1021)]:
    add_lot(lid, ik, "yeast", 300, ist(3, 11, 18, 0), None, "lab")
for lid in ["G-26-0006", "G-26-0007", "G-26-0008"]:
    add_lot(lid, 1030, "co2", 18000, ist(3, 1, 9, 0), "TANKER " + lid[-2:])
for lid, q in [("C-26-0100", 150000), ("C-26-0101", 150000), ("C-26-0102", 150000), ("C-26-0103", 150000)]:
    add_lot(lid, 1040, "can", q, ist(3, 5, 9, 0), "CANMAKER " + lid[-4:])
for lid in ["BTL-26-0055", "BTL-26-0056"]:
    add_lot(lid, 1041, "bottle", 60000, ist(3, 5, 9, 0), "GLASSCO " + lid[-4:])
for lid in ["CR-26-0031", "CR-26-0032"]:
    add_lot(lid, 1042, "crown", 100000, ist(3, 5, 9, 0), "CROWNCO " + lid[-4:])
for lid in ["LB-26-0021", "LB-26-0022"]:
    add_lot(lid, 1043, "label", 100000, ist(3, 5, 9, 0), "PRINTCO " + lid[-4:])
for fid, fv, beer, tr, btid, bt in FILLS:
    add_lot(btid, beer, "bright_fill", round(600 * (1 - CELLAR_LOSS - FILTRATION_LOSS), 2), ist(*tr), None,
            "transfer_log")

# pack lot, bright fill, line, item, pallets, units a pallet, pallet hL, shipped pallets, run start IST
PACK_LOTS = [
    ("L260329-C1-1", "BT01-26-026", "C1", 1072, 40, 3600, 11.88, 40, (3, 29, 6, 30)),
    ("L260412-C1-1", "BT02-26-031", "C1", 1070, 14, 3600, 11.88, 10, (4, 12, 7, 0)),
    ("L260413-B1-1", "BT02-26-031", "B1", 1071, 9, 1920, 6.336, 2, (4, 13, 7, 0)),
    ("L260414-C1-1", "BT04-26-032", "C1", 1070, 20, 3600, 11.88, 0, (4, 14, 7, 0)),
]
for pl, btid, line, sku, n, units, hl, shipped, run in PACK_LOTS:
    add_lot(pl, sku, "pack", round(n * hl, 3), ist(*run), None, "line_controller")

package_unit, serial = [], 1
for pl, btid, line, sku, n, units, hl, shipped, run in PACK_LOTS:
    for p in range(n):
        package_unit.append(dict(package_unit_key=serial, sscc=sscc(260000000 + serial), pack_lot_key=lot_key[pl],
                                 unit_count=units, volume_hl=hl,
                                 created_utc=fmt(ist(*run) + timedelta(minutes=6 * (p + 1)))))
        serial += 1

# ---------------------------------------------------------------- movements (the lineage edges)
movement = []


def move(mtype, ftype, fkey, ttype, tkey, ikey, qty, unit, when, order_ref, source):
    movement.append(dict(movement_key=len(movement) + 1, movement_type=mtype, from_node_type=ftype,
                         from_node_key=fkey, to_node_type=ttype, to_node_key=tkey, item_key=ikey,
                         quantity=qty, unit=unit, posted_utc=fmt(when), order_ref=order_ref,
                         source_system=source))


MALT = {"B26-0068": [("M-26-0087", 1001, 5300)],
        "B26-0069": [("M-26-0087", 1001, 3000), ("M-26-0091", 1001, 2300)],
        "B26-0070": [("M-26-0091", 1001, 5300)],
        "B26-0071": [("M-26-0091", 1001, 5300)],
        "B26-0072": [("M-26-0089", 1002, 5500), ("M-26-0090", 1003, 500)],
        "B26-0073": [("M-26-0089", 1002, 5540), ("M-26-0090", 1003, 500)]}
HOPS = {"LAG": [("H-26-0041", 1010, 30), ("H-26-0043", 1011, 20)],
        "PA": [("H-26-0042", 1010, 25), ("H-26-0044", 1011, 45)]}
for b in brew:
    when = datetime.strptime(b["mash_in_utc"], "%Y-%m-%d %H:%M:%S")
    for lid, ik, q in MALT[b["brew_id"]]:
        move("consume", "lot", lot_key[lid], "brew", b["brew_key"], ik, q, "kg", when, b["order_ref"], "erp")
    for lid, ik, q in HOPS["LAG" if b["recipe_version_key"] == 2 else "PA"]:
        move("consume", "lot", lot_key[lid], "brew", b["brew_key"], ik, q, "kg", when + timedelta(hours=2),
             b["order_ref"], "erp")
    bid = b["brew_id"]
    fid = [x[3] for x in BREWS if x[0] == bid][0]
    wort = 1050 if b["recipe_version_key"] == 2 else 1051
    move("produce", "brew", b["brew_key"], "batch", batch_key[fid], wort, CAST_HL, "hL", knockout(bid),
         b["order_ref"], "brew_sheet")
for (fid, fv, beer, tr, btid, bt), yeast, gas in zip(FILLS, ["Y-26-0012", "Y-26-0013", "Y-26-0014"],
                                                     ["G-26-0007", "G-26-0008", "G-26-0006"]):
    first = [x[0] for x in BREWS if x[3] == fid][0]
    move("consume", "lot", lot_key[yeast], "batch", batch_key[fid], 1020 if beer == 1060 else 1021, 300, "kg",
         knockout(first), None, "lab")
    move("transfer", "batch", batch_key[fid], "lot", lot_key[btid], beer,
         round(600 * (1 - CELLAR_LOSS - FILTRATION_LOSS), 2), "hL", ist(*tr) + timedelta(hours=3), None,
         "transfer_log")
    move("consume", "lot", lot_key[gas], "lot", lot_key[btid], 1030, 30, "kg", ist(*tr) + timedelta(hours=3),
         None, "erp")
CANS = {"L260329-C1-1": "C-26-0100", "L260412-C1-1": "C-26-0101", "L260414-C1-1": "C-26-0102"}
pu_by_lot = {}
for p in package_unit:
    pu_by_lot.setdefault(p["pack_lot_key"], []).append(p)
for pl, btid, line, sku, n, units, hl, shipped, run in PACK_LOTS:
    start = ist(*run)
    order = f"PK{pl[1:7]}{line}"
    move("pack", "lot", lot_key[btid], "pack_lot", lot_key[pl], sku, round(n * hl, 3), "hL", start, order,
         "line_controller")
    if pl in CANS:
        move("consume", "lot", lot_key[CANS[pl]], "pack_lot", lot_key[pl], 1040, n * units, "each", start, order,
             "erp")
    else:  # bottles and labels are posted; the crown issue for this run never reached the ERP
        move("consume", "lot", lot_key["BTL-26-0055"], "pack_lot", lot_key[pl], 1041, n * units, "each", start,
             order, "erp")
        move("consume", "lot", lot_key["LB-26-0021"], "pack_lot", lot_key[pl], 1043, n * units, "each", start,
             order, "erp")
    for j, p in enumerate(pu_by_lot[lot_key[pl]]):
        move("pack", "pack_lot", lot_key[pl], "pallet", p["package_unit_key"], sku, hl, "hL",
             datetime.strptime(p["created_utc"], "%Y-%m-%d %H:%M:%S"), order, "warehouse")
        if j < shipped:
            move("ship", "pallet", p["package_unit_key"], "customer", 1, sku, hl, "hL",
                 start + timedelta(days=4), f"SO-26-{lot_key[pl]:04d}", "erp")

# ---------------------------------------------------------------- samples and results
SAMPLERS = ["RK", "AS", "PM"]
bronze_sample, sample, result = [], [], []
seq_by_day = {}


def sample_id(t_utc):
    local = t_utc + IST
    day = local.strftime("%y%m%d")
    seq_by_day[day] = seq_by_day.get(day, 0) + 1
    return f"S{day}-{seq_by_day[day]:03d}"


def occupancy(vessel_code):
    """(start, end, batch_key) intervals when a vessel held a batch, from vessel_event."""
    vk = vkey[vessel_code]
    out = []
    for b in batch:
        if b["vessel_key"] == vk:
            out.append((datetime.strptime(b["fill_start_utc"], "%Y-%m-%d %H:%M:%S"),
                        datetime.strptime(b["empty_utc"], "%Y-%m-%d %H:%M:%S"), b["batch_key"]))
    for e in vessel_event:
        if e["vessel_key"] == vk and e["event_type"] == "bright fill":
            s = datetime.strptime(e["start_utc"], "%Y-%m-%d %H:%M:%S")
            out.append((s, s + timedelta(days=6), e["batch_key"]))
    return out


def add_sample(vessel_code, when, label, point, tests, sid=None, time_known=True, entered_after=None):
    """tests: list of (code, value, unit, method, instrument[, retest_of_value]) tuples."""
    sid = sid or sample_id(when)
    sk = len(sample) + 1
    bronze_sample.append(dict(sample_id=sid, vessel_code=vessel_code, label_id=label,
                              sampled_date_ist=(when + IST).strftime("%Y-%m-%d"),
                              sampled_time_ist=(when + IST).strftime("%H:%M") if time_known else None,
                              sample_point=point, sampler=SAMPLERS[sk % 3]))
    # the three joins, ranked by trust (chapter 5.5)
    bk, method = None, "none"
    if label and label.startswith("F"):
        bk, method = batch_key[label], "label"
    elif time_known:
        hits = [o[2] for o in occupancy(vessel_code) if o[0] <= when <= o[1]]
        if hits:
            bk, method = hits[0], "vessel_time"
    else:
        hits = [o[2] for o in occupancy(vessel_code) if o[0].date() <= when.date() <= o[1].date()]
        if hits:
            bk, method = hits[0], "vessel_date"
    sample.append(dict(sample_key=sk, sample_id=sid, vessel_key=vkey[vessel_code], batch_key=bk,
                       match_method=method, sample_point=point, sampled_at_utc=fmt(when),
                       sampler=bronze_sample[-1]["sampler"]))
    beer = [b["item_key"] for b in batch if b["batch_key"] == bk]
    for t in tests:
        code, value, unit, method_name, instrument = t[:5]
        entered = when + (entered_after or timedelta(hours=6))
        if len(t) > 5:
            entered = when + t[5]
        judged = beer and (point != "fermenter inlet" or code == "OG")  # wort pH has no beer spec
        s = spec_for(beer[0], code, when) if judged else None
        in_spec = None
        if s is not None:
            in_spec = int((s["low"] is None or value >= s["low"]) and (s["high"] is None or value <= s["high"]))
        result.append(dict(result_key=len(result) + 1, sample_key=sk, test_code=code, method=method_name,
                           value=value, unit=unit, analyst=SAMPLERS[(sk + 1) % 3], instrument=instrument,
                           sampled_at_utc=fmt(when), entered_at_utc=fmt(entered), status="approved",
                           is_current=1, retest_reason=None, spec_key=s["spec_key"] if s else None,
                           in_spec_flag=in_spec, reading_source="lab"))
    return sk


OG = dict(code="OG", unit="degrees Plato", method="density meter, lab", instrument="DMA-LAB-1")
for b in BREWS:
    bid, fid, lab, meter, sheet = b[0], b[3], b[6], b[7], b[8]
    fv = [f[1] for f in FILLS if f[0] == fid][0]
    t = knockout(bid) + timedelta(minutes=20)
    after = timedelta(hours=8, minutes=40) if bid == "B26-0068" else timedelta(hours=6)
    add_sample(fv, t, bid, "fermenter inlet",
               [("OG", lab, "degrees Plato", "density meter, lab", "DMA-LAB-1"),
                ("PH", 5.2, "pH", "pH electrode", "PH-LAB-2")], entered_after=after)
    for r in result:
        if r["sample_key"] == len(sample) and r["test_code"] == "OG":
            r["reading_source"] = f"lab (rank 1); inline meter {meter}; brew sheet {sheet}"

# FV07 mid fermentation (chapter 8.2.2) and the chapter 5.2 latency case
add_sample("FV07", ist(3, 23, 14, 5), "F07-26-034", "fermenter, racking arm",
           [("AE", 2.3, "degrees Plato", "density meter, lab", "DMA-LAB-1"),
            ("PH", 4.4, "pH", "pH electrode", "PH-LAB-2"),
            ("DO", 20, "ppb", "optical DO", "DO-LAB-1")], sid="S260323-022")
add_sample("FV07", ist(3, 25, 6, 40), None, "fermenter, racking arm",
           [("AE", 2.25, "degrees Plato", "density meter, lab", "DMA-LAB-1")],
           entered_after=timedelta(hours=4, minutes=35))
# end of fermentation
add_sample("FV07", ist(4, 1, 9, 0), "F07-26-034", "fermenter, racking arm",
           [("AE", 2.2, "degrees Plato", "density meter, lab", "DMA-LAB-1")])
add_sample("FV08", ist(4, 2, 9, 0), None, "fermenter, racking arm",
           [("AE", 2.3, "degrees Plato", "density meter, lab", "DMA-LAB-1")])
add_sample("FV09", ist(3, 26, 9, 0), None, "fermenter, racking arm",
           [("PH", 4.3, "pH", "pH electrode", "PH-LAB-2")], sid="S26032-6")  # bad ID pattern, no AE
# a paper lab result with a date but no time; a sample from an empty tank
add_sample("FV08", ist(3, 20, 12, 0), None, "fermenter, racking arm",
           [("PH", 4.5, "pH", "pH electrode", "PH-LAB-2")], time_known=False)
add_sample("FV10", ist(3, 18, 10, 0), None, "fermenter, racking arm",
           [("PH", 6.9, "pH", "pH electrode", "PH-LAB-2")])
# bright tank release sets
RELEASE = {"BT02": [("IBU", 18.2), ("EBC", 7.1), ("PH", 4.35), ("DO", 28)],
           "BT04": [("IBU", 15.6), ("EBC", 6.8), ("PH", 4.38), ("DO", 31)],
           "BT01": [("IBU", 37.5), ("EBC", 14.2), ("PH", 4.3), ("DO", 32)]}
UNITS = {"IBU": ("IBU", "spectrophotometer", "UV-LAB-1"), "EBC": ("EBC", "spectrophotometer", "UV-LAB-1"),
         "PH": ("pH", "pH electrode", "PH-LAB-2"), "DO": ("ppb", "optical DO", "DO-LAB-1")}
for fid, fv, beer, tr, btid, bt in FILLS:
    when = ist(*tr) + timedelta(hours=5)
    tests = []
    for code, v in RELEASE[bt]:
        u, m, ins = UNITS[code]
        late = timedelta(hours=30) if (bt == "BT01" and code == "EBC") else timedelta(hours=5)
        tests.append((code, v, u, m, ins, late))
    sk = add_sample(bt, when, btid, "bright tank, release", tests)
    if bt == "BT04":  # IBU retest: a new row, the first one stays with is_current = 0
        first = [r for r in result if r["sample_key"] == sk and r["test_code"] == "IBU"][0]
        first["is_current"] = 0
        retest = dict(first)
        retest.update(result_key=len(result) + 1, value=16.8, in_spec_flag=1, is_current=1,
                      retest_reason="sample warmed before analysis; repeat on retained sample",
                      entered_at_utc=fmt(when + timedelta(hours=9)))
        result.append(retest)

# ---------------------------------------------------------------- historian trace for FV07 and the wort meter
tag_reading = []


def reading(tag, t, value, flag="good"):
    tag_reading.append(dict(tag=tag, reading_utc=fmt(t), arrived_utc=fmt(t + timedelta(seconds=2)),
                            value=value, quality_flag=flag))


rng = np.random.default_rng(SEED)
ko1, ko2 = knockout("B26-0068"), knockout("B26-0069")


def fv07_state(t):
    """Level hL, temperature C, inlet, outlet, conductivity for FV07 at minute t (UTC)."""
    def ramp(t0, minutes, a, b):
        x = (t - t0).total_seconds() / 60
        return a + (b - a) * min(max(x / minutes, 0), 1)
    tr1, pause, tr2 = ist(4, 10, 8, 0), ist(4, 10, 10, 0), ist(4, 10, 10, 20)
    cip0 = ist(4, 11, 8, 0)
    if t < ist(4, 1):
        level = ramp(ko1, FILL_MINUTES, 0, 300) if t < ko2 else ramp(ko2, FILL_MINUTES, 300, 600)
        inlet = int(ko1 <= t < ko1 + timedelta(minutes=FILL_MINUTES) or
                    ko2 <= t < ko2 + timedelta(minutes=FILL_MINUTES))
        temp = 10.0 if level > 0 else 18.0
        return level, temp, inlet, 0, 0.6
    out_hl = 585.6
    if t < pause:
        level = ramp(tr1, 120, out_hl, out_hl / 3)
    else:
        level = ramp(tr2, 60, out_hl / 3, 0)
    outlet = int(tr1 <= t < pause or tr2 <= t < tr2 + timedelta(minutes=60))
    cip = cip0 <= t < cip0 + timedelta(hours=2)
    temp = 80.0 if cip else (0.5 if level > 0 else 15.0)
    return level, temp, 0, outlet, (60.0 if cip else 0.6)


for t0, hours in [(ist(3, 12), 24), (ist(4, 10, 6, 0), 36)]:
    for m in range(hours * 60):
        t = t0 + timedelta(minutes=m)
        level, temp, inlet, outlet, cond = fv07_state(t)
        noise = float(rng.normal(0, 0.05))
        gap = ist(3, 12, 18, 0) <= t < ist(3, 12, 18, 40)  # the temperature tag goes silent for 40 minutes
        if not gap:
            reading("CEL.FV07.TT01.PV", t, round(temp + noise, 2))
        reading("CEL.FV07.LT01.PV", t, round(level, 1))
        reading("CEL.FV07.XV01.PV", t, inlet)
        reading("CEL.FV07.XV02.PV", t, outlet)
        reading("CEL.FV07.CT01.PV", t, cond, "uncertain" if cond > 30 and m % 17 == 0 else "good")
for b in BREWS:
    ko = knockout(b[0])
    for m in range(FILL_MINUTES):
        reading("BRH.WL01.DT01.PV", ko + timedelta(minutes=m), b[7])

# ---------------------------------------------------------------- other source extracts (bronze shapes)
bronze_brewsheet_brew = []
for b in BREWS:
    mi = ist(*b[2])
    bronze_brewsheet_brew.append(dict(
        brew_id=b[0], brew_date_ist=(mi + IST).strftime("%Y-%m-%d"), recipe="LAG" if b[1] == 2 else "PA",
        recipe_version=3 if b[1] == 2 else 2, fill_id=b[3], planned_wort_hl=300, actual_wort_hl=300,
        malt_name="Pilsner" if b[1] == 2 else ("Pale ale malt" if b[0] != "B26-0073" else "Pale"),
        actual_grist_t=b[5] / 1000, start_ist=(mi + IST).strftime("%H:%M"),
        end_ist=(knockout(b[0]) + timedelta(minutes=FILL_MINUTES) + IST).strftime("%H:%M"),
        gravity_plato=b[8], brewer="GN" if b[1] == 2 else "SK"))

bronze_erp_order = [dict(order_ref=f"26{int(b[0][-4:]):05d}", brew_id=b[0], item_code="100234" if b[1] == 2
                         else "100240", planned_grist_kg=b[4], planned_wort_hl=300) for b in BREWS]

# ERP goods movements: what the ERP posted, in its own codes and units (bags of 50 kg)
ERP_CODE = {1001: "100234", 1002: "100240", 1003: "100241", 1010: "200110", 1011: "200111", 1040: "300400",
            1041: "300410", 1042: "300420", 1043: "300430", 1030: "400300"}
bronze_erp_goods_movement = []
for mv in movement:
    if mv["source_system"] != "erp" or mv["movement_type"] == "ship":
        continue
    code = ERP_CODE.get(mv["item_key"])
    qty, unit = mv["quantity"], mv["unit"]
    if mv["item_key"] in (1001, 1002, 1003):
        qty, unit = mv["quantity"] / 50, "bag50"
    bronze_erp_goods_movement.append(dict(doc_no=f"49{mv['movement_key']:08d}", movement_type=mv["movement_type"],
                                          item_code=code, from_ref=None, to_ref=mv["order_ref"], quantity=qty,
                                          unit=unit, posted_date=mv["posted_utc"][:10], order_ref=mv["order_ref"]))
# the actual pale ale grist was 6,040 kg; the ERP backflushed the planned 6,000
for r in bronze_erp_goods_movement:
    if r["order_ref"] == "2600073" and r["item_code"] == "100240":
        r["quantity"] = 5500 / 50
# a new bag size posted under a code nobody mapped; a silo log name with a typo
bronze_erp_goods_movement.append(dict(doc_no="4900009901", movement_type="receipt", item_code="100299",
                                      from_ref="SUP-A", to_ref="SILO1", quantity=40, unit="bag25",
                                      posted_date="2026-03-10", order_ref=None))
bronze_silolog_draw = [dict(brew_id=b[0], malt_code="PILS" if b[1] == 2 else "PALE", lot_id=lid, kg=q)
                       for b in BREWS for lid, ik, q in MALT[b[0]] if ik != 1003]
bronze_silolog_draw[1]["malt_code"] = "PILS "  # trailing space typed into the silo log
bronze_lims_material = [dict(material_code="MALT-PILS-A", description="Pilsner malt, intake"),
                        dict(material_code="MALT-PALE-A", description="Pale ale malt, intake")]

xref = []
for sysname, code, ent, sk in [("erp", "100234", "item", 1001), ("silo_log", "PILS", "item", 1001),
                               ("brew_sheet", "Pilsner", "item", 1001), ("lims", "MALT-PILS-A", "item", 1001),
                               ("erp", "100240", "item", 1002), ("silo_log", "PALE", "item", 1002),
                               ("brew_sheet", "Pale ale malt", "item", 1002), ("erp", "100241", "item", 1003),
                               ("erp", "200110", "item", 1010), ("erp", "200111", "item", 1011),
                               ("erp", "300400", "item", 1040), ("erp", "300410", "item", 1041),
                               ("erp", "300420", "item", 1042), ("erp", "300430", "item", 1043),
                               ("erp", "400300", "item", 1030),
                               ("historian", "FV07", "vessel", vkey["FV07"]), ("erp", "F07", "vessel", vkey["FV07"]),
                               ("historian", "FV08", "vessel", vkey["FV08"]), ("erp", "F08", "vessel", vkey["FV08"]),
                               ("historian", "FV09", "vessel", vkey["FV09"]), ("erp", "F09", "vessel", vkey["FV09"])]:
    xref.append(dict(source_system=sysname, source_key=code, entity=ent, surrogate_key=sk,
                     valid_from="2024-01-01", valid_to=None))
xref.append(dict(source_system="erp", source_key="F10", entity="vessel", surrogate_key=vkey["FV10"] - 1,
                 valid_from="2020-01-01", valid_to="2025-06-30"))
xref.append(dict(source_system="erp", source_key="F10", entity="vessel", surrogate_key=vkey["FV10"],
                 valid_from="2025-07-01", valid_to=None))

bronze_transferlog_transfer = [dict(transfer_id=f"T26-{i:04d}", from_vessel=fv, to_vessel=bt,
                                    start_ist=(ist(*tr) + IST).strftime("%Y-%m-%d %H:%M"),
                                    volume_hl=round(600 * (1 - CELLAR_LOSS), 1))
                               for i, (fid, fv, beer, tr, btid, bt) in enumerate(FILLS, start=101)]

# line controller: one row per line per shift
bronze_linectl_shift = [
    dict(equipment_code="C1", shift_date="2026-03-29", shift_name="A", pack_lot_id="L260329-C1-1",
         planned_min=300, run_min=250, packs_filled=110220, packs_rejected=220, rated_per_hour=30000, flush_l=150),
    dict(equipment_code="C1", shift_date="2026-03-29", shift_name="B", pack_lot_id="L260329-C1-1",
         planned_min=120, run_min=75, packs_filled=34080, packs_rejected=80, rated_per_hour=30000, flush_l=0),
    dict(equipment_code="C1", shift_date="2026-04-12", shift_name="A", pack_lot_id="L260412-C1-1",
         planned_min=150, run_min=120, packs_filled=50520, packs_rejected=120, rated_per_hour=30000, flush_l=150),
    dict(equipment_code="B1", shift_date="2026-04-13", shift_name="A", pack_lot_id="L260413-B1-1",
         planned_min=60, run_min=36.3, packs_filled=17424, packs_rejected=144, rated_per_hour=36000, flush_l=120),
    dict(equipment_code="C1", shift_date="2026-04-14", shift_name="A", pack_lot_id="L260414-C1-1",
         planned_min=200, run_min=170, packs_filled=72210, packs_rejected=210, rated_per_hour=30000, flush_l=150),
]
bronze_linectl_fill_check = []
for pl, ml in [("L260329-C1-1", [334, 333, 335, 334, 334]), ("L260412-C1-1", [335, 333, 334, 334, 334]),
               ("L260413-B1-1", [333, 334, 332, 333, 333]), ("L260414-C1-1", [334, 334, 333, 335, 334])]:
    for j, v in enumerate(ml):
        bronze_linectl_fill_check.append(dict(pack_lot_id=pl, check_no=j + 1, declared_ml=330, measured_ml=v))
bronze_qa_complaint = [dict(complaint_id="Q-26-0019", received_date="2026-04-20", pack_lot_id="L260412-C1-1",
                            category="flavour")]
bronze_supplier_coa = [
    dict(lot_id="M-26-0083", fine_grind_extract_pct=81.0, fine_coarse_diff_pct=1.0, moisture_pct=4.0),
    dict(lot_id="M-26-0087", fine_grind_extract_pct=81.0, fine_coarse_diff_pct=1.0, moisture_pct=4.0),
    dict(lot_id="M-26-0089", fine_grind_extract_pct=81.5, fine_coarse_diff_pct=1.2, moisture_pct=4.2),
    dict(lot_id="M-26-0090", fine_grind_extract_pct=75.0, fine_coarse_diff_pct=0.0, moisture_pct=5.0),
    dict(lot_id="M-26-0091", fine_grind_extract_pct=81.0, fine_coarse_diff_pct=1.0, moisture_pct=4.0),
]
stage_cost = [dict(stage="wort", carried_cost_usd_per_hl=24.0),
              dict(stage="end of fermentation", carried_cost_usd_per_hl=27.0),
              dict(stage="end of maturation", carried_cost_usd_per_hl=29.5),
              dict(stage="bright beer", carried_cost_usd_per_hl=32.0),
              dict(stage="packed", carried_cost_usd_per_hl=63.0)]
drill_log = []  # QA fills this in at each mock recall (chapter 9.6)

# ---------------------------------------------------------------- the year by month (stage totals)
MONTHS = [f"2026-{m:02d}" for m in range(1, 13)]
BREWS_A_MONTH = [28, 27, 29, 29, 31, 30, 29, 28, 29, 31, 30, 29]       # 350 in the year
TYPICAL = "2026-03"                                                    # the book's typical month


def fit_total(values, total):
    """Scale to a total, round to one decimal, put the rounding residue on the last value."""
    v = np.array(values) * total / sum(values)
    v = np.round(v, 1)
    v[-1] = round(total - v[:-1].sum(), 1)
    return list(v)


others = [m for m in MONTHS if m != TYPICAL]
nb = [BREWS_A_MONTH[MONTHS.index(m)] for m in others]
cast_o = fit_total([n * 298.4 * (1 + rng.normal(0, 0.004)) for n in nb], 104500 - 8700)
disp_o = fit_total([c * 0.9575 * (1 + rng.normal(0, 0.01)) for c in cast_o], 100000 - 8330)
month_rows, opening = [], 4200.0
for m, n in zip(MONTHS, BREWS_A_MONTH):
    if m == TYPICAL:
        cast, cel, fil, pac, disp, gap = 8700.0, 209.0, 52.0, 87.0, 8330.0, 22.0
    else:
        j = others.index(m)
        cast, disp = cast_o[j], disp_o[j]
        cel = round(cast * (0.024 + rng.normal(0, 0.0012)), 1)
        fil = round(cast * (0.006 + rng.normal(0, 0.0004)), 1)
        pac = round(cast * (0.010 + rng.normal(0, 0.0006)), 1)
        gap = round(cast * (0.009 if m == "2026-07" else 0.0025 + rng.normal(0, 0.0005)), 1)
    change = round(cast - disp - cel - fil - pac - gap, 1)
    closing = round(opening + change, 1)
    month_rows.append(dict(month=m, brews=n, cast_hl=cast, cellar_loss_hl=cel, filtration_loss_hl=fil,
                           packaging_loss_hl=pac, dispatched_hl=disp, opening_tank_hl=opening,
                           closing_tank_hl=closing))
    opening = closing
td = fit_total([r["brews"] for r in month_rows if r["month"] != TYPICAL], 4658 - 388)
for r in month_rows:
    r["tank_days_used"] = 388 if r["month"] == TYPICAL else int(round(td.pop(0)))
month_rows[-1]["tank_days_used"] += 4658 - sum(r["tank_days_used"] for r in month_rows)

# ---------------------------------------------------------------- the KPI dictionary (Appendix D)
V = "1.0, 2026-10-31"
KPI = [
    ("Extract efficiency", "The share of the extract in the grist that reached the fermenter.",
     "Extract in cast kg / theoretical extract in grist kg", "brew",
     "Grist weights from the brew sheet; malt certificate from the lot; cast volume from `vessel_event`; "
     "gravity from the lab result", "Head brewer", "3,767 / 4,070 = 92.6 percent"),
    ("Wort volume yield", "The hectolitres of wort cast for every 100 kg of grist.",
     "Cast hL / grist kg x 100; compare within one gravity", "brew", "`brew` (`wort_cast_hl`, `grist_kg`)",
     "Head brewer", "300 / 5,300 x 100 = 5.66 hL per 100 kg at 12.0 degrees Plato"),
    ("Cast gravity deviation", "How far the cast gravity sits from the recipe.",
     "Cast degrees Plato - recipe degrees Plato", "brew", "Lab result under the precedence rule; `recipe_version`",
     "Head brewer", "12.0 - 12.0 = 0.0 degrees Plato on the lab figure (the meter figure gives +0.3)"),
    ("Cast volume variance", "How far the cast volume sits from the recipe volume.",
     "(Cast hL - recipe hL) / recipe hL", "brew", "`vessel_event`; `recipe_version`", "Head brewer",
     "(104,500 / 350 - 300) / 300 = -0.48 percent, the yearly average"),
    ("Apparent attenuation", "The share of the original gravity that has fermented away, read from apparent extract.",
     "(OG - apparent extract) / OG", "fill", "Lab results", "Cellar manager", "(12.0 - 2.2) / 12.0 = 81.7 percent"),
    ("Cellar loss", "The share of wort cast that does not leave the cellar.",
     "(Cast hL - hL sent to filtration) / cast hL", "fill; month is a sum over a sum", "`vessel_event`",
     "Cellar manager", "209 / 8,700 = 2.40 percent"),
    ("Filtration and bright tank loss", "The share of wort cast lost between the filter and the bright tank.",
     "(hL into filter - hL into bright tank) / cast hL", "bright tank fill", "`vessel_event`", "Cellar manager",
     "52 / 8,700 = 0.6 percent"),
    ("Tank utilisation", "The share of available fermenter days that held a fill, with turnaround.",
     "Days each fermenter held a fill, with turnaround / (tanks x days in period)", "month", "`vessel_event`",
     "Planner", "4,658 / 5,475 = 85.1 percent for a year"),
    ("Value in tank", "The money tied up in beer in a tank, at the carried cost of its stage.",
     "hL in tank x carried cost per hL at that stage", "day", "`vessel_event`; item cost", "Finance",
     "600 x 27 = 16,200 for one lager fill at the end of fermentation"),
    ("Unexplained loss", "The share of wort cast that the balance cannot place.",
     "(Cast - dispatched - known loss - change in stock) / cast hL; change in stock = closing tank hL - "
     "opening tank hL", "month", "`vessel_event`; `movement`", "Plant manager",
     "(8,700 - 8,330 - 348 - 0) / 8,700 = 22 / 8,700 = 0.25 percent"),
    ("OEE", "How much of the planned time a line made good packs at rated speed.",
     "Availability x performance x quality. Availability is run time over planned time; performance is actual "
     "count over the count at rated speed; quality is good over total", "line shift", "Line controller",
     "Packaging manager", "78.5 x 86.4 x 99.7 = 67.6 percent on the companion slice, all line shifts"),
    ("Line speed loss", "The share of rated output that a line did not make.",
     "1 - (packs made / (run time x rated speed))", "line shift", "Line controller", "Packaging manager",
     "1 - 28,800 / 36,000 = 20 percent against nameplate"),
    ("Beer loss per hL packed", "The litres lost in fills, rejects and flush for each hL packed.",
     "Litres lost in fills, rejects and flush / hL packed", "pack lot", "Line controller; `vessel_event`",
     "Packaging manager", "87 hL on 8,352 hL packed = 1.04 litres per hL"),
    ("Reject rate", "The share of filled packs that were rejected.", "Rejected packs / packs filled", "pack lot",
     "Line controller", "Packaging manager", "774 / 284,454 = 0.27 percent on the companion slice"),
    ("Fill giveaway", "The beer inside the pack above the declared volume.",
     "Mean (measured fill - declared fill) in ml", "pack lot", "Line controller fill checks", "Packaging manager",
     "4 ml on a 330 ml can, about 1.2 percent"),
    ("Right first time", "The share of batches that passed every spec on the first test.",
     "Batches that pass every spec on first test / batches tested", "week", "`result`; `spec`", "QA lead",
     "2 of 3 fills = 66.7 percent on the companion slice; F08-26-035 failed bitterness on its first test"),
    ("Hold rate", "The share of finished batches placed on hold.", "Batches placed on hold / batches completed",
     "week",
     "A hold record. `batch` in C.1 has no hold column, so add one or load the QA hold log before this entry goes live",
     "QA lead", "Set once the hold record is loaded"),
    ("Spec compliance", "The share of results inside their spec.", "Results inside spec / results tested",
     "test, by week", "`result`; `spec`", "QA lead",
     "26 / 26 current results = 100.0 percent on the companion slice"),
    ("Complaints per million packs", "How many complaints arrive for each million packs dispatched.",
     "Complaints / packs dispatched x 1,000,000", "month",
     "The QA complaint log (`bronze_qa_complaint`); packs dispatched from `movement` (ship) joined to `package_unit`",
     "QA lead", "1 / 183,840 x 1,000,000 = 5.44 for April 2026 on the companion slice"),
    ("Mock recall time", "The minutes from a lot code to a signed pallet list.",
     "Minutes from lot code to a signed pallet list", "exercise", "Drill log", "QA lead",
     "Target set by QA before the first drill (ch. 9.6)"),
]
kpi_dictionary = [dict(name=n, plain_definition=p, formula=f, grain=g, source=s, owner=o, version=V, check_value=c)
                  for n, p, f, g, s, o, c in KPI]

# ---------------------------------------------------------------- write
if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    tables = dict(
        item=item, vessel=vessel, calendar_day=calendar_day, recipe_version=recipe_version, spec=spec,
        brew=brew, batch=batch, vessel_event=vessel_event, lot=lot, sample=sample, movement=movement,
        package_unit=package_unit, result=result, brew_batch=brew_batch,
        tag_reading=tag_reading, equipment=equipment, site=site, xref=xref, unit_factor=unit_factor,
        shift=shift, tag_map=tag_map, precedence=precedence, kpi_dictionary=kpi_dictionary,
        bronze_lims_sample=bronze_sample, bronze_lims_material=bronze_lims_material,
        bronze_brewsheet_brew=bronze_brewsheet_brew, bronze_erp_order=bronze_erp_order,
        bronze_erp_goods_movement=bronze_erp_goods_movement, bronze_silolog_draw=bronze_silolog_draw,
        bronze_transferlog_transfer=bronze_transferlog_transfer, bronze_linectl_shift=bronze_linectl_shift,
        bronze_linectl_fill_check=bronze_linectl_fill_check, bronze_qa_complaint=bronze_qa_complaint,
        bronze_supplier_coa=bronze_supplier_coa, stage_cost=stage_cost, vessel_event_month=month_rows,
    )
    for name, rows in tables.items():
        write(name, rows)
    write("drill_log", drill_log, ["drill_id", "drill_date", "lot_id", "minutes_to_signed_list",
                                   "pallets_found", "pallets_known", "pallets_wrong", "signed_by"])
    print(f"wrote {len(tables) + 1} CSV files to {DATA}")
