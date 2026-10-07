# build_regions.py - 2026-09-28. Scores the playbook regions' tracts with the rebuilt Gate-1 model and builds the per-region
# sweep queues. Inputs: tract_<st>_g1/g2/r2.json (ACS 2020-24 pulls), the NC/VA reference model (for the percentile universe),
# the 696-county screen, the repo's kept-county CSV, the ZCTA520<->tract20 relationship file and GeoNames US.txt.
import json, os, sys, csv, io, re, collections, statistics
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D); import score_tracts as ST
S = os.path.join(D, ".."); CAMP = os.path.join(S, "camp"); MODEL = os.path.join(CAMP, "_pipeline", "model"); OUT = os.path.join(S, "regions"); os.makedirs(OUT, exist_ok=True)
REPO = "/home/user/Investment-Outside-NC-VA"
HARD = 532643.0; PRACTICAL = 481443.0
# ---- regions: memo 63 section 7.2 order; areas keyed by the repo CSV's area strings
REGIONS = {
 "phila": {"day": "Tuesday", "areas": ["Philadelphia–Reading–Camden", "Scranton", "Bloomsburg", "Pottsville", "Binghamton", "Elmira"]},
 "pitt":  {"day": "Wednesday", "areas": ["Pittsburgh–Weirton", "Wheeling", "Fairmont", "Morgantown", "Parkersburg", "Charleston–Huntington", "Cumberland, MD", "Johnstown", "Youngstown"]},
 "ohio":  {"day": "Thursday", "areas": ["Cleveland–Akron", "Toledo", "Dayton"]},
}
STFIPS = {"PA": "42", "OH": "39", "NJ": "34", "DE": "10", "MD": "24", "WV": "54", "NY": "36", "KY": "21", "NC": "37", "VA": "51"}
# ---- kept counties per area from the repo CSV (redfin_2to4_unit_sales_by_county_189_areas_2026-05.csv)
rows = list(csv.DictReader(open(os.path.join(REPO, "redfin_2to4_unit_sales_by_county_189_areas_2026-05.csv"), encoding="utf-8-sig")))
screen = {r["﻿fips"] if "﻿fips" in r else r["fips"]: r for r in csv.DictReader(open(os.path.join(CAMP, "_pipeline", "area_projection", "county_screen_consistent_rules_2026-09-25.csv"), encoding="utf-8"))}
STNAME = {"PA": "Pennsylvania", "OH": "Ohio", "NJ": "New Jersey", "DE": "Delaware", "MD": "Maryland", "WV": "West Virginia", "NY": "New York", "KY": "Kentucky"}
# county name -> fips from the ACS tract names ("Census Tract 101; Lackawanna County; Pennsylvania"); the 696-county screen lacks some kept counties
name2fips = {}
for st in ["42", "39", "34", "10", "24", "54", "36", "21"]:
    g1 = json.load(open(os.path.join(D, f"tract_{st}_g1.json"))); h = g1[0]
    for r in g1[1:]:
        e = dict(zip(h, r)); parts = [p.strip() for p in e["NAME"].split(";")]
        if len(parts) >= 3: name2fips.setdefault(f"{parts[1]}, {parts[2]}", e["state"] + e["county"])
area_of = {}; county_meta = {}
for reg, spec in REGIONS.items():
    for a in spec["areas"]:
        for r in rows:
            if a in r["area"] and r["kept_by_rules"] == "yes":
                full = f"{r['county']}, {STNAME[r['state']]}"; fips = name2fips.get(full)
                if not fips: print("NO FIPS for", full); continue
                area_of[fips] = (reg, a, r["area"]); county_meta[fips] = {"name": r["county"], "st": r["state"], "sales": int(r["redfin_2to4_sales_12mo_to_2026-05"] or 0), "median": r["redfin_2to4_median_sale_price_wtd"], "area": r["area"]}
print("kept counties:", collections.Counter(v[0] for v in area_of.values()))
# ---- reference universe from NC/VA at each multiplier
ref_raw = {}; ref_raw.update(ST.load(D, "37")); ref_raw.update(ST.load(D, "51")); ref_rows = ST.build_rows(ref_raw)
def ref_lists(mult):
    sc = ST.score(ref_rows, mult); return {mk: sorted(o[mk] for o in sc.values() if o.get(mk) is not None) for mk in ["cap_rate", "coc_return", "grm", "rental_vacancy_pct", "rental_pct", "small_mf_units"]}
REF = {1.0: ref_lists(1.0), 1.25: ref_lists(1.25)}
# ---- new states
new_raw = {}
for st in ["42", "39", "34", "10", "24", "54", "36", "21"]: new_raw.update(ST.load(D, st))
new_rows = ST.build_rows(new_raw); print("new-state tracts pulled:", len(new_rows))
def gate_string(o):
    if o.get("enhanced_score") is None: return "no data"
    if o["coc_return"] <= 0: return "FAIL: not in positive-cash-flow set"
    fails = [n for n, m in zip(["enhanced score", "tenant payment risk", "employment stability"], o["_margins"][1:]) if m < 0]
    return "PASS" if not fails else "FAIL: " + ", ".join(fails)
def tier_num(o):
    if o.get("enhanced_score") is None: return None
    if o["coc_return"] <= 0: return 6
    m = min((o["enhanced_score"] - 50) / 50, (45 - o["tenant_payment_risk"]) / 45, (o["employment_stability"] - 55) / 55)
    return 1 if m >= 0.25 else 2 if m >= 0.10 else 3 if m >= 0 else 4 if m >= -0.10 else 5 if m >= -0.25 else 6
FIELDS = ["median_rent", "median_home_value", "pop", "renter_occupied", "total_occupied", "units_2", "units_3_4", "small_mf_units", "renter_2_units", "median_hh_income", "rental_pct", "rental_vacancy_pct", "est_duplex_value", "annual_gross_rent", "grm", "cap_rate", "annual_cash_flow", "coc_return", "down_payment", "rent_to_price", "rent_burden_rate", "severe_rent_burden_rate", "poverty_rate", "tenant_payment_risk", "employment_rate", "labor_force_participation", "employment_stability", "commute_score", "old_housing_rate", "new_housing_rate", "housing_quality_score", "snap_rate", "economic_fragility", "education_score", "renter_stability_rate", "tenant_stability_score", "college_enrolled_share", "cv_value", "cv_rent", "cv_income", "norm_cap_rate", "norm_coc", "norm_grm", "norm_vacancy", "norm_rental_demand", "norm_mf_stock", "base_return_score", "risk_penalty", "quality_bonus", "enhanced_score"]
scored = {}
for mult in (1.0, 1.25):
    sc = ST.score(new_rows, mult, ref=REF[mult]); out = {}
    for g, o in sc.items():
        if g[:5] not in area_of: continue
        e = {k: o.get(k) for k in FIELDS}; e["gate"] = gate_string(o); e["tier"] = tier_num(o); e["name"] = o.get("name"); out[g] = e
    scored[mult] = out
print("region tracts scored:", len(scored[1.0]), "| gate at 1.0x:", collections.Counter(v["gate"].split(":")[0] for v in scored[1.0].values()), "| tiers:", collections.Counter(str(v["tier"]) for v in scored[1.0].values()))
# ---- crosswalk (land share) and GeoNames
xw = collections.defaultdict(list)   # tract -> [(zcta, share)]
with open(os.path.join(S, "xwalk", "tab20_zcta520_tract20_natl.txt"), encoding="utf-8-sig") as f:
    rd = csv.DictReader(f, delimiter="|")
    for r in rd:
        t = r["GEOID_TRACT_20"]; z = r["GEOID_ZCTA5_20"]
        if not z or t[:5] not in area_of: continue
        land = float(r["AREALAND_TRACT_20"] or 0); part = float(r["AREALAND_PART"] or 0)
        if land > 0: xw[t].append((z, part / land))
geo = {}   # zip -> (place, st, county)
for line in open(os.path.join(MODEL, "US.txt"), encoding="utf-8"):
    p = line.rstrip("\n").split("\t")
    if len(p) > 5 and p[1] not in geo: geo[p[1]] = (p[2], p[4], p[5])
# ---- per-region tract files, watchlists, map_data rows, ZIP queues
county_ratio = {}
for fips, m in county_meta.items():
    stock = sum((v["small_mf_units"] or 0) for g, v in scored[1.0].items() if g[:5] == fips)   # Redfin 12-month 2-4-unit sales over the county's ACS duplex-type stock (NC/VA median 0.0028)
    county_ratio[fips] = (m["sales"] / stock) if stock > 0 else 0.0028
CLASS2CAT = {"within": "A", "borderline": "D", "ELIMINATED": "E", "LIKELY ELIMINATED": "E", "CLOSED": "E", "within (no duplex stock)": "J", "no data": "D"}
summary = {}
for reg, spec in REGIONS.items():
    t10 = {g: v for g, v in scored[1.0].items() if area_of[g[:5]][0] == reg}; t125 = {g: scored[1.25][g] for g in t10}
    json.dump(t10, open(os.path.join(OUT, f"tract_scores_{reg}_x1.0.json"), "w"), indent=0); json.dump(t125, open(os.path.join(OUT, f"tract_scores_{reg}_x1.25.json"), "w"), indent=0)
    wl = []
    for g, v in t10.items():
        units = v["small_mf_units"] or 0; letter = "F" if v["gate"] != "PASS" else ("P" if units >= 20 else "S")
        zs = sorted(xw.get(g, []), key=lambda x: -x[1]); zstr = "; ".join(f"{z} ({round(sh*100)}%)" for z, sh in zs if sh >= 0.005)
        cm = county_meta[g[:5]]
        wl.append({"geoid": g, "county": f"{cm['name']} {cm['st']}", "tract": (v["name"] or "").split(";")[0], "tier": letter, "duplex_type_units": int(units), "expected_sales_per_year": round(units * county_ratio[g[:5]], 2), "median_value": v["median_home_value"], "median_rent": v["median_rent"], "rent_to_price_at_1.0x": round(v["rent_to_price"], 2) if v.get("rent_to_price") else "", "coc_at_1.0x": round(v["coc_return"], 1) if v.get("coc_return") is not None else "", "tenant_payment_risk": round(v["tenant_payment_risk"], 1) if v.get("tenant_payment_risk") is not None else "", "employment_stability": round(v["employment_stability"], 1) if v.get("employment_stability") is not None else "", "enhanced_score": round(v["enhanced_score"], 1) if v.get("enhanced_score") is not None else "", "gate1": v["gate"], "tier_gate1": v["tier"] if v["tier"] is not None else "", "county_condition": "", "zips_by_land_share": zstr})
    wl.sort(key=lambda r: -r["duplex_type_units"])
    with open(os.path.join(OUT, f"tract_watchlist_{reg}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(wl[0].keys())); w.writeheader(); w.writerows(wl)
    md_rows = []
    for fips, cm in county_meta.items():
        if area_of[fips][0] != reg: continue
        s = screen.get(fips, {}); md_rows.append({"fips": fips, "name": cm["name"], "st": cm["st"], "cat": CLASS2CAT.get(s.get("class", ""), "D"), "sub": "", "ov": "", "price": int(float(s.get("est_duplex_price") or 0)), "basis": s.get("basis", ""), "sales": cm["sales"], "stock": int(float(s.get("two_to_four_unit_structures") or 0)), "r2p": s.get("rent_to_price_pct", ""), "cls": s.get("class", ""), "note": f"{cm['area']}; kept by the 9-26 rules; Redfin 2-4-unit median ${cm['median']}"})
    json.dump({"labels": {"A": "Active sweep", "B": "Shallow market", "C": "Thin market", "D": "Undecided or watch", "E": "Eliminated at the median", "F": "Dropped for now", "G": "Specialist market", "J": "No duplex stock"}, "rows": md_rows}, open(os.path.join(OUT, f"map_data_{reg}.json"), "w"), indent=1)
    # ZIP roll-up over PASS tracts at 1.0x with value at or under the hard ceiling
    zip_units = collections.defaultdict(float); zip_all = collections.defaultdict(float); zip_counties = collections.defaultdict(set); zip_area = collections.defaultdict(lambda: collections.defaultdict(float)); zip_val = collections.defaultdict(list)
    for g, v in t10.items():
        units = v["small_mf_units"] or 0
        for z, sh in xw.get(g, []):
            zip_all[z] += units * sh
            if v["gate"] == "PASS" and (v["median_home_value"] or 0) <= HARD:
                zip_units[z] += units * sh; zip_counties[z].add(county_meta[g[:5]]["name"] + " " + county_meta[g[:5]]["st"]); zip_area[z][area_of[g[:5]][1]] += units * sh
                if v["median_home_value"]: zip_val[z].append((v["median_home_value"], units * sh))
    cands = []
    for z, u in zip_units.items():
        if u < 20: continue
        area = max(zip_area[z].items(), key=lambda x: x[1])[0]; gz = geo.get(z)
        wv = sum(a * b for a, b in zip_val[z]) / max(1e-9, sum(b for a, b in zip_val[z])) if zip_val[z] else None
        cands.append({"zip": z, "state": gz[1] if gz else "", "place": gz[0] if gz else "", "counties": "; ".join(sorted(zip_counties[z])), "area": area, "passing_units": round(u), "all_units": round(zip_all[z]), "value_wtd": round(wv) if wv else None})
    cands.sort(key=lambda c: -c["passing_units"])
    # allocation: proportional to kept sales per area, floor 3, cap 100
    N = 100; area_sales = collections.Counter()
    for fips, cm in county_meta.items():
        if area_of[fips][0] == reg: area_sales[area_of[fips][1]] += cm["sales"]
    tot = sum(area_sales.values()); quota = {a: max(3, round(N * s / tot)) for a, s in area_sales.items()}
    chosen = []; per = collections.Counter()
    for c in cands:
        if per[c["area"]] < quota.get(c["area"], 3): chosen.append(c); per[c["area"]] += 1
    for c in cands:
        if len(chosen) >= N: break
        if c not in chosen: chosen.append(c)
    chosen = chosen[:N]
    def slug(place, st, z): return re.sub(r"[^a-z0-9]+", "-", place.lower()).strip("-") + f"-{st.lower()}-{z}"
    sz = [{"rank": i + 1, "zip": c["zip"], "state": c["state"], "counties": c["counties"], "area": c["area"], "set": "playbook", "units": str(c["passing_units"]), "all_units": str(c["all_units"]), "value_wtd": c["value_wtd"], "redfin": f"https://www.redfin.com/zipcode/{c['zip']}/filter/property-type=multifamily", "zillow": f"https://www.zillow.com/{slug(c['place'], c['state'], c['zip'])}/duplex/" if c["place"] else "", "zillow_source": "geonames-derived, unverified"} for i, c in enumerate(chosen)]
    json.dump(sz, open(os.path.join(OUT, f"sweep_zips_{reg}.json"), "w"), indent=1)
    summary[reg] = {"tracts": len(t10), "pass_1.0": sum(1 for v in t10.values() if v["gate"] == "PASS"), "zip_candidates": len(cands), "chosen": len(sz), "by_area": dict(per), "quota": quota, "top5": [(c["zip"], c["place"], c["passing_units"]) for c in chosen[:5]]}
print(json.dumps(summary, indent=1))
