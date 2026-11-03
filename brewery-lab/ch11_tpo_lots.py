"""Chapter 11.5 lot level set: 50 bottle lots, TPO and papery tags (synthetic, seed 2081).

find() starts at seed 1102 and keeps the first seed that fits; that is 2081. make_data.py imports it.

Every lot is a bottle lot inside the 150 ppb bottle limit, so every lot shipped on the
normal release route. Rejection sampling keeps the planted shape: 13 lots above 120 ppb,
7 above 140, 103 papery tags in 400 records, one lot at 138 ppb with 5 of 8 papery.
"""
import math
import random

N_LOTS, TASTERS, LIMIT = 50, 8, 150


def make(seed):
    rng = random.Random(seed)
    tpo = sorted(round(rng.uniform(55, 119)) for _ in range(37))
    tpo += sorted(round(rng.uniform(121, 139)) for _ in range(5)) + [138]
    tpo += sorted(round(rng.uniform(141, 149)) for _ in range(7))
    pap = [sum(rng.random() < min(0.95, max(0.0, 0.0075 * (t - 75))) for _ in range(TASTERS))
           for t in tpo]
    pap[42] = 5  # the 11.4.2 example lot: 138 ppb, 5 of 8 papery
    return tpo, pap


def stats(tpo, pap):
    share = [p / TASTERS for p in pap]
    n = len(tpo)
    mx, my = sum(tpo) / n, sum(share) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(tpo, share))
    sxx = sum((x - mx) ** 2 for x in tpo)
    syy = sum((y - my) ** 2 for y in share)
    r = sxy / math.sqrt(sxx * syy)
    hi = [s for t, s in zip(tpo, share) if t > 120]
    lo = [s for t, s in zip(tpo, share) if t <= 120]
    k, p = 6, 7 / 50
    tail = sum(math.comb(k, j) * p ** j * (1 - p) ** (k - j) for j in range(4, k + 1))
    return dict(r=r, r2=r * r, slope_pp_per_10ppb=1000 * sxy / sxx,
                t=r * math.sqrt(n - 2) / math.sqrt(1 - r * r),
                n_hi=len(hi), mean_hi=100 * sum(hi) / len(hi),
                n_lo=len(lo), mean_lo=100 * sum(lo) / len(lo),
                papery=sum(pap), max_tpo=max(tpo), tail=tail)


def find():
    for seed in range(1102, 1102 + 100000):
        tpo, pap = make(seed)
        s = stats(tpo, pap)
        if s["papery"] == 103 and 0.75 <= s["r"] <= 0.80:
            return seed, tpo, pap, s
    raise RuntimeError("no seed found")


if __name__ == "__main__":
    seed, tpo, pap, s = find()
    assert max(tpo) < LIMIT and sum(t > 120 for t in tpo) == 13 and sum(t > 140 for t in tpo) == 7
    assert sum(pap) == 103 and tpo[42] == 138 and pap[42] == 5
    complaints = [31, 41, 43, 44, 45, 49]  # 6 staling complaints, planted: 4 on the 7 lots above 140 ppb
    assert sum(tpo[i] > 140 for i in complaints) == 4
    print("seed", seed, "complaint lots", [tpo[i] for i in complaints])
    print(list(zip(tpo, pap)))
    for k, v in s.items():
        print(k, round(v, 4))
