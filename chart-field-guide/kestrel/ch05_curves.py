"""Synthetic Kestrel pale ale fermentations for chapter 5 (standard library only, seed 26).

Eleven healthy fills are built so the 10th, 50th and 90th percentile curves hit the figures the chapter states:
hour 72 band 3.30 / 3.60 / 3.86, hour 96 p90 3.05, hour 168 band 2.73 / 2.76 / 2.83.
Fills keep their rank at every hour, so with n = 11 the percentiles are fills 2, 6 and 10.
One stalled fill crosses 8 at hour 34, touches the p90 line at hour 54, reads 5.92 at hour 72 and sits above the band from hour 60.
"""
import random
random.seed(26)
HOURS = list(range(0, 169))

def pchip(knots):
    xs, ys = zip(*knots)
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = max(j for j in range(n - 1) if xs[j] <= x)
        t = (x - xs[i]) / h[i]
        h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
        return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]
    return f

def build(f11_96=3.30):
    k = {
     "F1": [(0,13.5),(12,12.9),(22,11.4),(28,9.8),(34,8.0),(42,5.4),(50,4.1),(60,3.4),(72,3.0),(96,2.89),(120,2.72),(168,2.66)],
     "L":  [(0,13.5),(12,13.0),(24,11.9),(32,10.2),(37,8.0),(46,5.6),(54,4.5),(60,4.1),(66,3.6),(72,3.30),(84,3.05),(96,2.90),(120,2.77),(144,2.74),(168,2.73)],
     "M":  [(0,13.5),(12,13.1),(24,12.3),(34,10.1),(41,8.0),(50,5.7),(60,4.4),(66,3.95),(72,3.60),(84,3.25),(96,2.98),(120,2.84),(144,2.78),(168,2.76)],
     "U":  [(0,13.5),(16,13.3),(28,12.2),(38,10.3),(46,8.0),(54,6.55),(59,6.12),(60,5.95),(66,4.9),(72,3.86),(84,3.4),(96,3.05),(120,2.9),(144,2.85),(168,2.83)],
     "F11":[(0,13.5),(16,13.4),(30,12.5),(40,10.6),(49,8.0),(56,6.9),(64,5.6),(72,4.4),(84,3.7),(96,f11_96),(120,3.0),(144,2.92),(168,2.89)],
    }
    return {name: pchip(v) for name, v in k.items()}

ANCH = [0, 1, 5, 9, 10]            # fill indices carried by F1, L, M, U, F11
def make(curves):
    names = ["F1", "L", "M", "U", "F11"]
    def fillk(k, h):               # k is a fill index from 0 to 10; other indices mix their two neighbours
        for a in range(4):
            lo, hi = ANCH[a], ANCH[a + 1]
            if lo <= k <= hi:
                t = (k - lo) / (hi - lo)
                return (1 - t) * curves[names[a]](h) + t * curves[names[a + 1]](h)
    return fillk

def stats96(fillk):
    v = [fillk(k, 96) for k in range(11)]
    m = sum(v) / 11
    sd = (sum((x - m) ** 2 for x in v) / 10) ** 0.5
    return m + 2 * sd

lo, hi = 3.06, 4.5                  # tune the slowest fill at hour 96 so mean + 2 sd reads 3.11
for _ in range(60):
    mid = (lo + hi) / 2
    if stats96(make(build(mid))) > 3.11:
        hi = mid
    else:
        lo = mid
CURVES = build((lo + hi) / 2)
fillk = make(CURVES)
HEALTHY = [[fillk(k, h) for h in HOURS] for k in range(11)]

def pct(vals, q):                  # inclusive percentile, as PERCENTILE.INC
    v = sorted(vals); pos = q * (len(v) - 1); i = int(pos); fr = pos - i
    return v[i] if i + 1 >= len(v) else v[i] + fr * (v[i + 1] - v[i])
P10 = [pct([f[h] for f in HEALTHY], 0.10) for h in HOURS]
P50 = [pct([f[h] for f in HEALTHY], 0.50) for h in HOURS]
P90 = [pct([f[h] for f in HEALTHY], 0.90) for h in HOURS]

_stall = pchip([(0,13.5),(12,12.9),(22,11.4),(28,9.8),(34,8.0),(44,7.1),(54,6.55),(55,6.43),(56,6.33),(57,6.23),(58,6.14),(59,6.06),(60,6.00),(72,5.92),(120,5.89),(168,5.88)])
STALLED = [_stall(h) for h in HOURS]

def cross8(v):
    return next(h for h, x in zip(HOURS, v) if x <= 8.0 + 1e-9)

def check():
    for h in HOURS:   # ranks never cross
        col = [f[h] for f in HEALTHY]
        assert all(col[i] <= col[i + 1] + 1e-9 for i in range(10)), h
    assert [round(P10[72], 2), round(P50[72], 2), round(P90[72], 2)] == [3.30, 3.60, 3.86]
    assert [round(P10[168], 2), round(P50[168], 2), round(P90[168], 2)] == [2.73, 2.76, 2.83]
    assert round(P90[96], 2) == 3.05
    col = [f[96] for f in HEALTHY]; m = sum(col) / 11
    assert round(m + 2 * (sum((x - m) ** 2 for x in col) / 10) ** 0.5, 2) == 3.11
    c = [cross8(f) for f in HEALTHY]
    assert min(c) == 34 and max(c) == 49, c
    assert cross8(STALLED) == 34
    assert abs(STALLED[54] - P90[54]) < 0.005 and all(STALLED[h] <= P90[h] + 1e-9 for h in range(34, 60))
    assert round(STALLED[72], 2) == 5.92
    outside = [h for h in HOURS if STALLED[h] > P90[h] + 1e-9 and h >= 34]
    assert outside == list(range(60, 169)) and len(outside) == 109, (outside[:3], len(outside))
    assert round(100 * (1 - 2.8 / 13.5), 1) == 79.3 and round(100 * (1 - 6.0 / 13.5), 1) == 55.6

if __name__ == "__main__":
    check(); print("ch5 data ok", [cross8(f) for f in HEALTHY])
