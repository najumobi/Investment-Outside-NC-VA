# weekly_sweep.py - local orchestrator for the weekly duplex re-sweep (written 2026-09-14).
# 2026-09-29 (evening): file 14's novice cell is written by novice_cell() in the grammar of memo 66 (grade: C-rating and basis; reason; unseen; flood driver; date).
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
# 2026-09-29 (memo 65, section 8): plan moves stale fetch outputs aside; ingest refuses a fetch under 80% of its pages and orders the detail
#   queue by rent-to-price band (under 1.8% first; --order=r2p for the old order); prep builds facts only for rows whose detail page came back;
#   underwrite folds the page's status (CONTINGENT / PENDING / unverified; SOLD and OFF MARKET are not folded), uses the portal tax bill when it
#   is higher than rate x price in every state, and counts missing judgments in one line; refresh leaves rows already stamped today alone,
#   guards OFF MARKET like PENDING and appends to the event text instead of replacing it.
# 2026-09-30 (pipeline DEFECT 4, memo 68 section 6; fix_defect4_rent_basis_0930.py): an unstated rent is priced on the tract's median CONTRACT rent
#   (ACS B25058, constants rent_basis.table) instead of the median GROSS rent the tract model carries (B25064, tenant-paid utilities included);
#   gross x rent_basis.fallback_multiplier where a tract has no contract figure; the gross figure stays as the rent_ceiling_gross column;
#   rent_basis.mode = "gross" restores the old basis. A backlog row that a knockout now removes stops counting as detail-pending.
#   underwrite --rescore re-scores the rows a run folded at their current list price: score, cash-on-cash, coverage, why and the verdict word
#   of the event only (price, status, novice and note are kept, so a row whose verdict becomes OUT stays on the list for Najum's review; no new rows; the tally is untouched).
# 2026-09-30 (memo 69): crime is read at block-group level from model/crime_bg.json (six CrimeGrade tabs, hand screenshots) instead of the ZIP letter;
#   ingest knocks out a row by memo 69 section 4.4 (regional: Robbery F on the block and across the street; NC/VA: Robbery F with Burglary or Vandalism F)
#   and sorts Robbery-F rows behind the rest of the detail queue; underwrite scores the Robbery
#   position (crime_penalty), applies the 8% vacancy at Robbery F, writes the six readings into file 14's crime column and lists "crime maps needed".
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
RB = C.get("rent_basis") or {}; _CR = {}
def tract_rent(g, med):
    """Per-unit rent for a row with no stated rent, and the name of its basis (2026-09-30, pipeline DEFECT 4): the tract's median contract rent; gross x the fallback multiplier without one."""
    if RB.get("mode") != "contract": return med, "tract median"
    if not _CR and os.path.exists(PIPE + RB.get("table", "?")): _CR.update(jl(PIPE + RB["table"]))
    v = _CR.get(g) if g else None
    if v and v[0] and v[0] > 0: return float(v[0]), "tract contract rent"
    m = RB.get("fallback_multiplier", 0.83)
    return (round(med * m) if med else None), f"tract gross rent x {m}"
# 2026-09-30 (memo 69, the block-level crime read): the crime input is the CrimeGrade legend position of the listing's 2020 census block group
#   on six crime tabs (Robbery, Assault, Burglary, Vandalism, Drug, Murder), read from model/crime_bg.json, which build_crime_bg.py fills from
#   hand screenshots of the ZIP pages; the ZIP-level Overall letter (constants crime_zip) is retired. Robbery carries the score penalty and the
#   vacancy rule; Robbery F together with Burglary or Vandalism F is a knockout; a block group no map covers reads "maps needed".
import urllib.parse
CB_FN = MODEL + "crime_bg.json"; _CB = {}
def crime_table():
    if not _CB and os.path.exists(CB_FN): _CB.update(jl(CB_FN).get("bg", {}))
    return _CB
import math
BGC_FN = MODEL + "geo_cache_bg.json"; _BG = {}
def _geo(address):
    """{"bg", "lat", "lon"} of an address: the batch geocoder's result from ingest (geo_cache_bg.json), else one call to the one-line geocoder, cached.
    A value cached as a bare block group (the first patch) is upgraded; a failed call is not cached, so the next run tries again."""
    if not _BG and os.path.exists(BGC_FN): _BG.update(jl(BGC_FN))
    v = _BG.get(address)
    if isinstance(v, dict) and (v.get("lat") is not None or not v.get("bg")): return v
    a = re.sub(r"\s+(Unit|Apt|#|Lot)\b[^,]*", "", address, flags=re.I); a = re.sub(r"^(\d+)\s*[-&/]\s*\d+\S*\s", r"\1 ", a.strip())
    try:
        q = urllib.parse.urlencode({"address": a, "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"})
        with urllib.request.urlopen(urllib.request.Request("https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress?" + q, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as resp: d = json.load(resp)
        m = d["result"]["addressMatches"]
        v = {"bg": m[0]["geographies"]["2020 Census Blocks"][0]["GEOID"][:12], "lat": m[0]["coordinates"]["y"], "lon": m[0]["coordinates"]["x"]} if m else ({"bg": v} if isinstance(v, str) and v else {"bg": ""})
    except Exception:
        return {"bg": v} if isinstance(v, str) else (v or {"bg": ""})
    _BG[address] = v; js(BGC_FN, _BG); return v
def block_group_for(address): return _geo(address).get("bg", "")
AX_FN = MODEL + "crime_across_cache.json"; _AX = {}
def across_street(address, radius_m=15):
    """[[GEOID, metres], ...] of the other 2020 block groups whose boundary lies within radius_m of the address point (the block group across
    the street), from one TIGERweb query, cached; [] when no boundary is that close; None when it cannot be checked."""
    if not _AX and os.path.exists(AX_FN): _AX.update(jl(AX_FN))
    if address in _AX: return _AX[address]
    g = _geo(address)
    if g.get("lat") is None or not g.get("bg"): return None
    lat, lon = g["lat"], g["lon"]; kx = 111320 * math.cos(math.radians(lat)); ky = 110540; e = 0.0015
    try:
        q = urllib.parse.urlencode({"geometry": f"{lon - e},{lat - e},{lon + e},{lat + e}", "geometryType": "esriGeometryEnvelope", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects", "outFields": "GEOID", "returnGeometry": "true", "outSR": "4326", "f": "geojson"})
        with urllib.request.urlopen(urllib.request.Request("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/11/query?" + q, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as resp: fc = json.load(resp)
    except Exception: return None
    if "features" not in fc: return None
    def seg(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay; t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy))) if (dx or dy) else 0.0
        return math.hypot(px - ax - t * dx, py - ay - t * dy)
    out = []
    for ft in fc["features"]:
        gid = (ft.get("properties") or {}).get("GEOID"); geom = ft.get("geometry") or {}
        if not gid or gid == g["bg"] or not geom: continue
        polys = [geom["coordinates"]] if geom.get("type") == "Polygon" else geom.get("coordinates", [])
        best = min((seg(0.0, 0.0, (x1 - lon) * kx, (y1 - lat) * ky, (x2 - lon) * kx, (y2 - lat) * ky)
                    for poly in polys for ring in poly for (x1, y1), (x2, y2) in zip(ring, ring[1:])), default=1e9)
        if best <= radius_m: out.append([gid, round(best)])
    _AX[address] = out; js(AX_FN, _AX); return out
def crime_read(address):
    """The legend positions (0 = A+ .. 1 = F) of the address's block group on each tab, plus its GEOID, or None when no map covers it."""
    bg = block_group_for(address); rec = crime_table().get(bg) if bg else None
    return dict(rec, bg=bg) if rec and "R" in rec else None
GRADES = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]
def cgrade(p): return GRADES[min(12, int(p * 13))]
def cpos(p): return ("%.2f" % p)[1:]
def crime_cell(cr, mmdd):
    """file 14's crime cell: Robbery, Assault, Burglary and Vandalism as position and letter, Murder and Drug as letters, the date of the read."""
    parts = [f"{k} {cpos(cr[k])} {cgrade(cr[k])}" for k in ("R", "A", "B", "V") if k in cr]
    flags = [f"{k} {cgrade(cr[k])}" for k in ("M", "D") if k in cr]
    return " / ".join(parts) + ("; " + ", ".join(flags) if flags else "") + f" ({mmdd})"
def crime_penalty(cr): return round(max(0.0, 3 * (cr["R"] - 0.6) / 0.4), 1) if cr else 0   # 0 at C+ and better, about 1 at D+, 2 at D-, 2.6 in the middle of F; replaces the letter's 3/2/1/0.5
def crime_knockout(cr, address):
    """memo 69 section 4.4. Regional sweeps: Robbery F and the block group across the street also F. NC/VA: Robbery F and Burglary or Vandalism F.
    A street that cannot be checked, or a block group across it with no map, does not knock the row out."""
    if not cr or cr["R"] < 12 / 13: return False
    if REGION == "ncva": return cr.get("B", 0) >= 12 / 13 or cr.get("V", 0) >= 12 / 13
    ax = across_street(address)
    if ax is None: return False
    return all((crime_table().get(gid) or {}).get("R", 0) >= 12 / 13 for gid, _ in ax)
def crime_ko_text(cr):
    if REGION == "ncva": return f"crime: Robbery {cgrade(cr['R'])} with Burglary {cgrade(cr.get('B', 0))}, Vandalism {cgrade(cr.get('V', 0))}"
    return f"crime: Robbery {cgrade(cr['R'])} on this block and across the street"
MMDD = f"{int(DATE[5:7])}/{int(DATE[8:10])}"
def akey(a):
    m = re.search(r"(\d{5})\s*$", a.strip()); return key(a) + "|" + (m.group(1) if m else "")
def note(line):
    with open(RUN + "report_parts.txt", "a", encoding="utf-8") as f: f.write(line.rstrip() + "\n")
    print(line)

# 2026-09-29: the novice cell of a folded file 14 row, in the grammar of memo 66 (restate_novice_0929.py carries the same three functions)
def clause_split(text):
    """Split at semicolons that are not inside parentheses or quotes."""
    out, cur, depth = [], "", 0
    for ch in text:
        if ch == "(": depth += 1
        elif ch == ")": depth = max(0, depth - 1)
        if ch == ";" and depth == 0: out.append(cur.strip()); cur = ""
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return out

def trim(text, n):
    """Cut at a clause or word boundary under n characters, never inside a parenthesis."""
    if len(text) <= n: return text
    cut = text[:n]
    for sep in (", ", " but ", " and ", " "):
        i = cut.rfind(sep)
        if i > n // 2:
            cand = text[:i]
            if cand.count("(") == cand.count(")"): return cand.rstrip(",") + " ..."
    while cut.count("(") > cut.count(")"): cut = cut[:cut.rfind("(")].rstrip()
    return cut.rstrip(",") + " ..."

def novice_cell(grade, c, cond, flood, mmdd):
    """The novice designation for a folded row: grade, C-rating and its basis, the judgment's first clause, the flood driver, the date."""
    c = (c or "").strip()
    cphrase = "no usable photo" if c.lower() in ("", "n/a", "none") else f"{c.replace('-', ' to ')} on the one listing photo"
    text = re.sub(r"^\[[^\]]*\]\s*", "", (cond or "").strip())                   # drop the jurisdiction flag prefix
    text = re.sub(r"^(GREEN-verify|GREEN|YELLOW|RED|UNVERIFIED)\s*[:,]?\s*", "", text, flags=re.I)
    clauses = clause_split(text)                                                     # the judgment line is "why this grade; then the rest"
    if len(clauses) > 1 and re.fullmatch(r"(Redfin )?flood factor \d+", clauses[0]): clauses = clauses[1:]   # a bare flood clause is carried by the suffix
    reason = clauses[0] if clauses else ""
    if len(clauses) > 1 and (len(reason) < 40 or (grade == "GREEN-verify" and re.search(r"verif|confirm|receipt|invoice|permit|scope|dates", clauses[1]) and len(reason) + len(clauses[1]) < 210)):
        reason += "; " + clauses[1]                                                  # a short first clause, or the verify demand a GREEN-verify states
    reason = re.sub(r"^C\d(?:-C\d)?\s+(?:but\s+)?(?=built|with|construction)", "", reason)   # "C3 but built 1904 ..." repeats the C-rating
    reason = trim(reason.rstrip("."), 200)
    while reason.count("(") > reason.count(")"): reason = reason[:reason.rfind("(")].rstrip(" ,;") + " ..."   # a judgment line cut at the note's 300-character cap
    try: fl = int(str(flood).split(" ")[0])
    except Exception: fl = None
    ftxt = f"; flood factor {fl}, itself a YELLOW driver" if fl is not None and fl >= 5 and grade != "RED" and "flood factor" not in reason else ""
    return f"{grade}: {cphrase}" + (f"; {reason}" if reason else "") + ftxt + f" ({mmdd})"
# end of the novice-cell helpers

if stage == "wait":
    target = RUN + args[1]; t = time.time()
    while not os.path.exists(target) and time.time() - t < 240: time.sleep(10)
    print("found" if os.path.exists(target) else "MISSING after 240 s:", target); sys.exit(0 if os.path.exists(target) else 2)

if stage == "plan":
    stamp = datetime.datetime.now().strftime("%H%M")   # 2026-09-29: a fetch output left by an earlier or colliding run must not satisfy "wait" (the 9/28 collision left a 160-of-200-page listings_raw.csv in the pitt folder)
    for fn in ("listings_raw.csv", "fetch_counts.json", "details.json", "tracked.json"):
        if os.path.exists(RUN + fn):
            base, ext = os.path.splitext(fn); os.replace(RUN + fn, RUN + f"{base}.stale-{stamp}{ext}"); print(f"moved a stale {fn} aside as {base}.stale-{stamp}{ext}")
    rows = rd(F14); tracked = []; n_today = 0
    for r in rows:
        s = r["status"].upper()
        if s.startswith(("OUT", "SOLD", "WITHDRAWN", "OFF MARKET", "EXPIRED")): continue
        if DATE in (r["status"] or "") or DATE in (r["event"] or ""): n_today += 1; continue   # 2026-09-29: folded or refreshed earlier today by another region's run; refresh would skip it anyway
        if "redfin.com" in r["url"] or "zillow.com" in r["url"]: tracked.append({"address": r["address"], "url": r["url"], "status": r["status"], "price": r["price"]})
    js(RUN + "tracked_urls.json", tracked)
    zips = jl(ZFILE)
    open(RUN + "report_parts.txt", "w", encoding="utf-8").write(f"# Weekly sweep {DATE} ({REGION})\n")
    print(f"run folder {RUN}\nregion {REGION}: list pages to fetch: {sum(1 + (1 if z.get('zillow') else 0) for z in zips)} across {len(zips)} ZIPs ({RC['zips']})\ntracked rows to refresh: {len(tracked)} (tracked_urls.json){f'; {n_today} rows already stamped today left out' if n_today else ''}")
    print(f"NEXT: in the workbench run remote_setup(DATE, '{REGION}'); remote_fetch_lists(0..4); remote_parse_lists(); then locally: weekly_sweep.py wait listings_raw.csv --region={REGION} && weekly_sweep.py ingest --region={REGION}")

if stage == "ingest":
    raw = rd(RUN + "listings_raw.csv"); health = jl(RUN + "fetch_counts.json") if os.path.exists(RUN + "fetch_counts.json") else {"counts": {}, "bad": []}
    if health.get("pages") and health["pages"] - (health.get("fetched_ok") or 0) >= 0.2 * health["pages"]:   # 2026-09-29: the workbench HALT counted only fetched-and-failed pages and its print can vanish; a fetch missing a fifth or more of its pages (one skipped part = exactly a fifth, the 9/28 collision case) is refused here, before the seen index is touched
        sys.exit(f"HALT: only {health.get('fetched_ok')} of {health['pages']} list pages were fetched (fetch_counts.json); nothing ingested. Re-run the workbench fetch for every part, then ingest again.")
    idx = {r["key"]: r for r in rd(PIPE + "seen_index.csv")}; fields_idx = list(next(iter(idx.values())).keys())
    if "detail_pending" not in fields_idx: fields_idx.append("detail_pending")   # 2026-09-28: shortlisted rows whose detail page has not been fetched yet (dense regions exceed the 40-page cap)
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
    bgc = jl(BGC_FN) if os.path.exists(BGC_FN) else {}   # 2026-09-30: block groups from the same batch geocode
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
                if len(rec) >= 12 and rec[2] == "Match":
                    cache[raw[int(rec[0])]["address"]] = rec[8] + rec[9] + rec[10]
                    if len(rec) >= 12 and rec[11]:
                        try: lon_, lat_ = (float(x) for x in rec[5].split(","))
                        except Exception: lon_ = lat_ = None
                        bgc[raw[int(rec[0])]["address"]] = {"bg": rec[8] + rec[9] + rec[10] + rec[11][:1], "lat": lat_, "lon": lon_}
            js(cache_fn, cache); js(BGC_FN, bgc); _BG.update(bgc)
        except Exception as ex: note(f"geocoder failed: {ex}")
    S10 = jl(PIPE + RC["tract_scores_x1.0"]); S125 = jl(PIPE + RC["tract_scores_x1.25"]); md = jl(PIPE + RC["map_data"])["rows"]
    cat = {r["fips"]: r["cat"] for r in md}; names = {r["fips"]: r["name"] + " " + r["st"] for r in md}; tiers = {}
    for fn in RC["watchlists"]:
        for rr in rd(PIPE + fn): tiers[rr["geoid"]] = rr["tier"]
    scored = []; shortlist = []
    for r in raw:
        k = akey(r["address"]); g = cache.get(r["address"]); d = S10.get(g, {}) if g else {}; d125 = S125.get(g, {}) if g else {}; fips = g[:5] if g else None
        p = num(r["price"]); beds = num(r["beds"]); ut = num(r["units_text"]); units = int(ut) if ut else (2 if (beds and beds <= 6) else None)
        med = d.get("median_rent"); con, cbasis = tract_rent(g, med); rent_stated = num(r["rent_text"]); rent = rent_stated or ((units or 2) * con if con else None)   # 2026-09-30: contract rent, not gross (DEFECT 4)
        rec = dict(r); rec.update({"delta": deltas.get(k, ""), "tract": g or "", "county": names.get(fips, ""), "county_category": cat.get(fips, ""), "tract_tier": tiers.get(g, "") if g else "", "gate1_x1.0": d.get("gate", ""), "gate1_x1.25": d125.get("gate", ""), "tract_median_rent": med, "tract_contract_rent": con if cbasis == "tract contract rent" else "", "units_assumed": units, "rent_used": rent, "rent_basis": "listing text" if rent_stated else cbasis + " x units", "rent_ceiling_gross": (units or 2) * med if med else ""})
        rec["rent_to_price_pct"] = round(rent * 100 / p, 2) if (p and rent) else ""
        ko = []
        if r.get("land") == "True": ko.append("land")
        if not p: ko.append("no price")
        elif p > C["hard_ceiling"]: ko.append("above hard ceiling")
        if units and units != 2: ko.append("%d units, not a duplex" % units)
        if not g: ko.append("not geocoded")
        if g and d.get("gate") and d["gate"] != "PASS": ko.append("tract fails Gate 1 at x1.0")
        if rec["rent_to_price_pct"] != "" and rec["rent_to_price_pct"] < 0.9: ko.append("rent-to-price under 0.9%")
        # 2026-09-30: block-level crime for the rows that could reach the detail queue (the rest would cost a geocode each for nothing)
        could = (rec["delta"] in ("new", "relisted") or rec["delta"].startswith("price cut") or idx.get(k, {}).get("detail_pending") == "yes") and not ko and p and p <= C["practical_ceiling"]
        cr = crime_read(r["address"]) if could else None
        rec["block_group"] = cr["bg"] if cr else ""; rec["crime_R"] = round(cr["R"], 3) if cr else ""; rec["crime_cell"] = crime_cell(cr, MMDD) if cr else (f"maps needed {k.split(chr(124))[1]}" if could else "")
        if cr and crime_knockout(cr, r["address"]): ko.append(crime_ko_text(cr))
        rec["knockouts"] = "; ".join(ko)
        fresh = rec["delta"] in ("new", "relisted") or rec["delta"].startswith("price cut")
        pending = idx.get(k, {}).get("detail_pending") == "yes"   # shortlisted on an earlier run, detail page never fetched
        if pending and ko: idx[k]["detail_pending"] = ""; pending = False   # 2026-09-30: a backlog row that a knockout now removes (the contract-rent basis moved many under 0.9%) stops counting as pending
        rec["shortlist"] = "YES" if ((fresh or pending) and not ko and p and p <= C["practical_ceiling"]) else ""
        if pending and not fresh: rec["delta"] = (rec["delta"] + "; detail pending").strip("; ")
        scored.append(rec)
        if rec["shortlist"]: shortlist.append(rec); idx[k]["detail_pending"] = "yes"
    wr(PIPE + "seen_index.csv", list(idx.values()), fields_idx)
    keys = []
    for o in scored:
        for kk in o.keys():
            if kk not in keys: keys.append(kk)
    wr(RUN + "scored.csv", scored, keys)
    BAND = float(C.get("detail_order_band_pct", 1.8)); DORDER = opts.get("order", "band")   # 2026-09-29 (memo 65 section 4): NC/VA money-passers at 1.8%+ rent-to-price reached the live list 0.5 times in 33 (memo 63), so the capped detail fetch takes the 0.9-1.8% band first, highest first, then the rest; --order=r2p restores the plain rent-to-price order
    r2p_of = lambda s: s["rent_to_price_pct"] if s["rent_to_price_pct"] != "" else 0
    if DORDER == "r2p": shortlist.sort(key=lambda s: -r2p_of(s))
    else: shortlist.sort(key=lambda s: (1 if r2p_of(s) >= BAND else 0, 1 if (s.get("crime_R") != "" and s.get("crime_R") is not None and float(s["crime_R"]) >= 12 / 13) else 0, -r2p_of(s)))   # 2026-09-30: Robbery-F rows go behind the band (memo 69 section 4.3)
    js(RUN + "detail_plan.json", [{"address": s["address"], "url": s["url"], "zurl": s.get("zurl", ""), "rent_to_price_pct": s["rent_to_price_pct"], "delta": s["delta"], "crime": s.get("crime_cell", "")} for s in shortlist])
    need_maps = sorted({s["crime_cell"].split(" ")[-1] for s in shortlist if str(s.get("crime_cell", "")).startswith("maps needed")})
    if need_maps: note(f"## Crime maps needed ({len(need_maps)} ZIPs on the shortlist have no block-level read; six CrimeGrade tabs each, see memo 69): " + ", ".join(need_maps))
    dl = {}
    for v in deltas.values(): dl[v.split(" ")[0]] = dl.get(v.split(" ")[0], 0) + 1
    note(f"## Fetch health\n{health.get('fetched_ok','?')}/{health.get('pages','?')} list pages ok; bad pages: {len(health.get('bad', []))}; ZIPs with both portals ok: {len(ok_zips)}/{len(cnt)}; listings this week: {len(raw)}")
    note(f"## Listings\nnew {dl.get('new',0)}, relisted {dl.get('relisted',0)}, price cuts {dl.get('price',0)}, unchanged {dl.get('unchanged',0)}, off the list pages since last sweep {len(gone)} (pending, sold, withdrawn, or pushed past page 1; tracked rows get the truth from their detail pages)")
    for g_ in gone[:40]: note(f"  off list: {g_}")
    for r in scored:
        if r["delta"] in ("new", "relisted") or r["delta"].startswith("price cut"): note(f"  {r['delta'][:24]:24s} | {r['address'][:46]:46s} | ${r['price']} | {r['beds']}bd {r['sqft']}sf | tier {r['tract_tier']} {r['gate1_x1.0'][:4]} | r2p {r['rent_to_price_pct']} | {r['knockouts'] or 'SHORTLIST'}")
    note(f"## Shortlist ({len(shortlist)} rows need detail pages; {sum(1 for s in shortlist if 'detail pending' in s['delta'])} carried over from earlier runs; {sum(1 for s in shortlist if r2p_of(s) >= BAND)} at or above {BAND}% rent-to-price go last; the workbench fetches the first 40-50 in {'plain rent-to-price' if DORDER == 'r2p' else 'band'} order)")
    print(f"\nNEXT: {len(shortlist)} detail URLs in detail_plan.json; in the workbench run remote_details_batched(<first 40-50 urls>, 'details') and remote_details_batched(<tracked urls>, 'tracked') once per cell until each returns 'done'; then locally: wait details.json && prep")

if stage == "prep":
    det = jl(RUN + "details.json") if os.path.exists(RUN + "details.json") else {}; plan = jl(RUN + "detail_plan.json"); scored = {akey(r["address"]): r for r in rd(RUN + "scored.csv")}
    os.makedirs(RUN + "photos", exist_ok=True); facts = {}; tmpl = {}
    for p in plan:
        d = det.get(p["url"]) or det.get(p.get("zurl", "")) or {}; k = akey(p["address"]); s = scored.get(k, {}); street = p["address"].split(",")[0]
        if not d: continue   # 2026-09-29: rows the capped fetch did not reach stay detail_pending; they used to get a facts and template entry (and a 'no judgment' line each in underwrite)
        photo = d.get("photo", ""); local = ""
        if photo:
            local = RUN + "photos/" + re.sub(r"[^A-Za-z0-9]+", "_", street)[:40] + ".jpg"
            try:
                if not os.path.exists(local):
                    req = urllib.request.Request(photo, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.redfin.com/"}); open(local, "wb").write(urllib.request.urlopen(req, timeout=60).read())
            except Exception as ex: local = f"(photo download failed: {ex})"
        facts[street] = {"address": p["address"], "price": s.get("price"), "built": d.get("built"), "dom": d.get("dom"), "status": d.get("status"), "history": d.get("history", ""), "flood": d.get("flood"), "tax_annual": d.get("tax_annual"), "mls": d.get("mls", ""), "listed_by": d.get("listed_by", ""), "zoning_line": (d.get("zoning_line") or "")[:120], "unit_rent_text": d.get("unit_rent_text", ""), "remarks": (d.get("remarks") or d.get("excerpt") or "")[:900], "tract_tier": s.get("tract_tier"), "tract": s.get("tract"), "tract_median_rent": s.get("tract_median_rent"), "tract_contract_rent": s.get("tract_contract_rent"), "rent_to_price_pct": s.get("rent_to_price_pct"), "beds": s.get("beds"), "sqft": s.get("sqft"), "photo_url": photo, "photo_local": local, "url": p["url"]}
        tmpl[street] = {"grade": "GREEN|GREEN-verify|YELLOW|RED|OUT", "c": "C1..C6 from the front photo", "units": 2, "units_txt": "one line: what the building is per remarks and photos", "rents": None, "cond": "one line: why this grade (its first clause becomes the file 14 novice cell); RED items per file 08", "pnote": "one line photo note", "flood": d.get("flood"), "built": d.get("built"), "dom": d.get("dom"), "status": d.get("status"), "last_sold": ""}
    js(RUN + "facts.json", facts); js(RUN + "judgments_template.json", tmpl)
    note(f"## Detail pages: {len(facts)} of {len(plan)} shortlisted rows have a fetched page this run; {len(plan) - len(facts)} stay detail_pending for the next run")
    # clear the detail backlog flag for every shortlisted row whose detail page came back; the rest stay pending for next week
    idx = {r["key"]: r for r in rd(PIPE + "seen_index.csv")}; fields_idx = list(next(iter(idx.values())).keys()); cleared = 0
    for p in plan:
        d = det.get(p["url"]) or det.get(p.get("zurl", "")) or {}; k = akey(p["address"])
        if d and k in idx and idx[k].get("detail_pending") == "yes": idx[k]["detail_pending"] = ""; cleared += 1
    if cleared: wr(PIPE + "seen_index.csv", list(idx.values()), fields_idx)
    still = sum(1 for e in idx.values() if e.get("detail_pending") == "yes")
    note(f"## Detail backlog: {cleared} shortlisted rows detailed this run; {still} rows still pending a detail page (all regions)")
    for street, f in facts.items():
        print(f"\n=== {f['address']} | ${f['price']} | built {f['built']} | dom {f['dom']} | {f['status']} | flood {f['flood']} | tax {f['tax_annual']} | tier {f['tract_tier']} tract contract rent {f.get('tract_contract_rent')} (gross {f['tract_median_rent']}) r2p {f['rent_to_price_pct']}\n  photo: {f['photo_local']}\n  history: {f['history'][:160]}\n  rent text: {f['unit_rent_text']}\n  remarks: {f['remarks'][:500]}")
    print(f"\nNEXT: view each photo with Read, then write judgments.json (copy judgments_template.json, fill grade/c/units/units_txt/rents/cond/pnote), then: underwrite")

if stage == "underwrite":
    facts = jl(RUN + "facts.json"); J = jl(RUN + "judgments.json") if os.path.exists(RUN + "judgments.json") else {}
    dry = opts.get("dry", False); out = []; unknown = set(); no_j = []
    rescore = opts.get("rescore", False); TODAY = datetime.date.today().isoformat()   # 2026-09-30: --rescore, see the header
    same_day = f"weekly sweep {DATE}"
    mine = lambda r: r["event"].startswith(same_day) and "UNREVIEWED" in r["event"] and ((f"[{REGION}]" in r["event"]) if REGION != "ncva" else not re.search(r"UNREVIEWED \[\w+\]", r["event"]))   # a row this run folded that nobody has reviewed
    sc_tract = {akey(r["address"]): r.get("tract", "") for r in rd(RUN + "scored.csv")} if os.path.exists(RUN + "scored.csv") else {}   # facts written before 2026-09-30 carry no tract
    cur_price = {key(r["address"]): num(r["price"]) for r in rd(F14) if mine(r) and num(r["price"])} if rescore else {}   # refresh may have recorded a price cut since the fold
    def crime_for(city, z):   # the retired ZIP letter, kept in results.csv as crime_zip for reference only (2026-09-30)
        return C["crime"].get(city) or C["crime_zip"].get(z, "")
    ORDER = {"ENTRANT": 0, "NEAR-MISS": 1, "OUT (negative cash flow)": 2, "OUT (crime)": 2.5, "OUT (RED)": 3, "OUT": 4}
    for street, f in facts.items():
        j = J.get(street)
        if not j: no_j.append(street); continue   # 2026-09-29: counted once below instead of one line per row
        parts = [p.strip() for p in f["address"].split(",")]; city = parts[1] if len(parts) > 2 else ""; st = parts[-1].split()[0] if parts else ""; z = f["address"][-5:]
        price = num(f["price"]); med = num(f["tract_median_rent"]); con, cbasis = tract_rent(f.get("tract") or sc_tract.get(akey(f["address"]), ""), med); stated = num(j.get("rents")); rent = stated or (2 * con if con else None)   # 2026-09-30: contract rent, not gross (DEFECT 4)
        if cur_price.get(key(f["address"])): price = cur_price[key(f["address"])]
        # tax rate: street, city, ZIP (county owner rate, 2026-09-28), then the state default; NC keeps max(portal bill, rate x price)
        rate_t = C["tax_street"].get(street) or C["tax_city"].get(city) or C.get("tax_zip", {}).get(z) or C["tax_state"].get(st, 0.012)
        bill = num(f.get("tax_annual")) or 0; taxes = max(rate_t * price, bill); tax_src = "from the portal bill" if bill > rate_t * price else f"at {rate_t*100:.2f}%"   # 2026-09-29: the higher of rate x price and the portal's bill in every state (was NC only): 713 Mcmillen St modelled $682 against a $1,666 bill
        # rental classification adjustment (memo 63 section 5.2): what a rented duplex pays over the owner-occupant rate the ACS reports
        RTA = C.get("rental_tax_adjust", {}); adj = RTA.get(f"{st}:{city}") or RTA.get(st) or {}
        taxes = taxes * adj.get("mult", 1.0) + adj.get("add_usd", 0) + adj.get("add_pct", 0) * (price or 0); adj_txt = (f" x{adj['mult']}" if adj.get("mult") else "") + (f" +${adj['add_usd']}" if adj.get("add_usd") else "") + (f" +{adj['add_pct']*100:.2f}pts" if adj.get("add_pct") else "")
        ins = C["insurance_hampton_roads"] if z[:3] in C["insurance_hampton_roads_zip3"] else C["insurance_state"].get(st, 1500)
        # distance: ZIP hours (Google-equivalent) before the city table; Elizabeth City hours where known; tier and its costs (memo 63 section 3)
        drive = C.get("drive_zip", {}).get(z) or C["drive_wb"].get(city); dec = C.get("drive_ec", {}).get(city)
        hours = min(x for x in (drive, dec) if x is not None) if (drive is not None or dec is not None) else None
        TC = C.get("tier_costs") or {"hours": {"A": 5.5, "B": 8.0}, "gate5_shift": {"A": 0, "B": 0.05, "C": 0.15}, "travel_usd": {"A": 0, "B": 600, "C": 1400}, "mgmt_extra": {"A": 0, "B": 0.04, "C": 0.04}, "score_penalty": {"A": 0, "B": 0.5, "C": 0.5}}
        tier = "A" if hours is None or hours <= TC["hours"]["A"] else ("B" if hours <= TC["hours"]["B"] else "C"); bar = round(0.9 + TC["gate5_shift"][tier], 2)
        crime = crime_for(city, z); cr = crime_read(f["address"])   # 2026-09-30: the block-level read decides; the letter is reference only
        grade = j.get("grade", "YELLOW"); units = j.get("units", 2)
        flags = C.get("jurisdiction_flags", {}); jflag = flags.get(f"{st}:{city}") or flags.get(st) or ""
        missing = []   # only rows that survive as ENTRANT or NEAR-MISS need constants; OUT rows are noise
        if city not in C["tax_city"] and street not in C["tax_street"] and z not in C.get("tax_zip", {}): missing.append(f"{city} {st}: tax rate (using state default {rate_t*100:.2f}%)")
        if hours is None: missing.append(f"{city} {st}: drive time from Williamsburg")
        if not cr: missing.append(f"{z}: crime maps needed (the six CrimeGrade tabs of the ZIP page, screenshot by hand; memo 69)")
        coc = dscr = r2p = None; score = ""; why = []
        if rent and price:
            vac = 0.08 if (grade == "RED" or (cr and cr["R"] >= 12 / 13)) else 0.05   # 2026-09-30: Robbery F, not the ZIP letter
            noi = rent * 12 * (1 - vac - 0.10 - (0.08 + TC["mgmt_extra"][tier]) - 0.05) - taxes - ins - TC["travel_usd"][tier]; ads = pmt(0.75 * price, C["rate"]); coc = (noi - ads) / (0.3125 * price) * 100; dscr = noi / ads; r2p = round(rent * 100 / price, 4)
        if grade == "RED": verdict = "OUT (RED)"
        elif grade == "OUT" or not rent or units != 2: verdict = "OUT"
        elif crime_knockout(cr, f["address"]): verdict = "OUT (crime)"   # 2026-09-30 (memo 69 section 4.4)
        elif r2p is not None and r2p < bar: verdict = "NEAR-MISS"
        elif coc is not None and coc < 0: verdict = "OUT (negative cash flow)"
        else: verdict = "ENTRANT"
        if verdict in ("ENTRANT", "NEAR-MISS") or (rescore and verdict == "OUT (negative cash flow)"):
            pen = 0
            if grade.startswith("YELLOW"): pen += 4; why.append("YELLOW -4")
            cp = crime_penalty(cr); pen += cp   # 2026-09-30: on the Robbery position
            why.append((f"crime R {cpos(cr['R'])} {cgrade(cr['R'])} -{cp}" if cp else f"crime R {cpos(cr['R'])} {cgrade(cr['R'])} 0") if cr else "crime unread (maps needed)")
            sp = TC.get("score_penalty_over_1_25h", 0.5) if (hours is not None and hours > 1.25) else 0   # was -2 beyond 1.25 h; the tier bar shift now carries the cost (memo 63 section 7.1 item 1)
            if sp: pen += sp; why.append(f"drive {hours}h tier {tier} -{sp}")
            fl = j.get("flood") if j.get("flood") is not None else f.get("flood")
            if fl and fl >= 5: pen += 1; why.append(f"flood {fl} -1")
            if dscr is not None and dscr < 1.2: pen += 2; why.append(f"DSCR {dscr:.2f} -2")
            if stated and med and RB.get("stated_rent_flag_under") and stated < RB["stated_rent_flag_under"] * 2 * med: why.append(f"stated rent ${stated:,.0f} is under {RB['stated_rent_flag_under']} of the tract gross figure x 2 (${2 * med:,.0f}): confirm it covers both units")   # 2026-09-30: no score effect
            score = round(coc - pen, 1)
            if verdict == "NEAR-MISS": why.insert(0, f"fails Gate 5: rent-to-price {r2p:.2f}% < {bar:.2f}% (tier {tier} bar)")
            if jflag: why.append(f"[{st} flag: {jflag.split(':')[0]}]")
            for m_ in missing: unknown.add(m_)
        out.append({"address": f["address"], "price": int(price) if price else "", "built": j.get("built") or f.get("built") or "", "days_on_market": j.get("dom") if j.get("dom") is not None else f.get("dom"), "status_" + DATE: j.get("status") or f.get("status") or "", "units": j.get("units_txt", ""), "rent_used": round(rent) if rent else "", "rent_basis": "listing text" if stated else (cbasis + " x 2" if rent else ""), "rent_ceiling_gross": round(2 * med) if med else "", "tract_tier": f.get("tract_tier", ""), "rent_to_price_pct": round(r2p, 2) if r2p else "", "gate5_bar_pct": bar, "distance_tier": tier, "drive_h_google_eq": hours if hours is not None else "", "taxes_assumed": f"${taxes:,.0f}/yr {tax_src}{adj_txt}", "insurance_assumed": ins, "tier_costs_assumed": f"travel ${TC['travel_usd'][tier]} + mgmt +{TC['mgmt_extra'][tier]*100:.0f}pts" if tier != "A" else "", "coc_6.75_full_expense_pct": round(coc, 1) if coc is not None else "", "dscr_6.75": round(dscr, 2) if dscr is not None else "", "break_even_rent_for_bar": round(bar / 100 * price) if price else "", "novice_grade": grade, "photo_c_rating": j.get("c", ""), "photo_note": j.get("pnote", ""), "condition_note": ((f"[{jflag}] " if jflag else "") + (j.get("cond") or "")), "jurisdiction_flag": jflag, "crime_cell": crime_cell(cr, MMDD) if cr else f"maps needed {z}", "block_group": cr["bg"] if cr else "", "crime_zip": crime, "drive_h_williamsburg": drive if drive is not None else "", "flood_factor": j.get("flood") if j.get("flood") is not None else (f.get("flood") if f.get("flood") is not None else ""), "last_sold": j.get("last_sold", ""), "score": score, "why": "; ".join(why), "verdict": verdict, "region": REGION, "url": f["url"]})
    if no_j: note(f"  {len(no_j)} facts rows without a judgment were skipped (first: {no_j[0]})")
    out.sort(key=lambda o: (ORDER[o["verdict"]], -(o["score"] if o["score"] != "" else -999)))
    if out: wr(RUN + "results.csv", out)
    rows14 = rd(F14); f14fields = list(rows14[0].keys()); IFIELD = f14fields[0]   # the header starts with a BOM, so the first field reads as "ï»¿i", not "i"; writing the row under "i" silently dropped it (rows folded on 9/21 had a blank i)
    by_key = {}   # street-level match: portals disagree on ZIPs, unit suffixes and spellings (parsers.key folds Mount/Mt, North/N etc. since 2026-09-28)
    for r in rows14: by_key.setdefault(key(r["address"]), r)
    wnum = max([int(m.group(1)) for r in rows14 for m in [re.match(r"^w(\d+)$", (r[IFIELD] or "").strip())] if m] + [0])
    n_new = 0; n_ref = 0
    def fold_status(o):   # 2026-09-29: the folded row said ACTIVE whatever the detail page said (seven 9/28 rows were CONTINGENT or unread); SOLD and OFF MARKET rows are not folded at all
        s = str(o.get("status_" + DATE) or "").upper()
        if s.startswith(("SOLD", "OFF MARKET", "EXPIRED", "WITHDRAWN")): return None
        if s.startswith("CONTINGENT"): return f"CONTINGENT ({DATE})"
        if s.startswith("PENDING"): return f"PENDING ({DATE})"
        if s.startswith("COMING SOON"): return f"COMING SOON ({DATE})"
        return "ACTIVE (for sale)" if s == "ACTIVE" else "ACTIVE (status unverified)"
    done14 = set()   # 2026-09-30: re-score the rows this run folded; nothing else in the row moves. One result per file 14 row: the one with the row's own URL, else the best verdict (two portals' pages of one listing share a street key)
    for o in (sorted(out, key=lambda o: 0 if (by_key.get(key(o["address"])) or {}).get("url") == o["url"] else 1) if rescore else []):
        r = by_key.get(key(o["address"]))
        if r is None or not mine(r) or id(r) in done14: continue
        done14.add(id(r))
        m = re.match(re.escape(same_day) + r" (ENTRANT|NEAR-MISS|OUT \([^)]*\)|OUT)", r["event"]); oldv = m.group(1) if m else ""
        before = (str(r["score"]), str(r["coc_6.75"]), str(r["dscr"]))
        r["score"] = o["score"]; r["coc_6.75"] = o["coc_6.75_full_expense_pct"]; r["dscr"] = o["dscr_6.75"]; r["why"] = o["why"]; r["crime"] = o["crime_cell"]   # 2026-09-30: the crime cell follows the read
        flipped = bool(oldv) and oldv != o["verdict"]
        if flipped:
            r["event"] = r["event"].replace(f"{same_day} {oldv}", f"{same_day} {o['verdict']} (was {oldv}; re-scored {TODAY} on {o['rent_basis'] or 'current rules'})", 1)
        if flipped or before != (str(r["score"]), str(r["coc_6.75"]), str(r["dscr"])):
            n_ref += 1; note(f"  re-scored {r[IFIELD]}: {o['address']} | rent {o['rent_used']} ({o['rent_basis']}) at ${o['price']} | score {before[0]} -> {o['score']} | CoC {before[1]} -> {o['coc_6.75_full_expense_pct']} | {(oldv + ' -> ' + o['verdict']) if flipped else o['verdict']}")
    for o in ([] if rescore else out):
        if o["verdict"] not in ("ENTRANT", "NEAR-MISS"): continue
        st14 = fold_status(o)
        if st14 is None: note(f"  not folded, the page shows {o['status_' + DATE]}: {o['address']} ({o['verdict']} {o['score']})"); continue
        k = key(o["address"]); r = by_key.get(k)
        row = {IFIELD: "", "address": o["address"], "price": o["price"], "status": st14, "event": f"{same_day} {o['verdict']} UNREVIEWED" + ("" if REGION == "ncva" else f" [{REGION}]"), "score": o["score"], "coc_6.75": o["coc_6.75_full_expense_pct"], "dscr": o["dscr_6.75"], "novice": novice_cell(o["novice_grade"], o["photo_c_rating"], o["condition_note"], o["flood_factor"], f"{int(DATE[5:7])}/{int(DATE[8:10])}"), "crime": o["crime_cell"], "drive_wb": o["drive_h_williamsburg"], "drive_ec": "", "flood": o["flood_factor"], "historic": "", "why": o["why"], "note": (o["condition_note"] or "")[:300], "url": o["url"]}
        if r is None:
            wnum += 1; row[IFIELD] = f"w{wnum}"; n_new += 1; rows14.append(row); by_key[k] = row
        elif r["event"].startswith(same_day) and "UNREVIEWED" in r["event"] and (REGION == "ncva" or f"[{REGION}]" in r["event"]):
            # 2026-09-28: a rerun on the same date (normally the one after the step-8 constants lookup) re-scores the row it folded earlier instead of leaving the pre-constant score and blank crime/drive columns in place; i, drive_ec and historic are kept
            for f_ in ("price", "status", "event", "score", "coc_6.75", "dscr", "novice", "crime", "drive_wb", "flood", "why", "note", "url"): r[f_] = row[f_]
            n_ref += 1; note(f"  re-scored same-date UNREVIEWED row {r[IFIELD]}: {o['address']} ({o['verdict']} {o['score']}, status {row['status']})")
        else: note(f"  already in file 14: {o['address']} ({o['verdict']} {o['score']})")
    if (n_new or n_ref) and not dry:
        def k14(r):
            active = r["status"].startswith("ACTIVE"); s = num(r["score"]); return (0 if active else 1, -(s if s is not None else -999))
        rows14.sort(key=k14); wr(F14, rows14, f14fields)
    folded_total = sum(1 for r in rows14 if r["event"].startswith(same_day) and (REGION == "ncva" or f"[{REGION}]" in r["event"]))   # every row this date's sweep folded, whichever pass folded it (the tally used to count only the latest pass, so a rerun wrote 0)
    note(f"## {'Re-score ' + TODAY + ', verdicts' if rescore else 'Verdicts'} ({len(out)} underwritten; {n_new} new rows folded into file 14 as UNREVIEWED, {n_ref} same-date rows re-scored, {folded_total} rows carry this sweep date{' [DRY RUN, file 14 untouched]' if dry else ''})")
    for o in out: note(f"  {o['verdict']:24s} | {o['address'][:44]:44s} | ${o['price']} | rent {o['rent_used']} r2p {o['rent_to_price_pct']} | CoC {o['coc_6.75_full_expense_pct']} DSCR {o['dscr_6.75']} | score {o['score']} | {o['novice_grade']} {o['photo_c_rating']} | {o['why']}" + ("" if o['status_' + DATE] == "ACTIVE" else f" | page status {o['status_' + DATE] or 'unknown'}"))
    if unknown:
        note("## Constants needed (defaults used; add to constants.json with provenance)")
        for u in sorted(unknown): note("  " + u)
    if dry: print("  [dry run: weekly_tally.csv untouched]"); sys.exit(0)
    if rescore: print("  [re-score: weekly_tally.csv keeps the counts of the day of the run]"); sys.exit(0)
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
        if r is not None and (DATE in (r["status"] or "") or DATE in (r["event"] or "")):   # 2026-09-29: folded or refreshed earlier today (another region's run); the second refresh used to re-stamp the row and overwrite its event
            changes.append({"address": t["address"], "change": "already refreshed today", "detail": (r["status"] or "")[:60]}); continue
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
        elif st == "OFF MARKET" and not old_status.startswith("OFF MARKET"): r["status"] = f"OFF MARKET ({DATE})"; ev.append("off market")   # 2026-09-29: guarded like PENDING and CONTINGENT
        elif st == "ACTIVE" and not old_status.startswith("ACTIVE"): r["status"] = "ACTIVE (for sale)"; ev.append("back to active")
        if st == "ACTIVE" and newp and old_price and abs(newp - old_price) > 0.5:
            ev.append(f"price {'cut' if newp < old_price else 'up'} ${old_price:,.0f} -> ${newp:,}"); r["price"] = str(newp)
        if ev:
            new_ev = f"{'; '.join(ev)} ({DATE}; was: {old_status})"[:200]; old_ev = (r["event"] or "").strip()   # 2026-09-29: appended, so "weekly sweep <date> ... UNREVIEWED [region]" survives; the old text is cut from its end to keep the field under 300 characters
            r["event"] = (old_ev[:max(0, 300 - len(new_ev) - 3)].rstrip() + " | " + new_ev) if old_ev else new_ev
            changes.append({"address": t["address"], "change": "; ".join(ev), "detail": d.get("last_event", "")})
        else: changes.append({"address": t["address"], "change": "no change", "detail": f"{st} dom {d.get('dom')}"})
    if changes: wr(RUN + "tracked_changes.csv", changes)
    if not dry: wr(F14, rows14, f14fields)
    real = [c for c in changes if c["change"] not in ("no change", "already refreshed today")]; n_today = sum(1 for c in changes if c["change"] == "already refreshed today")
    note(f"## Tracked rows refreshed ({len(tracked)} checked, {len(real)} changes or problems{f', {n_today} left alone as already stamped today' if n_today else ''}{' [DRY RUN]' if dry else ''})")
    for c in real: note(f"  {c['change'][:40]:40s} | {c['address'][:44]:44s} | {c['detail'][:90]}")

if stage == "report":
    parts = open(RUN + "report_parts.txt", encoding="utf-8").read() if os.path.exists(RUN + "report_parts.txt") else "(no parts)"
    open(RUN + "report.md", "w", encoding="utf-8").write(parts + f"\n\nFiles: {RUN}\n"); print(parts)

if stage == "help": print(__doc__ or open(__file__, encoding="utf-8").read().split("import csv")[0])

