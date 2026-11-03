"""The duty and MRP calculator for Brewing in India by the Numbers (Appendix D).

It reads a rate table, picks the row in force on a date, returns duty for
designs A, B, B2 and C (chapter 5) and runs the walk from declared
manufacturing cost (DMC) to MRP (chapters 1.4 and 6). It also holds the five
rate table checks of chapter 13.4.

Synthetic State S only. Its rules match no real state. Money is INR; every
line is rounded to the paisa before the next step, as the book prints it.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from pathlib import Path
import math

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OPEN_END = pd.Timestamp("2099-12-31")  # an open row: in force until superseded


class NoRate(LookupError):
    """No row covers the state, band and date. The calculator refuses."""


def r2(x):
    """Round to the paisa, half up."""
    return float(Decimal(repr(float(x))).quantize(Decimal("0.01"), ROUND_HALF_UP))


def inr(x, dp=2):
    """Format rupees with Indian digit grouping: 1096680 -> '10,96,680.00'."""
    neg = x < 0
    s = f"{abs(x):.{dp}f}"
    whole, _, frac = s.partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        pairs = []
        while len(head) > 2:
            pairs.insert(0, head[-2:])
            head = head[:-2]
        if head:
            pairs.insert(0, head)
        whole = ",".join(pairs + [tail])
    out = whole + ("." + frac if frac else "")
    return ("-" if neg else "") + out


# ---------------------------------------------------------------- rate table

def load_rates(name="rate_table_state_s.csv"):
    t = pd.read_csv(DATA / name, parse_dates=["effective_from", "effective_to"])
    t["effective_to"] = t["effective_to"].fillna(OPEN_END)
    return t


def band_of(abv, rates, state="S"):
    """The strength band a beer falls in, read from the table (up to is inclusive)."""
    d = rates[(rates.state == state) & (rates.kind == "duty")]
    hit = d[(d.abv_min < abv) & (abv <= d.abv_max)]
    if hit.empty:
        raise NoRate(f"no band in State {state} covers {abv} percent ABV")
    return hit.band.iloc[0]


def row_in_force(rates, state, abv, date, kind="duty", item=None):
    """The one row in force for a state, strength and date. Refuses on none or two."""
    date = pd.Timestamp(date)
    t = rates[(rates.state == state) & (rates.kind == kind)]
    if item:
        t = t[t["item"] == item]
    if kind == "duty":
        t = t[(t.abv_min < abv) & (abv <= t.abv_max)]
    t = t[(t.effective_from <= date) & (date <= t.effective_to)]
    if len(t) != 1:
        what = "no row" if t.empty else f"{len(t)} rows"
        raise NoRate(f"{what} for State {state}, {abv} percent ABV, {date.date()}: refuse and name the gap")
    return t.iloc[0]


def duty_for(row, dmc_case, bulk_litres, abv):
    """Duty a case under the row's design."""
    design = row["design"]
    if design == "A":
        return r2(row["share"] * dmc_case)
    if design == "B":
        return r2(row["rate_per_bl"] * bulk_litres)
    if design == "B2":
        return r2(bulk_litres * abv / 100 * row["rate_per_lal"])
    if design == "C":
        return r2(max(row["share"] * dmc_case, row["floor_per_bl"] * bulk_litres))
    raise ValueError(f"unknown design {design}")


def floor_bites_below(share, floor_per_bl, bulk_litres):
    """DMC a case below which the floor sets the duty (design C)."""
    return r2(floor_per_bl * bulk_litres / share)


# ---------------------------------------------------------------- the walk

@dataclass
class Walk:
    dmc: float
    duty: float
    fee: float
    landed: float
    buyer_margin: float
    buyer_price: float
    retail_margin: float
    pre_round: float
    pre_round_bottle: float
    mrp_bottle: float
    mrp_case: float
    rounding: float
    rate_version: str

    @property
    def state_share(self):
        return (self.duty + self.fee) / self.mrp_case


def walk(dmc_case, bottles=12, litres=0.65, abv=5.3, date="2026-07-01",
         rates=None, state="S", buyer=0.08, retail=0.15, step=5):
    """DMC a case to MRP: duty, pass fee, buyer margin, retailer margin, round up a bottle."""
    rates = load_rates() if rates is None else rates
    bl = bottles * litres
    row = row_in_force(rates, state, abv, date)
    fee_row = row_in_force(rates, state, abv, date, kind="fee", item="transport pass")
    duty = duty_for(row, dmc_case, bl, abv)
    fee = r2(fee_row["fee_amount"] * bl)
    landed = r2(dmc_case + duty + fee)
    bm = r2(buyer * landed)
    bp = r2(landed + bm)
    rm = r2(retail * bp)
    pre = r2(bp + rm)
    pre_b = pre / bottles
    mrp_b = float((Decimal(repr(pre_b)) / step).to_integral_value(ROUND_CEILING) * step)
    mrp_c = r2(mrp_b * bottles)
    return Walk(dmc_case, duty, fee, landed, bm, bp, rm, pre, r2(pre_b), mrp_b, mrp_c,
                r2(mrp_c - pre), row["row_id"])


def reverse_dmc(mrp_bottle, bottles=12, litres=0.65, share=1.10, fee_per_bl=2.0,
                buyer=0.08, retail=0.15):
    """Highest DMC a case that still lands at this MRP (percentage side of the duty)."""
    k = (1 + buyer) * (1 + retail)
    return (mrp_bottle * bottles / k - fee_per_bl * bottles * litres) / (1 + share)


def carrying_cost(cash, days, rate=0.12):
    return cash * rate * days / 365


# ---------------------------------------------------------------- chapter 13.4 checks

def check_rate_exists(rates, facts):
    """Facts (state, abv, dispatch_date) with no row, or two rows, in force."""
    bad = []
    for f in facts.itertuples():
        try:
            row_in_force(rates, f.state, f.abv, f.dispatch_date)
        except NoRate as e:
            bad.append((f.pass_no, str(e)))
    return bad


def check_gap_overlap(rates, start, end):
    """Each state and band must have exactly one duty row on every day from start to end."""
    bad = []
    d = rates[rates.kind == "duty"]
    for (state, band), g in d.groupby(["state", "band"]):
        for day in pd.date_range(start, end):
            n = ((g.effective_from <= day) & (day <= g.effective_to)).sum()
            if n != 1:
                bad.append((state, band, day.date(), "gap" if n == 0 else "overlap"))
    return bad


def check_recompute(rates, facts, tol=0.01):
    """Duty charged against the larger of share x DMC and floor x bulk litres."""
    bad = []
    for f in facts.itertuples():
        row = row_in_force(rates, f.state, f.abv, f.dispatch_date)
        due = r2(duty_for(row, f.dmc_case, f.bulk_litres_case, f.abv) * f.cases)
        if abs(due - f.duty_charged) > tol:
            bad.append((f.pass_no, f.duty_charged, due, r2(due - f.duty_charged)))
    return bad


def check_band(rates, facts):
    """ABV and the band charged disagree."""
    return [(f.pass_no, f.abv, f.band_charged, band_of(f.abv, rates, f.state))
            for f in facts.itertuples() if band_of(f.abv, rates, f.state) != f.band_charged]


def check_expiry(rates, today, days=90):
    """Rows with no check for more than `days` days."""
    today = pd.Timestamp(today)
    checked = pd.to_datetime(rates["checked_on"])
    old = rates[(today - checked).dt.days > days]
    return list(old.row_id)


if __name__ == "__main__":
    w = walk(12600 * 0.078)
    assert (w.duty, w.landed, w.pre_round, w.mrp_bottle, w.rounding) == (1081.08, 2079.48, 2582.72, 220.0, 57.28)
    assert inr(1096680) == "10,96,680.00" and inr(135e7, 0) == "1,35,00,00,000"
    print("calculator self-check passed:", inr(w.mrp_case), "a case, rate version", w.rate_version)
