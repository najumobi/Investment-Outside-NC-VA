# fix_defects_0928.py - one-shot repair for the two defects the 2026-09-21 weekly sweep logged (README "Weekly sweeps log", note of 2026-09-21).
# Run from anywhere: python "<PIPE>/fix_defects_0928.py" [--dry]. Safe to re-run: it backs up first and skips anything already repaired.
#   1. seen_index.csv: re-key every row with the 2026-09-28 parsers.key (Mount/Mt, North/N, ...) and merge rows that now share a key
#      (the Zillow "749 Mount Airy St" row merges into the Redfin "749 Mt Airy St" row).
#   2. file 14: drop the duplicate UNREVIEWED row a weekly sweep folded when a tracked row with the same normalised street already existed,
#      carrying its URL, photo judgment and rerun score into the tracked row's note.
#   3. _sweeps/weekly_tally.csv: folded_into_14 for a date = rows whose event starts with "weekly sweep <date>" (the rerun had overwritten 3 with 0).
# Rows 20 (413-415 Gilmer Cir) and 59 (307 N Church St), the other two rows the 9/21 pass folded with pre-constant scores, were already
# re-scored by the 9/25 and 9/26 advisory passes (files 47/48) and are not touched here.
import csv, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parsers import key
CAMP = "C:/Users/najum/Dropbox/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign/"
PIPE = CAMP + "_pipeline/"; SWEEPS = CAMP + "_sweeps/"
F14 = CAMP + "14 Live status and ranking of the 42 tracked candidates (2026-09-11).csv"
SEEN = PIPE + "seen_index.csv"; TALLY = SWEEPS + "weekly_tally.csv"
DRY = "--dry" in sys.argv; TAG = "0928"
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
seen = rd(SEEN); fields = list(seen[0].keys()); merged = {}; n_merge = 0
for e in seen:
    k = key(e["address"]) + "|" + e["zip"]
    if k not in merged:
        e["key"] = k; merged[k] = e; continue
    m = merged[k]; n_merge += 1
    print(f"  merge: '{e['address']}' ({e['source'] or 'seed'}, first {e['first_seen']}) into '{m['address']}' ({m['source'] or 'seed'}, first {m['first_seen']})")
    if e["first_seen"] < m["first_seen"]: m["first_seen"], m["price_first"] = e["first_seen"], e["price_first"]
    if e["last_seen"] > m["last_seen"]: m["last_seen"], m["price_last"] = e["last_seen"], e["price_last"]
    if e["status"] == "listed" and m["status"] == "gone": m["status"], m["gone_date"] = "listed", ""
    if e["source"] and m["source"] and e["source"] != m["source"] and m["source"] != "both": m["source"] = "both"
    m["note"] = (m["note"] + f"; merged {e['address']} ({e['url']}) on 2026-09-28 after the Mount/Mt matching fix").strip("; ")
print(f"  {len(seen)} rows -> {len(merged)} after {n_merge} merge(s)")
if n_merge: wr(SEEN, list(merged.values()), fields)

print("2. file 14 duplicate UNREVIEWED rows")
backup(F14, "14")
rows = rd(F14); f14 = list(rows[0].keys()); IF = f14[0]; groups = {}
for r in rows: groups.setdefault(key(r["address"]), []).append(r)
drop = []
for k, g in groups.items():
    if len(g) < 2: continue
    sweeps = [r for r in g if r["event"].startswith("weekly sweep") and "UNREVIEWED" in r["event"]]
    keep = [r for r in g if r not in sweeps]
    if len(keep) != 1 or not sweeps:
        print(f"  ambiguous group, left alone: {[r['address'] for r in g]}"); continue
    t = keep[0]
    for d in sweeps:
        print(f"  drop '{d['address']}' (i='{d[IF]}', score {d['score']}) -> keep '{t['address']}' (i='{t[IF]}', score {t['score']})")
        m = re.match(r"weekly sweep (\d{4}-\d{2}-\d{2})", d["event"]); sdate = m.group(1) if m else ""
        final = d   # the row holds the score of the pass that folded it; the date's results.csv holds the last pass's (post-constant) score
        rfn = SWEEPS + sdate + "/results.csv"
        if sdate and os.path.exists(rfn):
            for rr in rd(rfn):
                if rr["address"] == d["address"]: final = {"score": rr["score"], "coc_6.75": rr["coc_6.75_full_expense_pct"], "dscr": rr["dscr_6.75"], "why": rr["why"]}
        extra = (f"weekly sweep {sdate} folded this property a second time from its Zillow row ({d['url']}): photo {d['novice']}, {d['note']} "
                 f"Fold score {d['score']}; last underwrite pass that day scored it {final['score']} (CoC {final['coc_6.75']}, DSCR {final['dscr']}, {final['why']}); "
                 f"duplicate row removed 2026-09-28 after the Mount/Mt matching fix.")
        t["note"] = (t["note"] + " | " + extra).strip(" |")
        if not t["event"]: t["event"] = "Zillow duplicate merged 2026-09-28"
        drop.append(d)
if drop:
    rows = [r for r in rows if r not in drop]; wr(F14, rows, f14)
print(f"  {len(drop)} duplicate row(s) removed; file 14 now {len(rows)} rows")

print("3. weekly_tally.csv folded_into_14")
backup(TALLY, "tally")
tally = rd(TALLY); tfields = list(tally[0].keys()); changed = 0
for t in tally:
    if t["date"] != "2026-09-21": continue   # the 9/14 row deliberately records the scheduled run (0 folded), not the hand-run build test whose two rows also carry that date
    n = sum(1 for r in rows if r["event"].startswith(f"weekly sweep {t['date']}"))
    if str(n) != str(t["folded_into_14"]) and n > 0:
        print(f"  {t['date']}: folded_into_14 {t['folded_into_14']} -> {n}"); t["folded_into_14"] = n; changed += 1
if changed: wr(TALLY, tally, tfields)
print(f"  {changed} tally row(s) corrected")
print("done" + (" (dry run, nothing written)" if DRY else ""))
