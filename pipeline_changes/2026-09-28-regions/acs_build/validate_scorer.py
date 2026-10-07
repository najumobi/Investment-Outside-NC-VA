# validate_scorer.py - reproduce _pipeline/model/tract_scores_x1.0.json for NC/VA from a fresh ACS pull.
import json, sys, math, os
sys.path.insert(0, os.path.dirname(__file__)); import score_tracts as ST
D = os.path.dirname(os.path.abspath(__file__)); CAMP = os.path.join(D, "..", "camp", "_pipeline", "model")
ref = json.load(open(os.path.join(CAMP, "tract_scores_x1.0.json")))
raw = {}; raw.update(ST.load(D, "37")); raw.update(ST.load(D, "51"))
rows = ST.build_rows(raw)
common = [g for g in ref if g in rows]; print("ref tracts", len(ref), "pulled", len(rows), "common", len(common), "missing from pull", [g for g in ref if g not in rows][:5])
# 1. raw metric agreement
RAW = ["median_rent", "median_home_value", "pop", "renter_occupied", "total_occupied", "units_2", "units_3_4", "small_mf_units", "renter_2_units", "median_hh_income", "rental_pct", "rental_vacancy_pct", "rent_burden_rate", "severe_rent_burden_rate", "poverty_rate", "employment_rate", "labor_force_participation", "old_housing_rate", "new_housing_rate", "snap_rate", "renter_stability_rate", "college_enrolled_share", "cv_value", "cv_rent", "cv_income"]
for k in RAW:
    diffs = []; n = 0
    for g in common:
        a = ref[g].get(k); b = rows[g].get(k)
        if a is None and b is None: continue
        if a is None or b is None: n += 1; continue
        diffs.append(abs(a - b))
    print(f"  {k:26s} max|diff| {max(diffs) if diffs else 0:.6g}  n_compared {len(diffs)}  one-sided-None {n}")
# alt rent-burden denominator check
alt = []
for g in common:
    r = rows[g]; a = ref[g].get("rent_burden_rate")
    if a is None or not r["renter_occupied"]: continue
    alt.append(abs(a - r["rent_burden_rate"]))
print("  rent_burden alt(ro) max", max(alt))
# 2. scored fields at 1.0x, try percentile conventions
best = None
for pmode in ["mean1", "mean"]:
    sc = ST.score(rows, 1.0, ref=None, pmode=pmode)
    d = {k: [] for k in ["cap_rate", "coc_return", "grm", "annual_cash_flow", "tenant_payment_risk", "employment_stability", "commute_score", "housing_quality_score", "education_score", "tenant_stability_score", "norm_cap_rate", "norm_coc", "norm_grm", "norm_vacancy", "norm_rental_demand", "norm_mf_stock", "base_return_score", "risk_penalty", "quality_bonus", "enhanced_score"]}
    gate_ok = 0; gate_n = 0
    for g in common:
        for k in d:
            a = ref[g].get(k); b = sc[g].get(k)
            if a is not None and b is not None: d[k].append(abs(a - b))
        if ref[g].get("gate") in ("PASS", "FAIL") and sc[g].get("gate") in ("PASS", "FAIL"): gate_n += 1; gate_ok += (ref[g]["gate"] == sc[g]["gate"])
    summary = {k: (round(max(v), 4) if v else None) for k, v in d.items()}
    print(f"pmode={pmode}: norm maxdiff cap {summary['norm_cap_rate']} vac {summary['norm_vacancy']} demand {summary['norm_rental_demand']} stock {summary['norm_mf_stock']} | enhanced {summary['enhanced_score']} | gate agree {gate_ok}/{gate_n}")
    if pmode == "mean1": print("   detail:", summary)
# college share alternative denominators (descriptive field only): B14007_001 (pop 3+) vs B01003 (total pop)
r2 = {}
for st in ["37", "51"]:
    d = json.load(open(os.path.join(D, f"tract_{st}_r2.json"))); h = d[0]
    for r in d[1:]:
        e = dict(zip(h, r)); r2[e["state"] + e["county"] + e["tract"]] = e
alt1 = []; alt2 = []
for g in common:
    a = ref[g].get("college_enrolled_share"); e = r2.get(g); rr = raw.get(g)
    if a is None or not e or not rr: continue
    col = (ST.f(rr.get("B14007_017E")) or 0) + (ST.f(rr.get("B14007_018E")) or 0); pop = ST.f(e["B01003_001E"]); u = ST.f(e["B14007_001E"])
    if pop: alt1.append(abs(a - col / pop))
    if u: alt2.append(abs(a - col / u))
print("college share: max|diff| vs col/pop", max(alt1), "| vs col/B14007_001", max(alt2))
alt3 = [abs(ref[g]["renter_2_units"] - ST.f(r2[g]["B25032_016E"])) for g in common if g in r2 and ref[g].get("renter_2_units") is not None and ST.f(r2[g]["B25032_016E"]) is not None]
print("renter_2_units vs B25032_016E max|diff|", max(alt3))
# 3. refit risk_penalty and quality_bonus on the reference JSON (unclipped interior rows), least squares
import itertools
def lstsq(X, y):
    # pure-Python normal equations (X'X) c = X'y, Gauss-Jordan
    k = len(X[0]); A = [[sum(X[i][a] * X[i][b] for i in range(len(X))) for b in range(k)] + [sum(X[i][a] * y[i] for i in range(len(X)))] for a in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(A[r][c])); A[c], A[p] = A[p], A[c]; pv = A[c][c]
        A[c] = [v / pv for v in A[c]]
        for r in range(k):
            if r != c: A[r] = [rv - A[r][c] * cv for rv, cv in zip(A[r], A[c])]
    return [A[i][k] for i in range(k)]
try:
    X = []; y = []
    for g in common:
        r = ref[g]
        if r.get("risk_penalty") is None: continue
        if 5.2 < r["risk_penalty"] < 22.4: X.append([1, r["tenant_payment_risk"], r["employment_stability"], r["economic_fragility"]]); y.append(r["risk_penalty"])
    c = lstsq(X, y); print("risk_penalty refit:", [round(x, 6) for x in c], "n", len(y))
    X = []; y = []
    for g in common:
        r = ref[g]
        if r.get("quality_bonus") is None: continue
        if 2.7 < r["quality_bonus"] < 9.5: X.append([1, r["housing_quality_score"], r["education_score"], r["tenant_stability_score"], r["commute_score"]]); y.append(r["quality_bonus"])
    c = lstsq(X, y); print("quality_bonus refit:", [round(x, 6) for x in c], "n", len(y))
    rp = [r["risk_penalty"] for r in ref.values() if r.get("risk_penalty") is not None]; qb = [r["quality_bonus"] for r in ref.values() if r.get("quality_bonus") is not None]
    print("risk_penalty min/max", min(rp), max(rp), "| quality_bonus min/max", min(qb), max(qb))
except Exception as ex: print("refit skipped:", ex)
# 4. tiers in the reference
import collections; print("ref tiers:", collections.Counter(str(r.get("tier")) for r in ref.values()), "gates:", collections.Counter(str(r.get("gate")) for r in ref.values()))
