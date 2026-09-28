# score_tracts.py - rebuilt 2026-09-28 from file 04b's formulas and the fields of _pipeline/model/tract_scores_x1.0.json.
# build_rows(state) turns the two ACS pulls (tract_<st>_g1.json, tract_<st>_g2.json) into per-tract raw metrics;
# score(rows, mult, ref) applies the cash-flow model at duplex multiplier `mult` and the enhanced score, with the norm_
# percentiles taken against `ref` (a dict metric -> sorted reference values; None = rank within `rows` themselves).
import json, math, os, sys, bisect
def f(x):
    try:
        v = float(x); return v if v > -1e8 else None   # ACS uses -666666666 etc. for suppressed cells
    except: return None
def load(d, st):
    g1 = json.load(open(f"{d}/tract_{st}_g1.json")); g2 = json.load(open(f"{d}/tract_{st}_g2.json"))
    h1, h2 = g1[0], g2[0]; m2 = {}
    for r in g2[1:]:
        e = dict(zip(h2, r)); m2[e["state"] + e["county"] + e["tract"]] = e
    m3 = {}
    if os.path.exists(f"{d}/tract_{st}_r2.json"):
        g3 = json.load(open(f"{d}/tract_{st}_r2.json")); h3 = g3[0]
        for r in g3[1:]:
            e = dict(zip(h3, r)); m3[e["state"] + e["county"] + e["tract"]] = {"B25032_016E": e["B25032_016E"]}
    out = {}
    for r in g1[1:]:
        e = dict(zip(h1, r)); geoid = e["state"] + e["county"] + e["tract"]
        if geoid in m2: e.update(m2[geoid])
        if geoid in m3: e.update(m3[geoid])
        out[geoid] = e
    return out
def pmt_annual(loan, rate, years=30):
    r = rate / 12; n = years * 12; return loan * r / (1 - (1 + r) ** -n) * 12
def build_rows(raw):
    rows = {}
    for geoid, e in raw.items():
        g = lambda k: f(e.get(k))
        pop = g("B01003_001E"); occ = g("B25003_001E"); ro = g("B25003_003E"); vac = g("B25004_002E")
        u2 = g("B25024_004E") or 0; u34 = g("B25024_005E") or 0; r2 = g("B25032_016E")   # renter-occupied units in 2-unit structures
        inc = g("B19013_001E"); incm = g("B19013_001M"); rent = g("B25064_001E"); rentm = g("B25064_001M"); val = g("B25077_001E"); valm = g("B25077_001M")
        rb_tot = g("B25070_001E"); rb_nc = g("B25070_011E") or 0
        rb30 = sum((g(k) or 0) for k in ["B25070_007E", "B25070_008E", "B25070_009E", "B25070_010E"]); rb50 = g("B25070_010E") or 0
        pov_u = g("B17001_001E"); pov = g("B17001_002E")
        lf_tot = g("B23025_001E"); lf = g("B23025_002E"); clf = g("B23025_003E"); emp = g("B23025_004E")
        snap_u = g("B22010_001E"); snap = g("B22010_002E")
        cm_tot = g("B08303_001E"); short = sum((g(k) or 0) for k in ["B08303_002E", "B08303_003E", "B08303_004E", "B08303_005E"]); long_ = sum((g(k) or 0) for k in ["B08303_011E", "B08303_012E", "B08303_013E"])
        yb_tot = g("B25034_001E"); new = sum((g(k) or 0) for k in ["B25034_002E", "B25034_003E", "B25034_004E"]); old = sum((g(k) or 0) for k in ["B25034_007E", "B25034_008E", "B25034_009E", "B25034_010E", "B25034_011E"])
        ed_tot = g("B15003_001E"); ed = sum((g(k) or 0) for k in ["B15003_021E", "B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"])
        mv_r = ro; mv_old = g("B25038_015E")   # renter-occupied, moved in 1989 or earlier (2024 vintage numbering); renter total = B25003_003E
        col_u = g("B14007_001E"); col = (g("B14007_017E") or 0) + (g("B14007_018E") or 0)
        row = {"median_rent": rent, "median_home_value": val, "pop": pop, "renter_occupied": ro, "total_occupied": occ, "units_2": u2, "units_3_4": u34, "small_mf_units": u2 + u34, "renter_2_units": r2, "median_hh_income": inc,
               "rental_pct": (ro / occ) if occ else None, "rental_vacancy_pct": (vac / (ro + vac)) if (ro is not None and vac is not None and ro + vac) else None,
               "rent_burden_rate": (rb30 / ro) if ro else None, "severe_rent_burden_rate": (rb50 / ro) if ro else None,
               "poverty_rate": (pov / pov_u) if pov_u else None, "employment_rate": (emp / clf) if clf else None, "labor_force_participation": (lf / lf_tot) if lf_tot else None,
               "short_commute_rate": (short / cm_tot) if cm_tot else None, "long_commute_rate": (long_ / cm_tot) if cm_tot else None,
               "old_housing_rate": (old / yb_tot) if yb_tot else None, "new_housing_rate": (new / yb_tot) if yb_tot else None,
               "snap_rate": (snap / snap_u) if snap_u else None, "education_share": (ed / ed_tot) if ed_tot else None,
               "renter_stability_rate": (mv_old / mv_r) if mv_r else None, "college_enrolled_share": (col / pop) if pop else None,   # undergraduate + graduate enrolment over total population (validated against the 2026-09-08 model)
               "cv_value": (valm / 1.645 / val * 100) if (val and valm is not None) else None, "cv_rent": (rentm / 1.645 / rent * 100) if (rent and rentm is not None) else None, "cv_income": (incm / 1.645 / inc * 100) if (inc and incm is not None) else None,
               "name": e.get("NAME"), "_rb_nc": rb_nc, "_rb_tot": rb_tot}
        rows[geoid] = row
    return rows
def pct_rank(values_sorted, x, mode="mean"):
    lo = bisect.bisect_left(values_sorted, x); hi = bisect.bisect_right(values_sorted, x); n = len(values_sorted)
    if mode == "mean1": return (lo + 1 + hi) / 2 / n * 100   # pandas rank(method="average", pct=True): 1-based average rank over n (matches the 2026-09-08 model)
    if mode == "mean": return (lo + hi) / 2 / n * 100
    if mode == "max": return hi / n * 100
    if mode == "min": return (lo + 1) / n * 100
    if mode == "minus1": return lo / (n - 1) * 100 if n > 1 else 50
    return lo / n * 100
NORM = {"norm_cap_rate": ("cap_rate", 1), "norm_coc": ("coc_return", 1), "norm_grm": ("grm", -1), "norm_vacancy": ("rental_vacancy_pct", -1), "norm_rental_demand": ("rental_pct", 1), "norm_mf_stock": ("small_mf_units", 1)}
def score(rows, mult, ref=None, rp=(16.68502, 0.13905, -0.13831, 0.10432, 5.15, 22.5), qb=(1.57336, 0.00339, 0.06386, 0.02022, 0.04021, 2.65, 9.56), pmode="mean", mortgage=0.07, opex=0.40, months=24, down=0.25):
    # rp/qb: coefficients refit by least squares on the 2026-09-08 model's own rows (n = 4,495 / 4,291 unclipped tracts); 04b prints them rounded
    out = {}
    for geoid, r in rows.items():
        o = dict(r); rent = r["median_rent"]; val = r["median_home_value"]
        if not (rent and val): out[geoid] = o; continue
        ev = mult * val; gross = months * rent; noi = gross * (1 - opex); loan = ev * (1 - down); ds = pmt_annual(loan, mortgage); cf = noi - ds; dp = ev * down
        o.update({"est_duplex_value": ev, "annual_gross_rent": gross, "grm": ev / gross, "cap_rate": noi / ev * 100, "annual_cash_flow": cf, "coc_return": cf / dp * 100, "down_payment": dp, "rent_to_price": rent * 2 / ev * 100})
        def s(x, k=100): return x * k if x is not None else None
        o["tenant_payment_risk"] = 0.4 * s(r["rent_burden_rate"]) + 0.3 * s(r["severe_rent_burden_rate"]) + 0.3 * s(r["poverty_rate"]) if None not in (r["rent_burden_rate"], r["severe_rent_burden_rate"], r["poverty_rate"]) else None
        o["employment_stability"] = 0.6 * s(r["employment_rate"]) + 0.4 * s(r["labor_force_participation"]) if None not in (r["employment_rate"], r["labor_force_participation"]) else None
        o["commute_score"] = 40 + 0.6 * s(r["short_commute_rate"]) - 0.4 * s(r["long_commute_rate"]) if None not in (r["short_commute_rate"], r["long_commute_rate"]) else None
        o["housing_quality_score"] = 50 + 0.5 * s(r["new_housing_rate"]) - 0.5 * s(r["old_housing_rate"]) if None not in (r["new_housing_rate"], r["old_housing_rate"]) else None
        o["economic_fragility"] = s(r["snap_rate"]); o["education_score"] = s(r["education_share"])
        o["tenant_stability_score"] = min(100, 2 * s(r["renter_stability_rate"])) if r["renter_stability_rate"] is not None else None
        out[geoid] = o
    # percentiles
    scored = {g: o for g, o in out.items() if "coc_return" in o}
    refs = {}
    for nk, (mk, sign) in NORM.items():
        vals = ref[mk] if ref else sorted(o[mk] for o in out.values() if o.get(mk) is not None)   # universe = every tract carrying the metric, not only fully scorable ones (matches the 2026-09-08 model)
        refs[nk] = (vals, sign)
    for g, o in scored.items():
        for nk, (vals, sign) in refs.items():
            v = o.get(NORM[nk][0])
            if v is None or not vals: o[nk] = None; continue
            p = pct_rank(vals, v, pmode); o[nk] = p if sign > 0 else 100 - p
        if None in (o.get(k) for k in NORM): o["enhanced_score"] = None; o["gate"] = "NO DATA"; continue
        o["base_return_score"] = 0.25 * o["norm_cap_rate"] + 0.25 * o["norm_coc"] + 0.15 * o["norm_grm"] + 0.10 * o["norm_vacancy"] + 0.15 * o["norm_rental_demand"] + 0.10 * o["norm_mf_stock"]
        tpr, es, ef = o["tenant_payment_risk"], o["employment_stability"], o["economic_fragility"]
        hq, edu, ts, cm = o["housing_quality_score"], o["education_score"], o["tenant_stability_score"], o["commute_score"]
        if None in (tpr, es, ef, hq, edu, ts, cm): o["enhanced_score"] = None; o["gate"] = "NO DATA"; continue
        o["risk_penalty"] = min(rp[5], max(rp[4], rp[0] + rp[1] * tpr + rp[2] * es + rp[3] * ef))
        o["quality_bonus"] = min(qb[6], max(qb[5], qb[0] + qb[1] * hq + qb[2] * edu + qb[3] * ts + qb[4] * cm))
        o["enhanced_score"] = min(100, max(0, o["base_return_score"] - o["risk_penalty"] + o["quality_bonus"] + 15))
        margins = [(o["coc_return"] - 0), (o["enhanced_score"] - 50), (45 - tpr), (es - 55)]
        o["gate"] = "PASS" if all(m >= 0 for m in margins) else "FAIL"
        o["_margins"] = margins
    return out
if __name__ == "__main__":
    print("module; use validate_scorer.py")
