# measure_zip_crime_1004.py - memo 72 phase B1 (desktop session, 2026-10-04): for each of the four sweep lists, the share of each ZIP's geocoded
#   listings (latest scored.csv of the region) whose block group reads Robbery F in model/crime_bg.json, and in NC/VA the share that meets the
#   NC/VA knockout (Robbery F with Burglary or Vandalism F). Block groups come from model/geo_cache_bg.json where the sweep has them; the rest
#   are geocoded once through the Census batch geocoder (the same call ingest makes, with the 2020 block in the geographies), cached in the
#   same file in the same shape ({"bg", "lat", "lon"}), with the one-line geocoder as the fallback for a batch miss.
#   Stages: `geocode` fills the cache; `table` writes "72c Sweep ZIPs by share of listings in Robbery-F block groups (2026-10-04).csv".
#   A listing belongs to the ZIP whose list page returned it (scored.csv page_zip); listings_last_two_runs counts the rows the ZIP's pages
#   returned on the region's last two runs (listings_raw.csv page_zip), the standing rule's "no listing on the last two runs" test.
import csv, io, json, os, re, sys, time, uuid, urllib.request, urllib.parse
CAMP = "C:/Users/najum/Dropbox/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign/"
PIPE = CAMP + "_pipeline/"; MODEL = PIPE + "model/"; SWEEPS = CAMP + "_sweeps/"
BGC_FN = MODEL + "geo_cache_bg.json"; CB_FN = MODEL + "crime_bg.json"
OUT = CAMP + "72c Sweep ZIPs by share of listings in Robbery-F block groups (2026-10-04).csv"
RUNS = {"ncva": ["2026-09-21", "2026-09-28"], "phila": ["2026-09-28-phila", "2026-09-29-phila"], "pitt": ["2026-09-28-pitt", "2026-09-30-pitt"], "ohio": ["2026-09-28-ohio", "2026-10-01-ohio"]}
LISTS = {"ncva": "sweep_zips.json", "phila": "sweep_zips_phila.json", "pitt": "sweep_zips_pitt.json", "ohio": "sweep_zips_ohio.json"}
F = 12 / 13
stage = sys.argv[1] if len(sys.argv) > 1 else "table"

def rd(fn): return list(csv.DictReader(open(fn, encoding="utf-8")))
def jl(fn): return json.load(open(fn, encoding="utf-8"))
def js_atomic(fn, obj):
    tmp = fn + ".tmp"; json.dump(obj, open(tmp, "w", encoding="utf-8"), indent=1); os.replace(tmp, fn)
def clean_street(a):   # weekly_sweep.py ingest
    parts = [x.strip() for x in a.split(",")]; st = re.sub(r"\s+(Unit|Apt|#|Lot).*$", "", parts[0], flags=re.I); st = re.sub(r"^(\d+)\s*[-&/]\s*\d+\s", r"\1 ", st); return st, parts

latest = {reg: rd(SWEEPS + runs[-1] + "/scored.csv") for reg, runs in RUNS.items()}
bgc = jl(BGC_FN) if os.path.exists(BGC_FN) else {}

if stage == "geocode":
    need = []
    for reg, rows in latest.items():
        for r in rows:
            if r.get("tract") and not (isinstance(bgc.get(r["address"]), dict) and bgc[r["address"]].get("bg")): need.append(r["address"])
    need = list(dict.fromkeys(need)); print(f"{len(need)} geocoded listings lack a cached block group; batch geocoding in chunks of 800", flush=True)
    for start in range(0, len(need), 800):
        chunk = need[start:start + 800]; buf = io.StringIO(); w = csv.writer(buf); ids = {}
        for i, a in enumerate(chunk):
            st, parts = clean_street(a)
            if len(parts) < 3: continue
            stz = parts[-1].split(); w.writerow([i, st, parts[-2], stz[0], stz[-1]]); ids[i] = a
        b = uuid.uuid4().hex
        body = ("--%s\r\nContent-Disposition: form-data; name=\"addressFile\"; filename=\"a.csv\"\r\nContent-Type: text/csv\r\n\r\n%s\r\n--%s\r\nContent-Disposition: form-data; name=\"benchmark\"\r\n\r\nPublic_AR_Current\r\n--%s\r\nContent-Disposition: form-data; name=\"vintage\"\r\n\r\nCurrent_Current\r\n--%s--\r\n" % (b, buf.getvalue(), b, b, b)).encode()
        req = urllib.request.Request("https://geocoding.geo.census.gov/geocoder/geographies/addressbatch", data=body, headers={"Content-Type": "multipart/form-data; boundary=" + b, "User-Agent": "Mozilla/5.0"})
        t = time.time(); got = 0
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=900) as resp: out = resp.read().decode("utf-8", "replace")
                break
            except Exception as ex:
                print(f"  batch {start // 800 + 1}: attempt {attempt + 1} failed: {ex}", flush=True); out = ""; time.sleep(20)
        for rec in csv.reader(io.StringIO(out)):
            if len(rec) >= 12 and rec[2] == "Match" and rec[11]:
                try: lon_, lat_ = (float(x) for x in rec[5].split(","))
                except Exception: lon_ = lat_ = None
                bgc[ids[int(rec[0])]] = {"bg": rec[8] + rec[9] + rec[10] + rec[11][:1], "lat": lat_, "lon": lon_}; got += 1
        js_atomic(BGC_FN, bgc); print(f"  batch {start // 800 + 1}: {len(chunk)} sent, {got} matched with a block, {time.time() - t:.0f} s; cache now {len(bgc)}", flush=True)
    # one-line fallback for the misses (a few dozen at most)
    miss = [a for a in need if not (isinstance(bgc.get(a), dict) and bgc[a].get("bg"))]; print(f"{len(miss)} still without a block group; one-line geocoder, cached", flush=True); done = 0
    for a in miss:
        st, parts = clean_street(a); q = urllib.parse.urlencode({"address": st + ", " + ", ".join(parts[1:]), "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"})
        try:
            with urllib.request.urlopen(urllib.request.Request("https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress?" + q, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as resp: d = json.load(resp)
            m = d["result"]["addressMatches"]
            if m: bgc[a] = {"bg": m[0]["geographies"]["2020 Census Blocks"][0]["GEOID"][:12], "lat": m[0]["coordinates"]["y"], "lon": m[0]["coordinates"]["x"]}; done += 1
        except Exception as ex: pass
        if done % 25 == 0: js_atomic(BGC_FN, bgc)
    js_atomic(BGC_FN, bgc); print(f"one-line: {done} of {len(miss)} resolved; cache {len(bgc)} entries", flush=True); sys.exit(0)

cb = jl(CB_FN)["bg"]; out = []
for reg, rows in latest.items():
    lst = jl(PIPE + LISTS[reg]); rank = {z["zip"]: z["rank"] for z in lst}
    raw2 = {}
    for run in RUNS[reg]:
        fn = SWEEPS + run + "/listings_raw.csv"
        for r in (rd(fn) if os.path.exists(fn) else []): raw2[r.get("page_zip") or r.get("zip", "")] = raw2.get(r.get("page_zip") or r.get("zip", ""), 0) + 1
    per = {}
    for r in rows:
        z = r.get("page_zip") or r["zip"]; p = per.setdefault(z, {"listings": 0, "geocoded": 0, "read": 0, "robbery_F": 0, "ncva_rule": 0}); p["listings"] += 1
        if not r.get("tract"): continue
        p["geocoded"] += 1; g = bgc.get(r["address"]); rec = cb.get(g["bg"]) if isinstance(g, dict) and g.get("bg") else None
        if not rec or "R" not in rec: continue
        p["read"] += 1
        if rec["R"] >= F:
            p["robbery_F"] += 1
            if rec.get("B", 0) >= F or rec.get("V", 0) >= F: p["ncva_rule"] += 1
    for z in lst:
        p = per.get(z["zip"], {"listings": 0, "geocoded": 0, "read": 0, "robbery_F": 0, "ncva_rule": 0}); share = round(p["robbery_F"] / p["read"], 2) if p["read"] else ""
        nshare = (round(p["ncva_rule"] / p["read"], 2) if p["read"] else "") if reg == "ncva" else ""
        rule_share = nshare if reg == "ncva" else share
        two = raw2.get(z["zip"], 0)
        if z["zip"] in ("28206", "28303", "23607", "44112", "44103"): dec = "drop (decision 2, memo 72 section 1, accepted 2026-10-04)"
        elif z["zip"] in ("27701", "27703", "27707", "44105", "44120", "44108", "44104"): dec = "keep through the runs of 2026-10-26 (Mon) / 2026-10-29 (Thu), then the standing rule on the survivor count"
        elif two == 0: dec = "drop (standing rule: no listing on the last two runs)"
        elif p["read"] >= 10 and rule_share != "" and rule_share >= 0.9: dec = "drop (standing rule: 90% or more of 10+ read listings meet the region's knockout share)"
        else: dec = "keep"
        out.append({"region": reg, "rank": z["rank"], "zip": z["zip"], "listings": p["listings"], "geocoded": p["geocoded"], "read": p["read"], "robbery_F": p["robbery_F"], "robbery_F_share": share, "ncva_rule_share": nshare, "listings_last_two_runs": two, "decision": dec})
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()), lineterminator="\r\n"); w.writeheader(); w.writerows(out)
print(f"wrote {OUT}: {len(out)} ZIP rows")
for reg in RUNS:
    rows = [o for o in out if o["region"] == reg]; print(f"{reg}: listings {sum(o['listings'] for o in rows)}, geocoded {sum(o['geocoded'] for o in rows)}, read {sum(o['read'] for o in rows)}, Robbery F {sum(o['robbery_F'] for o in rows)}; decisions: " + ", ".join(f"{d.split(' (')[0]} {sum(1 for o in rows if o['decision'] == d)}" for d in sorted({o["decision"] for o in rows})))
