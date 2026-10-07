# sort_board_1004.py - memo 72 section 1 as decided 2026-10-04 (evening): re-sort file 14 with the sweep's key after weekly_sweep.py k14 gained
#   the event term (a row whose event carries "OUT (crime)" sorts below every live active row and above the non-active rows). No cell changes.
#   Check: every live active row precedes every knocked-out active row, every active row precedes every non-active row, the three non-active rows
#   that carry the OUT (crime) word go last, and the order inside each of the four blocks is the order the file had. Backup _backup_14_before_1004sort.csv. --dry prints and changes nothing. Desktop session.
import csv, io, sys, shutil
CAMP = "C:/Users/najum/Dropbox/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign/"
F14 = CAMP + "14 Live status and ranking of the 42 tracked candidates (2026-09-11).csv"; BACKUP = CAMP + "_pipeline/_backup_14_before_1004sort.csv"
DRY = "--dry" in sys.argv
def num(x):
    try: return float(str(x).replace(",", "").replace("$", ""))
    except Exception: return None
def k14(r):   # weekly_sweep.py, 2026-10-04 evening
    active = r["status"].startswith("ACTIVE"); s = num(r["score"]); return (0 if active else 1, 1 if "OUT (crime)" in (r.get("event") or "") else 0, 0 if (r.get("crime") or "").startswith("R ") else 1, -(s if s is not None else -999))
raw = open(F14, "rb").read(); assert raw[:3] == b"\xef\xbb\xbf" and raw.count(b"\r\n") == 230
rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))); fields = list(rows[0].keys()); assert len(rows) == 229
blk = lambda r: (0 if r["status"].startswith("ACTIVE") else 2) + (1 if "OUT (crime)" in r["event"] else 0)   # 0 live active, 1 knocked-out active, 2 non-active, 3 non-active with the OUT (crime) word (the three rows 72a did not list)
before = [r["address"] for r in rows]; srt = sorted(rows, key=k14); after = [r["address"] for r in srt]
for b in (0, 1, 2, 3): assert [a for a, r in zip(before, rows) if blk(r) == b] == [a for a, r in zip(after, srt) if blk(r) == b], f"order inside block {b} changed"
seq = [blk(r) for r in srt]; assert seq == sorted(seq), "blocks interleaved"
n = [seq.count(b) for b in (0, 1, 2, 3)]; moved = sum(1 for a, b_ in zip(before, after) if a != b_)
print(f"live active {n[0]}, knocked out {n[1]}, non-active {n[2]} plus {n[3]} non-active with the OUT (crime) word; {moved} rows change position; first knocked-out row now at position {seq.index(1) + 1}, last live active row is {srt[seq.index(1) - 1]['address']} ({srt[seq.index(1) - 1]['score']})")
if DRY: print("[dry run: nothing written]"); sys.exit(0)
shutil.copyfile(F14, BACKUP)
buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\r\n"); w.writeheader(); w.writerows(srt)
open(F14, "wb").write(b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8"))
back = open(F14, "rb").read(); rb = list(csv.DictReader(io.StringIO(back.decode("utf-8-sig"))))
assert back[:3] == b"\xef\xbb\xbf" and back.count(b"\r\n") == 230 and len(rb) == 229 and all(a[f] == b_[f] for a, b_ in zip(srt, rb) for f in fields)
print("written: file 14 re-sorted, every cell as before; backup", BACKUP)
