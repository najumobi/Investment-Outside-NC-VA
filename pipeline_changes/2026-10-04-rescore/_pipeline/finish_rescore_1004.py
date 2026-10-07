# finish_rescore_1004.py - memo 72 phase A3, second half (desktop session, 2026-10-04). After weekly_sweep.py underwrite --rescore ran on the
#   2026-09-28 ohio, 2026-09-28 pitt, 2026-09-29 phila and 2026-09-30 pitt folders (file 14 backup _backup_14_before_1004rescore.csv, taken
#   before the first of the four): (1) 556 Bellwood Rd, Newport News, a round-era Robbery-F row with no run folder, gets
#   'vacancy 8% at Robbery F not applied (round-era row)' appended to its why and keeps its score; (2) the board is sorted with the sweep's
#   key (weekly_sweep.py k14) and written back with the BOM and CRLF endings; (3) every cell the re-score and this step changed is listed
#   against the backup and written to rescore_1004_ledger.csv beside this script. --dry prints and changes nothing.
import csv, io, sys, re
CAMP = "C:/Users/najum/Dropbox/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign/"
PIPE = CAMP + "_pipeline/"
F14 = CAMP + "14 Live status and ranking of the 42 tracked candidates (2026-09-11).csv"
BACKUP = PIPE + "_backup_14_before_1004rescore.csv"; LEDGER = PIPE + "rescore_1004_ledger.csv"
DRY = "--dry" in sys.argv
BELLWOOD = "556 Bellwood Rd Unit A, Newport News, VA 23601"; NOTE = "vacancy 8% at Robbery F not applied (round-era row)"

def num(x):
    try: return float(str(x).replace(",", "").replace("$", ""))
    except Exception: return None
def k14(r):
    active = r["status"].startswith("ACTIVE"); s = num(r["score"])
    return (0 if active else 1, 0 if (r.get("crime") or "").startswith("R ") else 1, -(s if s is not None else -999))
def load(fn):
    raw = open(fn, "rb").read(); return raw, list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))

raw, rows = load(F14); braw, brows = load(BACKUP)
has_bom = raw[:3] == b"\xef\xbb\xbf"; n_crlf = raw.count(b"\r\n"); n_lf = raw.count(b"\n") - n_crlf
print(f"file 14 as the re-score left it: BOM {has_bom}, CRLF {n_crlf}, bare LF {n_lf}, rows {len(rows)}")
fields = list(rows[0].keys()); assert fields == list(brows[0].keys()) and fields[0] == "i", fields[:3]
assert len(rows) == len(brows) == 229, (len(rows), len(brows))
before = {r["address"]: r for r in brows}; assert len(before) == 229

bw = next(r for r in rows if r["address"] == BELLWOOD)
assert bw["crime"].startswith("R .93 F") and bw["status"].startswith("ACTIVE"), (bw["crime"], bw["status"])
if NOTE not in bw["why"]: bw["why"] = (bw["why"] + "; " if bw["why"] else "") + NOTE
print("Bellwood why ->", bw["why"])

order_before = [r["address"] for r in rows]; rows.sort(key=k14); moved = sum(1 for a, b in zip(order_before, [r["address"] for r in rows]) if a != b)
print(f"sort moved {moved} rows (the re-score wrote the file already sorted with the same key; a move here would be the Bellwood edit only, and it changes no score)")

ledger = []
for r in rows:
    b = before[r["address"]]
    ch = [f for f in fields if r[f] != b[f]]
    if ch: ledger.append({"i": r["i"], "address": r["address"], "status": r["status"], "changed": ", ".join(ch), "score_before": b["score"], "score_after": r["score"], "coc_before": b["coc_6.75"], "coc_after": r["coc_6.75"], "dscr_before": b["dscr"], "dscr_after": r["dscr"], "event_before": b["event"], "event_after": r["event"], "why_before": b["why"], "why_after": r["why"], "crime_before": b["crime"], "crime_after": r["crime"]})
print(f"{len(ledger)} rows differ from the backup; fields touched: {sorted({f for l in ledger for f in l['changed'].split(', ')})}")
for l in ledger: print(f"  {l['i']:>5} | {l['address'][:44]:44} | {l['changed']:38} | score {l['score_before']:>6} -> {l['score_after']:>6} | {l['event_after'][:70]}")
untouched = [f for f in ("price", "status", "novice", "note", "url", "drive_wb", "drive_ec", "flood", "historic", "address", "i") if any(f in l["changed"].split(", ") for l in ledger)]
assert not untouched, "a field the re-score must not touch changed: " + str(untouched)
if DRY: print("[dry run: nothing written]"); sys.exit(0)
buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\r\n"); w.writeheader(); w.writerows(rows)
open(F14, "wb").write(b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8"))
with open(LEDGER, "w", newline="", encoding="utf-8-sig") as f:
    lw = csv.DictWriter(f, fieldnames=list(ledger[0].keys()), lineterminator="\r\n"); lw.writeheader(); lw.writerows(ledger)
back, rb = load(F14)
assert back[:3] == b"\xef\xbb\xbf" and back.count(b"\r\n") == len(rb) + 1 == 230, (back[:3], back.count(b"\r\n"), len(rb))
print(f"written: file 14 ({len(rb)} rows, BOM and CRLF intact); ledger: {LEDGER}")
