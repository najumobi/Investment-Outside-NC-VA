# fix_defects_0929.py - one-shot data repair that goes with the 2026-09-29 parsers.key() change (memo 65, section 8, item 8).
# Run from anywhere: python "<PIPE>/fix_defects_0929.py" [--dry]. Safe to re-run: it backs up first and skips anything already repaired.
#   1. seen_index.csv: re-key every row with the 2026-09-29 parsers.key (a number range, a "#unit" or an "& 761R" companion collapse to the first
#      number, Way reads as St, a trailing street-type token is dropped) and merge rows that now share a key: the cross-portal twins that took
#      seven of the 150 regional detail slots on 9/28. The Redfin row is kept where the pair has one; detail_pending stays "yes" if either row had it.
#      Without this re-key the next ingest would see every listing as new and mark every old row gone.
#   2. file 14: report (do not drop) rows that share a key with another row, so Najum can decide about any twin that folded twice.
import csv, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parsers import key
CAMP = "C:/Users/najum/Dropbox/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign/"
PIPE = CAMP + "_pipeline/"
F14 = CAMP + "14 Live status and ranking of the 42 tracked candidates (2026-09-11).csv"
SEEN = PIPE + "seen_index.csv"
DRY = "--dry" in sys.argv; TAG = "0929"
def rd(fn): return list(csv.DictReader(open(fn, encoding="utf-8")))
def wr(fn, rows, fields):
    if DRY: print(f"  [dry] would write {len(rows)} rows to {os.path.basename(fn)}"); return
    with open(fn, "w", newline="", encoding="utf-8") as f: w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
def backup(fn, name):
    dst = PIPE + f"_backup_{name}_before_{TAG}" + os.path.splitext(fn)[1]
    if os.path.exists(dst): print(f"  backup exists: {os.path.basename(dst)}"); return
    if not DRY: shutil.copy2(fn, dst)
    print(f"  backed up {os.path.basename(fn)} -> {os.path.basename(dst)}")

print("1. seen_index.csv re-key and merge")
backup(SEEN, "seen_index")
seen = rd(SEEN); fields = list(seen[0].keys()); merged = {}; n_merge = 0; n_rekey = 0; pend0 = sum(1 for r in seen if r.get("detail_pending") == "yes")
for e in seen:
    k = key(e["address"]) + "|" + e["zip"]
    if k != e["key"]: n_rekey += 1
    if k not in merged:
        e["key"] = k; merged[k] = e; continue
    m = merged[k]; n_merge += 1
    if "zillow.com" in (m.get("url") or "") and "redfin.com" in (e.get("url") or ""):   # keep the Redfin row as the primary, as the 0928 repair did
        e["key"] = k; merged[k] = e; e, m = m, e
    print(f"  merge: '{e['address']}' ({e['source'] or 'seed'}, first {e['first_seen']}) into '{m['address']}' ({m['source'] or 'seed'}, first {m['first_seen']})")
    if e["first_seen"] and (not m["first_seen"] or e["first_seen"] < m["first_seen"]): m["first_seen"], m["price_first"] = e["first_seen"], e["price_first"]
    if e["last_seen"] and (not m["last_seen"] or e["last_seen"] > m["last_seen"]): m["last_seen"], m["price_last"] = e["last_seen"], e["price_last"]
    if e["status"] == "listed" and m["status"] == "gone": m["status"], m["gone_date"] = "listed", ""
    if e["source"] and m["source"] and e["source"] != m["source"] and m["source"] != "both": m["source"] = "both"
    if e.get("detail_pending") == "yes": m["detail_pending"] = "yes"
    if not m.get("url") and e.get("url"): m["url"] = e["url"]
    m["note"] = (m["note"] + f"; merged {e['address']} ({e['url']}) on 2026-09-29 after the twin-address key fix").strip("; ")
print(f"  {len(seen)} rows -> {len(merged)} after {n_merge} merge(s); {n_rekey} keys rewritten; detail_pending rows {sum(1 for r in merged.values() if r.get('detail_pending') == 'yes')} (was {pend0})")
if n_merge or n_rekey: wr(SEEN, list(merged.values()), fields)

print("2. file 14 rows that share a key (reported only)")
rows = rd(F14); IF = list(rows[0].keys())[0]; groups = {}
for r in rows: groups.setdefault(key(r["address"]), []).append(r)
dup = {k: g for k, g in groups.items() if len(g) > 1}
for k, g in dup.items(): print(f"  '{k}': " + " | ".join(f"{r[IF] or '-'} {r['address']} [{r['status'][:18]}] {('UNREVIEWED' if 'UNREVIEWED' in r['event'] else '')}" for r in g))
print(f"  {len(dup)} group(s) share a key; nothing changed in file 14")
print("done" + (" (dry run, nothing written)" if DRY else ""))
