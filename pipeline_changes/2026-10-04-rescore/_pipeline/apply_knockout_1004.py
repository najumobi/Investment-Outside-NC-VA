# apply_knockout_1004.py - memo 72 section 2, phase A2 (decision 1, accepted by Najum 2026-10-04): mark the 35 active rows of file 14
#   that meet the memo 69 section 4.4 crime knockout (file 72a) with 'OUT (crime) applied 2026-10-04: <reason> (memo 69 section 4.4)'
#   appended to the event, leaving status, price, score, crime, novice, why, note and url untouched; sort with the sweep's key
#   (weekly_sweep.py k14 of 2026-10-02: active rows first, then rows with a block-level reading, then score); write back with the BOM and
#   CRLF line endings intact. File 72a carries no URL column, so the match is by the exact address string (unique in file 14), cross-checked
#   on the event prefix 72a recorded. A 72a row that is no longer ACTIVE is skipped and listed.
#   --dry prints the event strings and the row count and changes nothing. Written 2026-10-04 (desktop session).
import csv, io, os, shutil, sys, datetime
CAMP = "C:/Users/najum/Dropbox/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign/"
PIPE = CAMP + "_pipeline/"
F14 = CAMP + "14 Live status and ranking of the 42 tracked candidates (2026-09-11).csv"
F72A = CAMP + "72a Board rows that meet the memo 69 knockout, 35 of 207 active (2026-10-04).csv"
TODAY = "2026-10-04"; TAG = "1004knockout"
BACKUP = PIPE + f"_backup_14_before_{TAG}.csv"
F72B = CAMP + f"72b Knockout applied to the board, 35 rows before and after ({TODAY}).csv"
DRY = "--dry" in sys.argv

def num(x):
    try: return float(str(x).replace(",", "").replace("$", ""))
    except Exception: return None
def k14(r):   # weekly_sweep.py, 2026-10-02
    active = r["status"].startswith("ACTIVE"); s = num(r["score"])
    return (0 if active else 1, 0 if (r.get("crime") or "").startswith("R ") else 1, -(s if s is not None else -999))

raw = open(F14, "rb").read()
assert raw[:3] == b"\xef\xbb\xbf", "file 14 has lost its BOM"
assert b"\r\n" in raw, "file 14 has lost its CRLF endings"
text = raw.decode("utf-8-sig")
rows = list(csv.DictReader(io.StringIO(text))); fields = list(rows[0].keys())
assert fields[:5] == ["i", "address", "price", "status", "event"], fields[:5]
ka = list(csv.DictReader(open(F72A, encoding="utf-8-sig")))
by_addr = {}
for r in rows:
    assert r["address"] not in by_addr, "duplicate address in file 14: " + r["address"]
    by_addr[r["address"]] = r
n_rows_before = len(rows); n_active_before = sum(1 for r in rows if r["status"].startswith("ACTIVE"))

changed = []; skipped = []; problems = []
for a in ka:
    r = by_addr.get(a["address"])
    if r is None: problems.append(f"NOT FOUND in file 14: {a['address']}"); continue
    if not r["status"].startswith("ACTIVE"): skipped.append((a["address"], r["status"])); continue
    if a["event"] and not r["event"].startswith(a["event"][:30]): problems.append(f"event prefix differs from 72a: {a['address']} | 72a '{a['event'][:40]}' | file 14 '{r['event'][:40]}'")
    if "OUT (crime) applied" in r["event"]: problems.append(f"already marked: {a['address']}"); continue
    suffix = f"OUT (crime) applied {TODAY}: {a['reason']} (memo 69 section 4.4)"
    new_event = (r["event"] + " | " + suffix) if r["event"] else suffix
    changed.append({"i": r["i"], "address": r["address"], "status": r["status"], "price": r["price"], "score": r["score"], "novice": r["novice"][:40], "crime": r["crime"], "reason_72a": a["reason"], "event_before": r["event"], "event_after": new_event, "url": r["url"]})
    r["event"] = new_event

print(f"72a rows: {len(ka)}; matched and marked: {len(changed)}; skipped (not ACTIVE): {len(skipped)}; problems: {len(problems)}")
for p in problems: print("  PROBLEM:", p)
for s in skipped: print("  SKIPPED:", s)
for c in changed: print(f"  {c['i']:>5} | {c['address'][:50]:50} | score {c['score']:>6} | {c['event_after']}")
if problems: sys.exit("stopping: see PROBLEM lines above")

order_before = [r["address"] for r in rows]
rows.sort(key=k14)   # stable: ties keep their current order
order_after = [r["address"] for r in rows]
print(f"rows: {len(rows)} (was {n_rows_before}); active: {sum(1 for r in rows if r['status'].startswith('ACTIVE'))} (was {n_active_before}); sort moved {sum(1 for a, b in zip(order_before, order_after) if a != b)} rows")

# every other cell unchanged: compare against the file as read
orig = {r["address"]: r for r in csv.DictReader(io.StringIO(text))}
diff_cells = [(r["address"], f) for r in rows for f in fields if f != "event" and r[f] != orig[r["address"]][f]]
assert not diff_cells, diff_cells[:5]
print("no cell other than event differs; event differs on", sum(1 for r in rows if r["event"] != orig[r["address"]]["event"]), "rows")

if DRY: print("[dry run: nothing written]"); sys.exit(0)
shutil.copyfile(F14, BACKUP); print("backup:", BACKUP)
buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\r\n"); w.writeheader(); w.writerows(rows)
open(F14, "wb").write(b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8"))
with open(F72B, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(changed[0].keys()), lineterminator="\r\n"); w.writeheader(); w.writerows(changed)
# read-back check
back = open(F14, "rb").read(); rb = list(csv.DictReader(io.StringIO(back.decode("utf-8-sig"))))
assert back[:3] == b"\xef\xbb\xbf" and back.count(b"\r\n") == len(rb) + 1 and len(rb) == n_rows_before, (back[:3], back.count(b"\r\n"), len(rb))
print(f"written: file 14 ({len(rb)} rows, BOM and CRLF intact); 72b: {F72B}")
