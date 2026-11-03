"""Synthetic Kestrel lager final gravity for chapter 6 (standard library only, seed 26).

Forty fills: 20 stable (mean 2.194, sample sd 0.1135, mean moving range 0.1458 so sigma within 0.129),
then a drift of 0.012 degrees Plato a fill. The run is searched with a fixed seed until it reproduces every number the chapter states:
no point beyond the limits, eight in a row rule first fires at fill 40, CUSUM crosses 0.64 at fill 34, EWMA signals at fill 35,
last ten fills average 2.384. A second set of 20 on target fills after the fix has mean 2.21 and sample sd 0.093.
"""
import random
CENTRE, SIGMA_W, K, H = 2.194, 0.129, 0.064, 0.64
LCL, UCL = CENTRE - 3 * SIGMA_W, CENTRE + 3 * SIGMA_W
SPEC_LO, SPEC_HI = 1.8, 2.6

def mean(v): return sum(v) / len(v)
def sd(v):
    m = mean(v); return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
def mr(v): return mean([abs(v[i] - v[i - 1]) for i in range(1, len(v))])

def standardise(v, m, s):
    a, b = mean(v), sd(v)
    return [m + (x - a) * s / b for x in v]

def runs8(v):
    """First fill (1 based) at which eight in a row sit on one side of the centre line, or None."""
    for i in range(7, len(v)):
        w = v[i - 7:i + 1]
        if all(x > CENTRE for x in w) or all(x < CENTRE for x in w):
            return i + 1
    return None

def cusum(v):
    c, out = 0.0, []
    for x in v:
        c = max(0.0, c + x - (CENTRE + K)); out.append(c)
    return out

def ewma(v):
    z, out = CENTRE, []
    for x in v:
        z = 0.2 * x + 0.8 * z; out.append(z)
    return out

EW = 3 * SIGMA_W * (0.2 / 1.8) ** 0.5          # 0.129 settled half width
def first(pred, v):
    return next((i + 1 for i, x in enumerate(v) if pred(x)), None)

def build():
    rnd = random.Random(26)
    # baseline: exact mean and sd, then shuffle until the mean moving range gives sigma 0.129
    base = standardise([rnd.gauss(0, 1) for _ in range(20)], CENTRE, 0.1135)
    best, target = None, 0.1458
    for _ in range(200000):
        rnd.shuffle(base)
        if best is None or abs(mr(base) - target) < abs(mr(best) - target):
            best = base[:]
        if abs(mr(best) - target) < 0.0003 and runs8(best) is None and min(best) > LCL and max(best) < UCL:
            break
    base = best
    # drift: draw noise until the chart rules fire where the chapter says
    for _ in range(3000000):
        e = [rnd.gauss(0, 0.10) for _ in range(20)]
        d = [CENTRE + 0.012 * (i + 1) + e[i] for i in range(20)]
        # nudge fills 31 to 40 so their mean is exactly 2.384
        shift = 2.384 - mean(d[10:])
        d = d[:10] + [x + shift for x in d[10:]]
        v = base + d
        if not all(LCL < x < UCL for x in v): continue
        if runs8(v) != 40: continue
        c = cusum(v)
        if first(lambda x: x >= H, c) != 34: continue
        z = ewma(v)
        if first(lambda x: x > CENTRE + EW or x < CENTRE - EW, z) != 35: continue
        return v
    raise SystemExit("no run found")

def build_after():
    rnd = random.Random(27)
    return standardise([rnd.gauss(0, 1) for _ in range(20)], 2.21, 0.093)

V = build()
BASE, DRIFT = V[:20], V[20:]
AFTER = build_after()
CU, EWM = cusum(V), ewma(V)

def check():
    assert round(mean(BASE), 3) == 2.194 and round(sd(BASE), 4) == 0.1135
    assert round(mr(BASE) / 1.128, 3) == 0.129, mr(BASE) / 1.128
    assert round(LCL, 2) == 1.81 and round(UCL, 2) == 2.58
    assert all(LCL < x < UCL for x in V)
    assert runs8(V) == 40 and first(lambda x: x >= H, CU) == 34
    assert first(lambda x: x > CENTRE + EW or x < CENTRE - EW, EWM) == 35
    assert round(mean(V[30:]), 3) == 2.384
    assert round(mean(AFTER), 2) == 2.21 and round(sd(AFTER), 3) == 0.093
    cp, cpk = 0.8 / (6 * 0.129), (CENTRE - SPEC_LO) / (3 * 0.129)
    assert (round(cp, 2), round(cpk, 2)) == (1.03, 1.02)
    pp, ppk = 0.8 / (6 * 0.1135), (mean(BASE) - SPEC_LO) / (3 * 0.1135)
    assert (round(pp, 2), round(ppk, 2)) == (1.17, 1.16)
    assert round((SPEC_HI - 2.21) / (3 * 0.093), 2) == 1.40
    assert round(SPEC_HI - 2.384, 3) == 0.216

if __name__ == "__main__":
    check(); print("ch6 data ok", round(mr(BASE) / 1.128, 4), runs8(V))
