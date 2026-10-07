# edit_sweep_zips_1004.py - memo 72 phase B2 (desktop session, 2026-10-04). Reproduces the `cands` ranking of
#   pipeline_changes/2026-09-28-regions/acs_build/build_regions.py (fetched from the repository's pull-request branch on 2026-10-04): for each
#   tract of the region's model (tract_scores_<region>_x1.0.json) that passes Gate 1 at 1.0x with a median value at or under the hard ceiling,
#   its small multifamily stock (ACS 2-unit and 3-4-unit structures) is allocated to 2020 ZCTAs by land share from the Census ZCTA520-tract20
#   relationship file; a ZCTA with 20 or more passing units is a candidate, ranked by that figure. For NC/VA the same roll-up runs on the Monday
#   list's model (tract_scores_x1.0.json, every NC and VA tract), restricted to the campaign's queue (file 06d: active and shallow sets, excluded
#   ZIPs out), which is memo 64 section 2's rule on the Monday model. Stages:
#     cands   - validates the roll-up against the stock figures of the three regional lists, then prints the drops of file 72c and the
#               replacements (the first candidates not already in the list, in candidate order) and writes zip_edits_1004.json beside this script
#     apply   - edits the four lists in place (each replacement takes the slot and rank of the ZIP it replaces), after
#               _backup_sweep_zips_<region>_before_1004.json is written; asserts 100 entries, distinct five-digit ZIPs, consecutive ranks;
#               a replacement whose Zillow slug has not been verified on the page title is refused (zip_edits_1004.json carries the verification)
import csv, json, os, re, sys, collections
CAMP = "C:/Users/najum/Dropbox/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign/"
PIPE = CAMP + "_pipeline/"; MODEL = PIPE + "model/"
XW = "C:/Users/najum/AppData/Local/Temp/claude/C--Users-najum-Dropbox-linked-FAMILY/be6f292d-b132-47c0-b858-b8dc25bb2878/scratchpad/tab20_zcta520_tract20_natl.txt"
F72C = CAMP + "72c Sweep ZIPs by share of listings in Robbery-F block groups (2026-10-04).csv"
EDITS = PIPE + "zip_edits_1004.json"
HARD = 532643.0
LISTS = {"ncva": "sweep_zips.json", "phila": "sweep_zips_phila.json", "pitt": "sweep_zips_pitt.json", "ohio": "sweep_zips_ohio.json"}
TS = {"ncva": "model/tract_scores_x1.0.json", "phila": "model/tract_scores_phila_x1.0.json", "pitt": "model/tract_scores_pitt_x1.0.json", "ohio": "model/tract_scores_ohio_x1.0.json"}
stage = sys.argv[1] if len(sys.argv) > 1 else "cands"
def jl(fn): return json.load(open(fn, encoding="utf-8"))

if stage == "cands":
    xw = collections.defaultdict(list)
    with open(XW, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter="|"):
            t = r["GEOID_TRACT_20"]; z = r["GEOID_ZCTA5_20"]
            if not z or t[:2] not in ("37", "51", "42", "39", "34", "10", "24", "54", "36", "21"): continue
            land = float(r["AREALAND_TRACT_20"] or 0); part = float(r["AREALAND_PART"] or 0)
            if land > 0: xw[t].append((z, part / land))
    geo = {}
    for line in open(MODEL + "US.txt", encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) > 5 and p[1] not in geo: geo[p[1]] = (p[2], p[4], p[5])
    cb = jl(MODEL + "crime_bg.json")["bg"]; bg_by_tract = collections.Counter(k[:11] for k in cb)
    c72 = list(csv.DictReader(open(F72C, encoding="utf-8-sig")))
    q06d = {r["zip"]: r for r in csv.DictReader(open(CAMP + "06d ZIP sweep queue, active and shallow sets (2026-09-09).csv", encoding="utf-8"))}
    tally = {r["zip"]: r for r in csv.DictReader(open(CAMP + "12 ZIP sweep tally, rounds 1-14 COMPLETE (2026-09-12).csv", encoding="utf-8"))}
    edits = {}
    for reg, lf in LISTS.items():
        t10 = jl(PIPE + TS[reg]); lst = jl(PIPE + lf); inlist = {z["zip"] for z in lst}
        area_of = {}
        if reg != "ncva":
            for r in jl(PIPE + f"model/map_data_{reg}.json")["rows"]: area_of[r["fips"]] = (r["note"].split(";")[0], r["name"] + " " + r["st"])
        else:
            for r in jl(MODEL + "map_data.json")["rows"]: area_of[r["fips"]] = ("", r["name"] + " " + r["st"])
        zu = collections.defaultdict(float); za = collections.defaultdict(float); zc = collections.defaultdict(set); zar = collections.defaultdict(lambda: collections.defaultdict(float)); zv = collections.defaultdict(list); ztr = collections.defaultdict(set)
        for g, v in t10.items():
            units = v.get("small_mf_units") or 0
            for z, sh in xw.get(g, []):
                za[z] += units * sh; ztr[z].add(g)
                if v.get("gate") == "PASS" and (v.get("median_home_value") or 0) <= HARD:
                    zu[z] += units * sh; zc[z].add(area_of.get(g[:5], ("", ""))[1]); zar[z][area_of.get(g[:5], ("", ""))[0]] += units * sh
                    if v.get("median_home_value"): zv[z].append((v["median_home_value"], units * sh))
        cands = []
        for z, u in zu.items():
            if u < 20: continue
            gz = geo.get(z); wv = sum(a * b for a, b in zv[z]) / max(1e-9, sum(b for a, b in zv[z])) if zv[z] else None
            cands.append({"zip": z, "state": gz[1] if gz else "", "place": gz[0] if gz else "", "counties": "; ".join(sorted(c for c in zc[z] if c)), "area": max(zar[z].items(), key=lambda x: x[1])[0], "passing_units": round(u), "all_units": round(za[z]), "value_wtd": round(wv) if wv else None, "bg_read": sum(bg_by_tract[t] for t in ztr[z])})
        cands.sort(key=lambda c: -c["passing_units"])
        if reg != "ncva":   # validation: every list entry's units and all_units must reproduce
            by = {c["zip"]: c for c in cands}; bad = [(z["zip"], z["units"], by.get(z["zip"], {}).get("passing_units"), z["all_units"], by.get(z["zip"], {}).get("all_units")) for z in lst if by.get(z["zip"], {}).get("passing_units") != int(z["units"]) or by.get(z["zip"], {}).get("all_units") != int(z["all_units"])]
            print(f"{reg}: {len(cands)} candidates; list stock figures reproduced for {100 - len(bad)} of 100 entries" + (f"; MISMATCH {bad[:5]}" if bad else ""))
            assert not bad, "the roll-up does not reproduce the list; stop"
            pool = [c for c in cands if c["zip"] not in inlist]
        else:
            by = {c["zip"]: c for c in cands}
            cmp = [(z["zip"], int(z["units"] or 0), by.get(z["zip"], {}).get("passing_units")) for z in lst]
            close = sum(1 for z, a, b in cmp if b is not None and abs(a - b) <= max(5, 0.1 * a))
            print(f"ncva: {len(cands)} NC/VA ZCTAs with 20+ passing units on the Monday model; 06d's weighted units agree within 10% for {close} of 100 list entries (06d was built 2026-09-09 on the same model's gate)")
            pool = [c for c in cands if c["zip"] not in inlist and c["zip"] in q06d and not q06d[c["zip"]]["status"].startswith("excluded")]
        drops = [r for r in c72 if r["region"] == reg and r["decision"].startswith("drop")]
        repl = pool[:len(drops)]
        print(f"  drops {len(drops)}: " + ", ".join(f"{r['zip']} (rank {r['rank']}; {r['decision'].split(' (')[0]}{', decision 2' if 'decision 2' in r['decision'] else ', zero rows'})" for r in drops))
        print(f"  replacements, in candidate order: " + ", ".join(f"{c['zip']} {c['place']} {c['state']} ({c['passing_units']} passing / {c['all_units']} all; {c['bg_read']} block groups read)" for c in repl))
        slug = lambda c: re.sub(r"[^a-z0-9]+", "-", c["place"].lower()).strip("-") + f"-{c['state'].lower()}-{c['zip']}"
        edits[reg] = {"drops": [{"zip": r["zip"], "rank": int(r["rank"]), "reason": r["decision"]} for r in drops], "replacements": [dict(c, zillow=f"https://www.zillow.com/{slug(c)}/duplex/", verified="", set=(q06d[c["zip"]]["set"] if reg == "ncva" else "playbook"), listings_last_sweep=(int(tally.get(c["zip"], {}).get("listings_found_redfin") or 0) if reg == "ncva" else None), units_06d=(q06d[c["zip"]]["weighted_duplex_units"] if reg == "ncva" else None)) for c in repl]}
    json.dump(edits, open(EDITS, "w", encoding="utf-8"), indent=1); print("wrote", EDITS)

if stage == "apply":
    edits = jl(EDITS)
    for reg, lf in LISTS.items():
        e = edits[reg]
        if not e["drops"]: print(f"{reg}: nothing to change"); continue
        fn = PIPE + lf; bk = PIPE + f"_backup_sweep_zips_{reg}_before_1004.json"
        if not os.path.exists(bk): open(bk, "wb").write(open(fn, "rb").read())
        lst = jl(fn); keys = list(lst[0].keys()); by_rank = {z["rank"]: z for z in lst}
        assert len(e["drops"]) == len(e["replacements"]), reg
        for d, c in zip(e["drops"], e["replacements"]):
            assert c["verified"].startswith("verified"), f"{reg} {c['zip']}: Zillow slug not verified; refusing"
            old = by_rank[d["rank"]]; assert old["zip"] == d["zip"], (reg, d, old["zip"])
            new = {k: "" for k in keys}; new.update({"rank": d["rank"], "zip": c["zip"], "state": c["state"], "counties": c["counties"], "redfin": f"https://www.redfin.com/zipcode/{c['zip']}/filter/property-type=multifamily", "zillow": c["zillow"], "zillow_source": c["verified"] + f"; added 2026-10-04 in place of {d['zip']} (memo 72 phase B2: {d['reason'].split(' (')[0]}, {'decision 2' if 'decision 2' in d['reason'] else 'standing rule, no listing on the last two runs'})"})
            if reg == "ncva": new.update({"set": c["set"], "listings_last_sweep": c["listings_last_sweep"], "units": c["units_06d"]})
            else: new.update({"area": c["area"], "set": "playbook", "units": str(c["passing_units"]), "all_units": str(c["all_units"]), "value_wtd": c["value_wtd"]})
            lst[lst.index(old)] = new
        json.dump(lst, open(fn, "w", encoding="utf-8"), indent=1)
        chk = jl(fn); zips = [z["zip"] for z in chk]
        assert len(chk) == 100 and len(set(zips)) == 100 and all(re.fullmatch(r"\d{5}", z) for z in zips) and [z["rank"] for z in chk] == list(range(1, 101)) and all(list(z.keys()) == keys for z in chk), reg
        print(f"{reg}: {len(e['drops'])} ZIPs replaced; {lf} holds 100 entries, distinct five-digit ZIPs, ranks 1 to 100, same keys; backup {os.path.basename(bk)}")
