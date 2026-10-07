# sweep_remote.py - runs INSIDE the Composio remote workbench (never locally). Written 2026-09-14.
# The weekly task bootstraps it with:
#   import base64; res,_ = run_composio_tool("DROPBOX_READ_FILE", {"path": BASE+"/_pipeline/sweep_remote.py"}, print_schema_for_tool=False)
#   exec(base64.b64decode(res["data"]["file_content_bytes"]).decode())
# then calls remote_setup(), remote_fetch_lists(part), remote_parse_lists(), remote_details(urls, name).
# 2026-09-29 (memo 65): STATE survives a re-exec of this file, remote_setup refuses to start over another region's fetched pages (the 9/28
#   collision), dbx_write only writes into the folder the kernel was set up for, the health check counts never-fetched pages and returns
#   health["halt"], and remote_details_batched fetches 25 pages per cell (the 180-second cell limit).
# Helpers provided by the workbench: run_composio_tool(tool_slug, arguments, account=...), upload_local_file(path).
import json, base64, os, re, time, csv, io
from concurrent.futures import ThreadPoolExecutor
BASE = "/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign"
ACC = ["brightdata_vadium-cur", "brightdata_archie-laura", "brightdata_morula-bulgy", "brightdata_scarf-shruff"]
STATE = globals().get("STATE") if isinstance(globals().get("STATE"), dict) else {"date": None, "region": None, "zips": [], "urls": [], "pages": {}, "bad": [], "details": {}, "touched": 0}   # 2026-09-29: keep the kernel's state across a re-exec so a second session cannot silently reset a running fetch

def dbx_read(path, tries=6, wait=20):
    """Download a file from Dropbox; retries while a freshly written local file is still syncing up."""
    for i in range(tries):
        res, err = run_composio_tool("DROPBOX_READ_FILE", {"path": path}, print_schema_for_tool=False)
        d = res.get("data", res) if isinstance(res, dict) else {}
        b = d.get("file_content_bytes") if isinstance(d, dict) else None
        if b: return base64.b64decode(b)
        c = (d.get("content") or {}) if isinstance(d, dict) else {}
        if isinstance(c, dict) and c.get("s3url"):
            import requests; r = requests.get(c["s3url"], timeout=60); r.raise_for_status(); return r.content
        if i < tries - 1: time.sleep(wait)
    raise RuntimeError(f"dropbox read failed for {path}: {err or json.dumps(res)[:300]}")

def dbx_write(path, data, mimetype="text/plain"):
    if STATE.get("date"):   # 2026-09-29: the 9/28 collision wrote the Ohio fetch into the Pittsburgh folder
        exp = run_folder(STATE["date"], STATE.get("region") or "ncva")
        if not path.startswith(exp + "/"): raise RuntimeError(f"refusing to write {path}: this kernel is set up for {exp} (region {STATE.get('region')}, {STATE['date']})")
    os.makedirs("/mnt/files/out", exist_ok=True); p = "/mnt/files/out/" + os.path.basename(path)
    open(p, "wb").write(data if isinstance(data, bytes) else data.encode("utf-8"))
    staged, serr = upload_local_file(p)
    if serr: raise RuntimeError("stage failed: " + str(serr))
    res, uerr = run_composio_tool("DROPBOX_UPLOAD_FILE", {"path": path, "mode": "overwrite", "content": {"name": os.path.basename(path), "mimetype": mimetype, "s3key": staged.get("s3key")}}, print_schema_for_tool=False)
    d = res.get("data", res) if isinstance(res, dict) else {}
    if not (isinstance(d, dict) and d.get("path_display")): raise RuntimeError("upload failed: " + (uerr or json.dumps(res)[:300]))
    return d["path_display"]

def fetch(url, i, tries=2):
    acc = ACC[i % 4]; last = None
    for t in range(tries):
        try:
            res, txt = run_composio_tool("BRIGHTDATA_WEB_UNLOCKER", {"url": url, "zone": "mcp_unlocker", "format": "raw", "data_format": "markdown", "country": "us"}, print_schema_for_tool=False, account=ACC[(i + t) % 4])
            d = res.get("data", res) if isinstance(res, dict) else {}
            c = (d.get("content") or "") if isinstance(d, dict) else ""; h = (d.get("headers") or {}) if isinstance(d, dict) else {}
            if c and len(c) > 1500: return (url, c, h)
            last = h.get("x-brd-error") or txt or "empty"
        except Exception as ex: last = repr(ex)[:200]
        time.sleep(2)
    return (url, "", {"x-brd-error": str(last)[:200]})

def run_folder(date, region="ncva"):
    """_sweeps/<date> for the Monday NC/VA sweep; _sweeps/<date>-<region> for the Tuesday-Thursday regions (added 2026-09-28)."""
    return f"{BASE}/_sweeps/{date}" + ("" if region == "ncva" else f"-{region}")

def remote_reset():
    """Forget every fetched page and detail (2026-09-29). remote_setup calls it; call it by hand only to abandon a dead run."""
    STATE.update(date=None, region=None, zips=[], urls=[], pages={}, bad=[], details={}, touched=0)

def remote_setup(date, region="ncva", limit=None, force=False):
    """Load parsers.py and the region's ZIP list from Dropbox; build the list-page URL set. region: ncva (sweep_zips.json) | phila | pitt | ohio (sweep_zips_<region>.json). limit: first N ZIPs only (smoke tests).
    2026-09-29: refuses while the kernel holds another region's pages fetched within the last three hours (four 'Run now' clicks in one minute on 9/28 made the Ohio session fetch the Pittsburgh list); older state is a finished or dead run
    (this sandbox persists from one weekday to the next) and is cleared; force=True overrides the refusal when that run is known to be dead."""
    held = STATE.get("region"); n_held = sum(1 for v in (STATE.get("pages") or {}).values() if v and v[0]); age_h = (time.time() - (STATE.get("touched") or 0)) / 3600
    if held and held != region and n_held and age_h < 3 and not force:
        raise RuntimeError(f"refusing remote_setup({date!r}, {region!r}): this kernel holds {n_held} pages fetched for region {held} ({STATE.get('date')}) {age_h*60:.0f} minutes ago; another region's sweep is running in the same sandbox. Wait for it to finish, or pass force=True only if you are certain it is dead.")
    if held and held != region and n_held: print(f"cleared a stale {held} run ({STATE.get('date')}, last touched {age_h:.1f} h ago) from this kernel")
    remote_reset()
    src = dbx_read(BASE + "/_pipeline/parsers.py"); os.makedirs("/mnt/files/pass2", exist_ok=True); open("/mnt/files/pass2/parsers.py", "wb").write(src); exec(src.decode("utf-8"), globals())
    zfile = "sweep_zips.json" if region == "ncva" else f"sweep_zips_{region}.json"
    zips = json.loads(dbx_read(BASE + "/_pipeline/" + zfile).decode("utf-8"))
    if limit: zips = zips[:int(limit)]
    urls = []
    for z in zips:
        urls.append(z["redfin"])
        if z.get("zillow"): urls.append(z["zillow"])
    STATE.update(date=date, region=region, zips=zips, urls=urls, pages={}, bad=[], details={})
    print(f"setup ok: region {region}, {len(zips)} ZIPs, {len(urls)} list pages; parsers: make_round={'make_round' in globals()} parse_detail={'parse_detail' in globals()}")
    return len(urls)

def remote_fetch_lists(part, nparts=5, workers=10):
    """Fetch one slice of the list pages (call for part = 0..nparts-1; each call stays well under the 180 s cell limit)."""
    urls = STATE["urls"]; chunk = [u for j, u in enumerate(urls) if j % nparts == part]
    t = time.time(); STATE["touched"] = t
    with ThreadPoolExecutor(max_workers=workers) as ex: res = list(ex.map(lambda p: fetch(p[1], p[0]), enumerate(chunk)))
    ok = 0
    for u, c, h in res:
        STATE["pages"][u] = (c, h)
        if c: ok += 1
    print(f"part {part}: {ok}/{len(chunk)} pages ok in {round(time.time()-t,1)} s; total fetched {sum(1 for v in STATE['pages'].values() if v[0])}/{len(urls)}")
    return ok, len(chunk)

def remote_parse_lists(retry_bad=True):
    """Parse all fetched list pages, retry bad ones once, write listings_raw.csv + fetch_counts.json to _sweeps/<date>/ on Dropbox."""
    date = STATE["date"]; zips = [z["zip"] for z in STATE["zips"]]; STATE["touched"] = time.time()
    merged, counts, bad, add_pages = make_round(zips)
    pages = [(u, c, h.get("x-brd-status-code")) for u, (c, h) in STATE["pages"].items()]
    add_pages(pages)
    if retry_bad and bad:
        again = [fetch(u, i + 7) for i, (u, b, n) in enumerate(bad)]
        merged2, counts2, bad2, add2 = make_round(zips); add2(pages); add2([(u, c, h.get("x-brd-status-code")) for u, c, h in again if c])
        merged, counts, bad = merged2, counts2, bad2
    rows = sorted(merged.values(), key=lambda r: (r["page_zip"], r["address"]))
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=fields + ["zip", "zlabel"], extrasaction="ignore"); w.writeheader()
    for r in rows: w.writerow({**{k: r.get(k, "") for k in fields}, "zip": r.get("zip", r.get("page_zip", "")), "zlabel": r.get("zlabel", "")})
    never = [u for u in STATE["urls"] if u not in STATE["pages"]]   # 2026-09-29: pages a part never fetched were invisible to the health check (the 9/28 collision file had 40 of them and would have passed)
    health = {"date": date, "zips": len(zips), "pages": len(STATE["urls"]), "fetched_ok": sum(1 for v in STATE["pages"].values() if v[0]), "never_fetched": len(never), "bad": [(u, str(b)[:80], n) for u, b, n in bad], "counts": counts, "rows": len(rows)}
    rf = run_folder(date, STATE.get("region", "ncva")); health["region"] = STATE.get("region", "ncva")
    p1 = dbx_write(f"{rf}/listings_raw.csv", buf.getvalue(), "text/csv"); p2 = dbx_write(f"{rf}/fetch_counts.json", json.dumps(health, indent=1), "application/json")
    bad_share = (len(bad) + len(never)) / max(1, len(STATE["urls"])); health["halt"] = bad_share >= 0.2   # a fifth or more: one skipped part of five is exactly a fifth
    print(f"rows {len(rows)} | bad pages {len(bad)} | never fetched {len(never)} | {bad_share:.0%} of {len(STATE['urls'])} pages failed or unfetched | wrote {p1} and {p2}")
    if health["halt"]: print("HALT: 20% or more of the list pages failed or were never fetched; do not treat this as a real sweep (ingest refuses such a fetch too)")
    return health   # end the cell with `health` so the dict comes back even when printed output does not

def remote_details(urls, name, workers=8):
    """Fetch detail pages (tracked rows or shortlist), parse them, write <name>.json to _sweeps/<date>/ on Dropbox."""
    date = STATE["date"]; t = time.time(); STATE["touched"] = t
    with ThreadPoolExecutor(max_workers=workers) as ex: res = list(ex.map(lambda p: fetch(p[1], p[0]), enumerate(urls)))
    out = {}
    for u, c, h in res:
        d = parse_detail(u, c, h) if "redfin.com" in u else parse_zillow_detail(u, c, h)
        d["excerpt"] = (d.get("remarks") or flat(c)[:300]) if c else ""
        out[u] = d
    p = dbx_write(f"{run_folder(date, STATE.get('region', 'ncva'))}/{name}.json", json.dumps(out, indent=1), "application/json")
    print(f"{name}: {sum(1 for d in out.values() if d.get('ok'))}/{len(urls)} pages ok in {round(time.time()-t,1)} s -> {p}")
    for u, d in out.items(): print(f"  {d.get('status','?'):10s} ${d.get('price') or 0:>8,} dom {d.get('dom')} | {d.get('page_address') or u[:70]}" + (" | REDIRECTED" if d.get("redirected_to") else ""))
    return out

def remote_details_batched(urls, name, size=25, workers=8):
    """Resumable remote_details for the 180-second cell limit (2026-09-29): each call fetches the next `size` URLs of `name` not yet done, keeps them in the kernel,
    and writes <name>.json to the run folder once every URL is done. Call it once per cell until it returns 'done ...'; the return value is the progress line,
    so end the cell with the call (printed output is not always returned)."""
    store = STATE.setdefault("details", {}).setdefault(name, {})
    todo = [u for u in urls if u not in store][:size]; t = time.time(); STATE["touched"] = t
    if todo:
        with ThreadPoolExecutor(max_workers=workers) as ex: res = list(ex.map(lambda p: fetch(p[1], p[0]), enumerate(todo)))
        for u, c, h in res:
            d = parse_detail(u, c, h) if "redfin.com" in u else parse_zillow_detail(u, c, h)
            d["excerpt"] = (d.get("remarks") or flat(c)[:300]) if c else ""
            store[u] = d
    done = sum(1 for u in urls if u in store)
    if done < len(urls):
        msg = f"{name}: {done}/{len(urls)} pages fetched ({len(todo)} this cell in {round(time.time()-t,1)} s); call remote_details_batched again for the next {min(size, len(urls)-done)}"
        print(msg); return msg
    out = {u: store[u] for u in urls}
    p = dbx_write(f"{run_folder(STATE['date'], STATE.get('region', 'ncva'))}/{name}.json", json.dumps(out, indent=1), "application/json")
    msg = f"done: {name}: {sum(1 for d in out.values() if d.get('ok'))}/{len(urls)} pages ok -> {p}"
    print(msg); return msg
