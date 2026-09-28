# weekly_sweep.py - local orchestrator for the weekly duplex re-sweep (written 2026-09-14).
# Stages, in order (the desktop task runs them; sweep_remote.py does the fetching in the Composio sandbox):
#   plan       -> creates _sweeps/<date>/, writes tracked_urls.json (file 14 rows to refresh) and prints what the remote must fetch
#   ingest     -> needs listings_raw.csv + fetch_counts.json (uploaded by the remote): seen-index diff, geocode, tract gates, knockouts, shortlist, detail_plan.json
#   prep       -> needs details.json (remote): merges facts, downloads front photos to photos/, prints the facts table and the judgments.json template
#   underwrite -> needs judgments.json (written by the task after viewing photos): verdicts, results.csv, folds ENTRANT/NEAR-MISS rows into file 14 as UNREVIEWED
#   refresh    -> needs tracked.json (remote): updates file 14 status/price/event for tracked rows, writes tracked_changes.csv
#   report     -> assembles report.md from the pieces
#   wait <file> -> polls the run folder for a Dropbox-synced file (up to 4 minutes)
# Every stage is idempotent; re-running overwrites its own outputs only.
# 2026-09-28: --region=ncva|phila|pitt|ohio selects the ZIP list, tract model and run folder (constants.json "regions"); the distance
#   penalty is re-specified as memo 63 section 7.1 says: Gate 5 bar = 0.90% + tier shift, tier costs in NOI, at most -0.5 in the score;
#   taxes carry the rental_tax_adjust block; drive hours and tax rates resolve by ZIP before city and state.
import csv, json, io, re, os, sys, uuid, time, datetime, urllib.request, glob
CAMP = "C:/Users/najum/Dropbox/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign/"
PIPE = CAMP + "_pipeline/"; MODEL = PIPE + "model/"; SWEEPS = CAMP + "_sweeps/"
F14 = CAMP + "14 Live status and ranking of the 42 tracked candidates (2026-09-11).csv"
sys.path.insert(0, PIPE); from parsers import key
C = json.load(open(PIPE + "constants.json", encoding="utf-8"))
args = [a for a in sys.argv[1:] if not a.startswith("--")]; opts = {a.split("=")[0][2:]: (a.split("=", 1)[1] if "=" in a else True) for a in sys.argv[1:] if a.startswith("--")}
DATE = opts.get("date") or datetime.date.today().isoformat()
REGION = opts.get("region") or "ncva"; RC = C.get("regions", {}).get(REGION)
if REGION != "ncva" and not RC: sys.exit(f"unknown region {REGION}: constants.json regions has {list(C.get('regions', {}).keys())}")
RC = RC or {"zips": "sweep_zips.json", "tract_scores_x1.0": "model/tract_scores_x1.0.json", "tract_scores_x1.25": "model/tract_scores_x1.25.json", "watchlists": ["model/active_tract_watchlist.csv", "model/shallow_tract_watchlist.csv"], "map_data": "model/map_data.json", "run_folder_suffix": ""}
RUN = SWEEPS + DATE + RC.get("run_folder_suffix", "") + "/"; os.makedirs(RUN, exist_ok=True)
ZFILE = PIPE + RC["zips"]
stage = args[0] if args else "help"
def num(x):
    try: return float(str(x).replace(",", "").replace("$", ""))
    except: return None
def pmt(loan, rate): r = rate / 12; return loan * r / (1 - (1 + r) ** -360) * 12
def rd(fn): return list(csv.DictReader(open(fn, encoding="utf-8")))
def wr(fn, rows, fields=None):
    fields = fields or list(rows[0].keys()) if rows else (fields or ["empty"])
    with open(fn, "w", newline="", encoding="utf-8") as f: w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
def jl(fn): return json.load(open(fn, encoding="utf-8"))
def js(fn, obj): json.dump(obj, open(fn, "w", encoding="utf-8"), indent=1)
def akey(a):
    m = re.search(r"(\d{5})\s*$", a.strip()); return key(a) + "|" + (m.group(1) if m else "")
def note(line):
    with open(RUN + "report_parts.txt", "a", encoding="utf-8") as f: f.write(line.rstrip() + "\n")
    print(line)

if stage == "wait":
    target = RUN + args[1]; t = time.time()
    while not os.path.exists(target) and time.time() - t < 240: time.sleep(10)
    print("found" if os.path.exists(target) else "MISSING after 240 s:", target); sys.exit(0 if os.path.exists(target) else 2)

if stage == "plan":
    rows = rd(F14); tracked = []
    for r in rows:
        s = r["status"].upper()
        if s.startswith(("OUT", "SOLD", "WITHDRAWN", "OFF MARKET", "EXPIRED")): continue
        if "redfin.com" in r["url"] or "zillow.com" in r["url"]: tracked.append({"address": r["address"], "url": r["url"], "status": r["status"], "price": r["price"]})
    js(RUN + "tracked_urls.json", tracked)
    zips = jl(ZFILE)
    open(RUN + "report_parts.txt", "w", encoding="utf-8").write(f"# Weekly sweep {DATE} ({REGION})\n")
    print(f"run folder {RUN}\nregion {REGION}: list pages to fetch: {sum(1 + (1 if z.get('zillow') else 0) for z in zips)} across {len(zips)} ZIPs ({RC['zips']})\ntracked rows to refresh: {len(tracked)} (tracked_urls.json)")
    print(f"NEXT: in the workbench run remote_setup(DATE, '{REGION}'); remote_fetch_lists(0..4); remote_parse_lists(); then locally: weekly_sweep.py wait listings_raw.csv --region={REGION} && weekly_sweep.py ingest --region={REGION}")

if stage == "ingest":
    raw = rd(RUN + "listings_raw.csv"); health = jl(RUN + "fetch_counts.json") if os.path.exists(RUN + "fetch_counts.json") else {"counts": {}, "bad": []}
    idx = {r["key"]: r for r in rd(PIPE + "seen_index.csv")}; fields_idx = list(next(iter(idx.values())).keys())
    present = set(); deltas = {}
    for r in raw:
        k = akey(r["address"]); present.add(k); p = str(int(num(r["price"]))) if num(r["price"]) else ""
        if k not in idx:
            idx[k] = {"key": k, "address": r["address"], "zip": k.split("|")[1], "first_seen": DATE, "last_seen": DATE, "price_first": p, "price_last": p, "source": r["source"], "url": r["url"], "status": "listed", "gone_date": "", "note": f"weekly sweep {DATE}"}; deltas[k] = "new"
        else:
            e = idx[k]; old = num(e["price_last"]); new = num(p)
            if e["status"] == "gone": deltas[k] = "relisted"; e["status"] = "listed"; e["gone_date"] = ""
            elif old and new and new < old - 0.5: deltas[k] = f"price cut {old:,.0f}->{new:,.0f}"
            elif old and new and new > old + 0.5: deltas[k] = f"price up {old:,.0f}->{new:,.0f}"
            else: deltas[k] = "unchanged"
            e["last_seen"] = DATE
            if p: e["price_last"] = p
            if not e.get("url") and r["url"]: e["url"] = r["url"]
    cnt = health.get("counts", {}); ok_zips = {z for z, c in cnt.items() if c.get("redfin") is not None and c.get("zillow") is not None}
    gone = []
    for k, e in idx.items():
        if e["status"] == "listed" and e["zip"] in ok_zips and k not in present: e["status"] = "gone"; e["gone_date"] = DATE; gone.append(e["address"])
    wr(PIPE + "seen_index.csv", list(idx.values()), fields_idx)
    # geocode + tract gates + knockouts for every row present (cache makes the old ones free)
    cache_fn = MODEL + "geo_cache.json"; cache = jl(cache_fn) if os.path.exists(cache_fn) else {}
    def clean_street(a):
        parts = [x.strip() for x in a.split(",")]; st = re.sub(r"\s+(Unit|Apt|#|Lot).*$", "", parts[0], flags=re.I); st = re.sub(r"^(\d+)\s*[-&/]\s*\d+\s", r"\1 ", st); return st, parts
    buf = io.StringIO(); w = csv.writer(buf); need = []
    for i, r in enumerate(raw):
        if r["address"] in cache: continue
        st, parts = clean_street(r["address"])
        if len(parts) < 3: continue
        stz = parts[-1].split(); w.writerow([i, st, parts[-2], stz[0], stz[-1]]); need.append(i)
    if need:
        b = uuid.uuid4().hex
        body = ("--%s\r\nContent-Disposition: form-data; name=\"addressFile\"; filename=\"a.csv\"\r\nContent-Type: text/csv\r\n\r\n%s\r\n--%s\r\nContent-Disposition: form-data; name=\"benchmark\"\r\n\r\nPublic_AR_Current\r\n--%s\r\nContent-Disposition: form-data; name=\"vintage\"\r\n\r\nCurrent_Current\r\n--%s--\r\n" % (b, buf.getvalue(), b, b, b)).encode()
        req = urllib.request.Request("https://geocoding.geo.census.gov/geocoder/geographies/addressbatch", data=body, headers={"Content-Type": "multipart/form-data; boundary=" + b, "User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=600) as resp: out = resp.read().decode("utf-8", "replace")
            for rec in csv.reader(io.StringIO(out)):
                if len(rec) >= 12 and rec[2] == "Match": cache[raw[int(rec[0])]["address"]] = rec[8] + rec[9] + rec[10]
            js(cache_fn, cache)
        except Exception as ex: note(f"geocoder failed: {ex}")
    S10 = jl(PIPE + RC["tract_scores_x1.0"]); S125 = jl(PIPE + RC["tract_scores_x1.25"]); md = jl(PIPE + RC["map_data"])["rows"]
    cat = {r["fips"]: r["cat"] for r in md}; names = {r["fips"]: r["name"] + " " + r["st"] for r in md}; tiers = {}
    for fn in RC["watchlists"]:
        for rr in rd(PIPE + fn): tiers[rr["geoid"]] = rr["tier"]
    scored = []; shortlist = []
    for r in raw:
        k = akey(r["address"]); g = cache.get(r["address"]); d = S10.get(g, {}) if g else {}; d125 = S125.get(g, {}) if g else {}; fips = g[:5] if g else None
        p = num(r["price"]); beds = num(r["beds"]); ut = num(r["units_text"]); units = int(ut) if ut else (2 if (beds and beds <= 6) else None)
        med = d.get("median_rent"); rent_stated = num(r["rent_text"]); rent = rent_stated or ((units or 2) * med if med else None)
        rec = dict(r); rec.update({"delta": deltas.get(k, ""), "tract": g or "", "county": names.get(fips, ""), "county_category": cat.get(fips, ""), "tract_tier": tiers.get(g, "") if g else "", "gate1_x1.0": d.get("gate", ""), "gate1_x1.25": d125.get("gate", ""), "tract_median_rent": med, "units_assumed": units, "rent_used": rent, "rent_basis": "listing text" if rent_stated else "tract median x units"})
        rec["rent_to_price_pct"] = round(rent * 100 / p, 2) if (p and rent) else ""
        ko = []
        if r.get("land") == "True": ko.append("land")
        if not p: ko.append("no price")
        elif p > C["hard_ceiling"]: ko.append("above hard ceiling")
        if units and units != 2: ko.append("%d units, not a duplex" % units)
        if not g: ko.append("not geocoded")
        if g and d.get("gate") and d["gate"] != "PASS": ko.append("tract fails Gate 1 at x1.0")
        if rec["rent_to_price_pct"] != "" and rec["rent_to_price_pct"] < 0.9: ko.append("rent-to-price under 0.9%")
        rec["knockouts"] = "; ".join(ko)
        fresh = rec["delta"] in ("new", "relisted") or rec["delta"].startswith("price cut")
        rec["shortlist"] = "YES" if (fresh and not ko and p and p <= C["practical_ceiling"]) else ""
        scored.append(rec)
        if rec["shortlist"]: shortlist.append(rec)
    keys = []
    for o in scored:
        for kk in o.keys():
            if kk not in keys: keys.append(kk)
    wr(RUN + "scored.csv", scored, keys)
    js(RUN + "detail_plan.json", [{"address": s["address"], "url": s["url"], "zurl": s.get("zurl", "")} for s in shortlist])
    dl = {}
    for v in deltas.values(): dl[v.split(" ")[0]] = dl.get(v.split(" ")[0], 0) + 1
    note(f"## Fetch health\n{health.get('fetched_ok','?')}/{health.get('pages','?')} list pages ok; bad pages: {len(health.get('bad', []))}; ZIPs with both portals ok: {len(ok_zips)}/{len(cnt)}; listings this week: {len(raw)}")
    note(f"## Listings\nnew {dl.get('new',0)}, relisted {dl.get('relisted',0)}, price cuts {dl.get('price',0)}, unchanged {dl.get('unchanged',0)}, off the list pages since last sweep {len(gone)} (pending, sold, withdrawn, or pushed past page 1; tracked rows get the truth from their detail pages)")
    for g_ in gone[:40]: note(f"  off list: {g_}")
    for r in scored:
        if r["delta"] in ("new", "relisted") or r["delta"].startswith("price cut"): note(f"  {r['delta'][:24]:24s} | {r['address'][:46]:46s} | ${r['price']} | {r['beds']}bd {r['sqft']}sf | tier {r['tract_tier']} {r['gate1_x1.0'][:4]} | r2p {r['rent_to_price_pct']} | {r['knockouts'] or 'SHORTLIST'}")
    note(f"## Shortlist ({len(shortlist)} rows need detail pages)")
    print(f"\nNEXT: {len(shortlist)} detail URLs in detail_plan.json; in the workbench run remote_details(<urls>, 'details') and remote_details(<tracked urls>, 'tracked'); then locally: wait details.json && prep")

if stage == "prep":
    det = jl(RUN + "details.json") if os.path.exists(RUN + "details.json") else {}; plan = jl(RUN + "detail_plan.json"); scored = {akey(r["address"]): r for r in rd(RUN + "scored.csv")}
    os.makedirs(RUN + "photos", exist_ok=True); facts = {}; tmpl = {}
    for p in plan:
        d = det.get(p["url"]) or det.get(p.get("zurl", "")) or {}; k = akey(p["address"]); s = scored.get(k, {}); street = p["address"].split(",")[0]
        photo = d.get("photo", ""); local = ""
        if photo:
            local = RUN + "photos/" + re.sub(r"[^A-Za-z0-9]+", "_", street)[:40] + ".jpg"
            try:
                if not os.path.exists(local):
                    req = urllib.request.Request(photo, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.redfin.com/"}); open(local, "wb").write(urllib.request.urlopen(req, timeout=60).read())
            except Exception as ex: local = f"(photo download failed: {ex})"
        facts[street] = {"address": p["address"], "price": s.get("price"), "built": d.get("built"), "dom": d.get("dom"), "status": d.get("status"), "history": d.get("history", ""), "flood": d.get("flood"), "tax_annual": d.get("tax_annual"), "mls": d.get("mls", ""), "listed_by": d.get("listed_by", ""), "zoning_line": (d.get("zoning_line") or "")[:120], "unit_rent_text": d.get("unit_rent_text", ""), "remarks": (d.get("remarks") or d.get("excerpt") or "")[:900], "tract_tier": s.get("tract_tier"), "tract_median_rent": s.get("tract_median_rent"), "rent_to_price_pct": s.get("rent_to_price_pct"), "beds": s.get("beds"), "sqft": s.get("sqft"), "photo_url": photo, "photo_local": local, "url": p["url"]}
        tmpl[street] = {"grade": "GREEN|GREEN-verify|YELLOW|RED|OUT", "c": "C1..C6 from the front photo", "units": 2, "units_txt": "one line: what the building is per remarks and photos", "rents": None, "cond": "one line: why this grade; RED items per file 08", "pnote": "one line photo note", "flood": d.get("flood"), "built": d.get("built"), "dom": d.get("dom"), "status": d.get("status"), "last_sold": ""}
    js(RUN + "facts.json", facts); js(RUN + "judgments_template.json", tmpl)
    for street, f in facts.items():
        print(f"\n=== {f['address']} | ${f['price']} | built {f['built']} | dom {f['dom']} | {f['status']} | flood {f['flood']} | tax {f['tax_annual']} | tier {f['tract_tier']} med {f['tract_median_rent']} r2p {f['rent_to_price_pct']}\n  photo: {f['photo_local']}\n  history: {f['history'][:160]}\n  rent text: {f['unit_rent_text']}\n  remarks: {f['remarks'][:500]}")
    print(f"\nNEXT: view each photo with Read, then write judgments.json (copy judgments_template.json, fill grade/c/units/units_txt/rents/cond/pnote), then: underwrite")

if stage == "underwrite":
    facts = jl(RUN + "facts.json"); J = jl(RUN + "judgments.json") if os.path.exists(RUN + "judgments.json") else {}
    dry = opts.get("dry", False); out = []; unknown = set()
    def crime_for(city, z):
        return C["crime"].get(city) or C["crime_zip"].get(z, "")
    def crime_pen(g):
        g = g.split(" ")[0] if g else ""; return {"F": 3, "D-": 2, "D": 1, "D+": 0.5}.get(g, 0)
    ORDER = {"ENTRANT": 0, "NEAR-MISS": 1, "OUT (negative cash flow)": 2, "OUT (RED)": 3, "OUT": 4}
    for street, f in facts.items():
        j = J.get(street)
        if not j: note(f"  no judgment for {street}; skipped"); continue
        parts = [p.strip() for p in f["address"].split(",")]; city = parts[1] if len(parts) > 2 else ""; st = parts[-1].split()[0] if parts else ""; z = f["address"][-5:]
        price = num(f["price"]); med = num(f["tract_median_rent"]); rent = num(j.get("rents")) or (2 * med if med else None)
        # tax rate: street, city, ZIP (county owner rate, 2026-09-28), then the state default; NC keeps max(portal bill, rate x price)
        rate_t = C["tax_street"].get(street) or C["tax_city"].get(city) or C.get("tax_zip", {}).get(z) or C["tax_state"].get(st, 0.012)
        taxes = max(rate_t * price, num(f.get("tax_annual")) or 0) if st == "NC" else rate_t * price
        # rental classification adjustment (memo 63 section 5.2): what a rented duplex pays over the owner-occupant rate the ACS reports
        RTA = C.get("rental_tax_adjust", {}); adj = RTA.get(f"{st}:{city}") or RTA.get(st) or {}
        taxes = taxes * adj.get("mult", 1.0) + adj.get("add_usd", 0) + adj.get("add_pct", 0) * (price or 0); adj_txt = (f" x{adj['mult']}" if adj.get("mult") else "") + (f" +${adj['add_usd']}" if adj.get("add_usd") else "") + (f" +{adj['add_pct']*100:.2f}pts" if adj.get("add_pct") else "")
        ins = C["insurance_hampton_roads"] if z[:3] in C["insurance_hampton_roads_zip3"] else C["insurance_state"].get(st, 1500)
        # distance: ZIP hours (Google-equivalent) before the city table; Elizabeth City hours where known; tier and its costs (memo 63 section 3)
        drive = C.get("drive_zip", {}).get(z) or C["drive_wb"].get(city); dec = C.get("drive_ec", {}).get(city)
        hours = min(x for x in (drive, dec) if x is not None) if (drive is not None or dec is not None) else None
        TC = C.get("tier_costs") or {"hours": {"A": 5.5, "B": 8.0}, "gate5_shift": {"A": 0, "B": 0.05, "C": 0.15}, "travel_usd": {"A": 0, "B": 600, "C": 1400}, "mgmt_extra": {"A": 0, "B": 0.04, "C": 0.04}, "score_penalty": {"A": 0, "B": 0.5, "C": 0.5}}
        tier = "A" if hours is None or hours <= TC["hours"]["A"] else ("B" if hours <= TC["hours"]["B"] else "C"); bar = round(0.9 + TC["gate5_shift"][tier], 2)
        crime = crime_for(city, z)
        grade = j.get("grade", "YELLOW"); units = j.get("units", 2)
        flags = C.get("jurisdiction_flags", {}); jflag = flags.get(f"{st}:{city}") or flags.get(st) or ""
        missing = []   # only rows that survive as ENTRANT or NEAR-MISS need constants; OUT rows are noise
        if city not in C["tax_city"] and street not in C["tax_street"] and z not in C.get("tax_zip", {}): missing.append(f"{city} {st}: tax rate (using state default {rate_t*100:.2f}%)")
        if hours is None: missing.append(f"{city} {st}: drive time from Williamsburg")
        if not crime: missing.append(f"{city} {st} {z}: CrimeGrade letter")
        coc = dscr = r2p = None; score = ""; why = []
        if rent and price:
            vac = 0.08 if (grade == "RED" or crime.startswith("F")) else 0.05
            noi = rent * 12 * (1 - vac - 0.10 - (0.08 + TC["mgmt_extra"][tier]) - 0.05) - taxes - ins - TC["travel_usd"][tier]; ads = pmt(0.75 * price, C["rate"]); coc = (noi - ads) / (0.3125 * price) * 100; dscr = noi / ads; r2p = round(rent * 100 / price, 4)
        if grade == "RED": verdict = "OUT (RED)"
        elif grade == "OUT" or not rent or units != 2: verdict = "OUT"
        elif r2p is not None and r2p < bar: verdict = "NEAR-MISS"
        elif coc is not None and coc < 0: verdict = "OUT (negative cash flow)"
        else: verdict = "ENTRANT"
        if verdict in ("ENTRANT", "NEAR-MISS"):
            pen = 0
            if grade.startswith("YELLOW"): pen += 4; why.append("YELLOW -4")
            cp = crime_pen(crime)
            if cp: pen += cp; why.append(f"crime {crime.split(' ')[0]} -{cp}")
            sp = TC.get("score_penalty_over_1_25h", 0.5) if (hours is not None and hours > 1.25) else 0   # was -2 beyond 1.25 h; the tier bar shift now carries the cost (memo 63 section 7.1 item 1)
            if sp: pen += sp; why.append(f"drive {hours}h tier {tier} -{sp}")
            fl = j.get("flood") if j.get("flood") is not None else f.get("flood")
            if fl and fl >= 5: pen += 1; why.append(f"flood {fl} -1")
            if dscr is not None and dscr < 1.2: pen += 2; why.append(f"DSCR {dscr:.2f} -2")
            score = round(coc - pen, 1)
            if verdict == "NEAR-MISS": why.insert(0, f"fails Gate 5: rent-to-price {r2p:.2f}% < {bar:.2f}% (tier {tier} bar)")
            if jflag: why.append(f"[{st} flag: {jflag.split(':')[0]}]")
            for m_ in missing: unknown.add(m_)
        out.append({"address": f["address"], "price": int(price) if price else "", "built": j.get("built") or f.get("built") or "", "days_on_market": j.get("dom") if j.get("dom") is not None else f.get("dom"), "status_" + DATE: j.get("status") or f.get("status") or "", "units": j.get("units_txt", ""), "rent_used": round(rent) if rent else "", "rent_basis": "listing text" if j.get("rents") else ("tract median x 2" if rent else ""), "tract_tier": f.get("tract_tier", ""), "rent_to_price_pct": round(r2p, 2) if r2p else "", "gate5_bar_pct": bar, "distance_tier": tier, "drive_h_google_eq": hours if hours is not None else "", "taxes_assumed": f"${taxes:,.0f}/yr at {rate_t*100:.2f}%{adj_txt}", "insurance_assumed": ins, "tier_costs_assumed": f"travel ${TC['travel_usd'][tier]} + mgmt +{TC['mgmt_extra'][tier]*100:.0f}pts" if tier != "A" else "", "coc_6.75_full_expense_pct": round(coc, 1) if coc is not None else "", "dscr_6.75": round(dscr, 2) if dscr is not None else "", "break_even_rent_for_bar": round(bar / 100 * price) if price else "", "novice_grade": grade, "photo_c_rating": j.get("c", ""), "photo_note": j.get("pnote", ""), "condition_note": ((f"[{jflag}] " if jflag else "") + (j.get("cond") or "")), "jurisdiction_flag": jflag, "crime_zip": crime, "drive_h_williamsburg": drive if drive is not None else "", "flood_factor": j.get("flood") if j.get("flood") is not None else (f.get("flood") if f.get("flood") is not None else ""), "last_sold": j.get("last_sold", ""), "score": score, "why": "; ".join(why), "verdict": verdict, "region": REGION, "url": f["url"]})
    out.sort(key=lambda o: (ORDER[o["verdict"]], -(o["score"] if o["score"] != "" else -999)))
    if out: wr(RUN + "results.csv", out)
    rows14 = rd(F14); f14fields = list(rows14[0].keys()); IFIELD = f14fields[0]   # the header starts with a BOM, so the first field reads as "﻿i", not "i"; writing the row under "i" silently dropped it (rows folded on 9/21 had a blank i)
    by_key = {}   # street-level match: portals disagree on ZIPs, unit suffixes and spellings (parsers.key folds Mount/Mt, North/N etc. since 2026-09-28)
    for r in rows14: by_key.setdefault(key(r["address"]), r)
    wnum = max([int(m.group(1)) for r in rows14 for m in [re.match(r"^w(\d+)$", (r[IFIELD] or "").strip())] if m] + [0])
    same_day = f"weekly sweep {DATE}"; n_new = 0; n_ref = 0
    for o in out:
        if o["verdict"] not in ("ENTRANT", "NEAR-MISS"): continue
        k = key(o["address"]); r = by_key.get(k)
        row = {IFIELD: "", "address": o["address"], "price": o["price"], "status": "ACTIVE (for sale)", "event": f"{same_day} {o['verdict']} UNREVIEWED" + ("" if REGION == "ncva" else f" [{REGION}]"), "score": o["score"], "coc_6.75": o["coc_6.75_full_expense_pct"], "dscr": o["dscr_6.75"], "novice": o["novice_grade"] + " / photo " + o["photo_c_rating"] + ("; flood factor %s" % o["flood_factor"] if o["flood_factor"] != "" else ""), "crime": (o["crime_zip"] or "").split(" ")[0], "drive_wb": o["drive_h_williamsburg"], "drive_ec": "", "flood": o["flood_factor"], "historic": "", "why": o["why"], "note": (o["condition_note"] or "")[:300], "url": o["url"]}
        if r is None:
            wnum += 1; row[IFIELD] = f"w{wnum}"; n_new += 1; rows14.append(row); by_key[k] = row
        elif r["event"].startswith(same_day) and "UNREVIEWED" in r["event"] and (REGION == "ncva" or f"[{REGION}]" in r["event"]):
            # 2026-09-28: a rerun on the same date (normally the one after the step-8 constants lookup) re-scores the row it folded earlier instead of leaving the pre-constant score and blank crime/drive columns in place; i, drive_ec and historic are kept
            for f_ in ("price", "status", "event", "score", "coc_6.75", "dscr", "novice", "crime", "drive_wb", "flood", "why", "note", "url"): r[f_] = row[f_]
            n_ref += 1; note(f"  re-scored same-date UNREVIEWED row {r[IFIELD]}: {o['address']} ({o['verdict']} {o['score']})")
        else: note(f"  already in file 14: {o['address']} ({o['verdict']} {o['score']})")
    if (n_new or n_ref) and not dry:
        def k14(r):
            active = r["status"].startswith("ACTIVE"); s = num(r["score"]); return (0 if active else 1, -(s if s is not None else -999))
        rows14.sort(key=k14); wr(F14, rows14, f14fields)
    folded_total = sum(1 for r in rows14 if r["event"].startswith(same_day) and (REGION == "ncva" or f"[{REGION}]" in r["event"]))   # every row this date's sweep folded, whichever pass folded it (the tally used to count only the latest pass, so a rerun wrote 0)
    note(f"## Verdicts ({len(out)} underwritten; {n_new} new rows folded into file 14 as UNREVIEWED, {n_ref} same-date rows re-scored, {folded_total} rows carry this sweep date{' [DRY RUN, file 14 untouched]' if dry else ''})")
    for o in out: note(f"  {o['verdict']:24s} | {o['address'][:44]:44s} | ${o['price']} | rent {o['rent_used']} r2p {o['rent_to_price_pct']} | CoC {o['coc_6.75_full_expense_pct']} DSCR {o['dscr_6.75']} | score {o['score']} | {o['novice_grade']} {o['photo_c_rating']} | {o['why']}")
    if unknown:
        note("## Constants needed (defaults used; add to constants.json with provenance)")
        for u in sorted(unknown): note("  " + u)
    if dry: print("  [dry run: weekly_tally.csv untouched]"); sys.exit(0)
    tfn = SWEEPS + "weekly_tally.csv"; trows = rd(tfn) if os.path.exists(tfn) else []
    trows = [t for t in trows if not (t["date"] == DATE and (t.get("region") or "ncva") == REGION)]
    scored_rows = rd(RUN + "scored.csv") if os.path.exists(RUN + "scored.csv") else []
    trows.append({"date": DATE, "region": REGION, "zips": len(jl(ZFILE)), "listings": len(scored_rows), "new": sum(1 for r in scored_rows if r["delta"] == "new"), "price_cuts": sum(1 for r in scored_rows if r["delta"].startswith("price cut")), "shortlist": sum(1 for r in scored_rows if r["shortlist"]), "entrants": sum(1 for o in out if o["verdict"] == "ENTRANT"), "near_misses": sum(1 for o in out if o["verdict"] == "NEAR-MISS"), "folded_into_14": folded_total})
    wr(tfn, trows, ["date", "region", "zips", "listings", "new", "price_cuts", "shortlist", "entrants", "near_misses", "folded_into_14"])

if stage == "refresh":
    T = jl(RUN + "tracked.json"); tracked = jl(RUN + "tracked_urls.json"); rows14 = rd(F14); f14fields = list(rows14[0].keys()); changes = []; dry = opts.get("dry", False)
    by_url = {r["url"]: r for r in rows14}
    for t in tracked:
        d = T.get(t["url"]); r = by_url.get(t["url"])
        if not d or not r: changes.append({"address": t["address"], "change": "no page fetched", "detail": ""}); continue
        if not d.get("ok"): changes.append({"address": t["address"], "change": "page failed", "detail": (d.get("excerpt") or "")[:80]}); continue
        if d.get("page_address") and key(d["page_address"]) != key(t["address"]) and "redfin" in t["url"]:
            changes.append({"address": t["address"], "change": "URL MISMATCH", "detail": f"page shows {d['page_address']} (redirect {d.get('redirected_to','')})"}); continue
        old_status = r["status"]; old_price = num(r["price"]); newp = d.get("price"); st = d.get("status")
        le = (d.get("last_event") or "")
        if st == "ACTIVE" and re.search(r"\b(Pending|Contingent)\b", le): st = "PENDING" if "Pending" in le else "CONTINGENT"   # belt and braces with parse_detail
        ev = []
        if st == "SOLD": r["status"] = f"SOLD {d.get('status_date','')} ${newp:,}" if newp else f"SOLD {d.get('status_date','')}"; ev.append("sold")
        elif st == "PENDING" and not old_status.startswith("PENDING"): r["status"] = f"PENDING ({DATE})"; ev.append("pending")
        elif st == "CONTINGENT" and not old_status.startswith("CONTINGENT"): r["status"] = f"CONTINGENT ({DATE})"; ev.append("contingent")
        elif st == "OFF MARKET": r["status"] = f"OFF MARKET ({DATE})"; ev.append("off market")
        elif st == "ACTIVE" and not old_status.startswith("ACTIVE"): r["status"] = "ACTIVE (for sale)"; ev.append("back to active")
        if st == "ACTIVE" and newp and old_price and abs(newp - old_price) > 0.5:
            ev.append(f"price {'cut' if newp < old_price else 'up'} ${old_price:,.0f} -> ${newp:,}"); r["price"] = str(newp)
        if ev:
            r["event"] = f"{'; '.join(ev)} ({DATE}; was: {old_status})"[:200]; changes.append({"address": t["address"], "change": "; ".join(ev), "detail": d.get("last_event", "")})
        else: changes.append({"address": t["address"], "change": "no change", "detail": f"{st} dom {d.get('dom')}"})
    if changes: wr(RUN + "tracked_changes.csv", changes)
    if not dry: wr(F14, rows14, f14fields)
    real = [c for c in changes if c["change"] not in ("no change",)]
    note(f"## Tracked rows refreshed ({len(tracked)} checked, {len(real)} changes or problems{' [DRY RUN]' if dry else ''})")
    for c in real: note(f"  {c['change'][:40]:40s} | {c['address'][:44]:44s} | {c['detail'][:90]}")

if stage == "report":
    parts = open(RUN + "report_parts.txt", encoding="utf-8").read() if os.path.exists(RUN + "report_parts.txt") else "(no parts)"
    open(RUN + "report.md", "w", encoding="utf-8").write(parts + f"\n\nFiles: {RUN}\n"); print(parts)

if stage == "help": print(__doc__ or open(__file__, encoding="utf-8").read().split("import csv")[0])
