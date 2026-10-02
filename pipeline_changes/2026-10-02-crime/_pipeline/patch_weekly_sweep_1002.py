#!/usr/bin/env python3
"""Third crime patch of weekly_sweep.py (2026-10-02, after patch_weekly_sweep_0930.py and _0930b.py): unread rows sort last.

Memo 69 section 4.3 says a listing whose block group no map covers yet "is folded below rows that have a reading". The first two patches
wrote the "maps needed" cell but sorted such a row by its score alone, and since an unread row carries no crime term its score is higher
than it would be with a reading (979 Lagonda Ave, Springfield, folded by the 10/1 Ohio run at 0.1, sat above read rows). This patch adds
crime_rank() and uses it in three places:
  ingest's detail queue: within each rent-to-price band group, read rows better than Robbery F first, then Robbery F, then unread;
  underwrite's verdict list: within each verdict, unread rows after the rows that have a reading;
  file 14 when the sweep writes it: within the active rows (and within the inactive ones), unread rows after the rows that have a reading.
A row is read on file 14 when its crime cell starts with "R " (the six-tab grammar); "maps needed <zip>", "zip X retired 9/30; block maps
needed" and "off the <zip> page map ..." are unread. Nothing about scores, verdicts or knockouts changes.

Usage: patch_weekly_sweep_1002.py <weekly_sweep.py in (already patched by 0930 and 0930b)> <weekly_sweep.py out>
"""
import sys

PATCHES = [
    ('#   position (crime_penalty), applies the 8% vacancy at Robbery F, writes the six readings into file 14\'s crime column and lists "crime maps needed".\n',
     '#   position (crime_penalty), applies the 8% vacancy at Robbery F, writes the six readings into file 14\'s crime column and lists "crime maps needed".\n'
     '# 2026-10-02 (memo 69 section 4.3; patch_weekly_sweep_1002.py): a row whose block group no map covers yet sorts below the rows that have a reading,\n'
     '#   in the detail queue (within its rent-to-price band group, after the Robbery-F rows), in the verdict list and on file 14; its score carries no crime term.\n'),
    ('def crime_ko_text(cr):\n',
     'def crime_rank(R):\n'
     '    """Place of a row\'s crime reading in the detail queue (memo 69 section 4.3): 0 read and Robbery better than F, 1 Robbery F, 2 no map yet."""\n'
     '    if R == "" or R is None: return 2\n'
     '    return 1 if float(R) >= 12 / 13 else 0\n'
     'def crime_ko_text(cr):\n'),
    ('    else: shortlist.sort(key=lambda s: (1 if r2p_of(s) >= BAND else 0, 1 if (s.get("crime_R") != "" and s.get("crime_R") is not None and float(s["crime_R"]) >= 12 / 13) else 0, -r2p_of(s)))   # 2026-09-30: Robbery-F rows go behind the band (memo 69 section 4.3)\n',
     '    else: shortlist.sort(key=lambda s: (1 if r2p_of(s) >= BAND else 0, crime_rank(s.get("crime_R")), -r2p_of(s)))   # 2026-09-30: Robbery-F rows go behind the rest of their band group; 2026-10-02: unread rows behind both (memo 69 section 4.3)\n'),
    ('    if need_maps: note(f"## Crime maps needed ({len(need_maps)} ZIPs on the shortlist have no block-level read; six CrimeGrade tabs each, see memo 69): " + ", ".join(need_maps))\n',
     '    if need_maps: note(f"## Crime maps needed ({len(need_maps)} ZIPs hold the {sum(1 for s in shortlist if str(s.get(\'crime_cell\', \'\')).startswith(\'maps needed\'))} shortlist rows with no block-level read, which wait behind the rows that have one; six CrimeGrade tabs each, see memo 69): " + ", ".join(need_maps))\n'),
    ('    out.sort(key=lambda o: (ORDER[o["verdict"]], -(o["score"] if o["score"] != "" else -999)))\n',
     '    out.sort(key=lambda o: (ORDER[o["verdict"]], 1 if o["block_group"] == "" else 0, -(o["score"] if o["score"] != "" else -999)))   # 2026-10-02: unread rows below the rows that have a reading (memo 69 section 4.3)\n'),
    ('        def k14(r):\n'
     '            active = r["status"].startswith("ACTIVE"); s = num(r["score"]); return (0 if active else 1, -(s if s is not None else -999))\n',
     '        def k14(r):   # 2026-10-02: a row with no block-level crime reading sorts below the rows that have one (memo 69 section 4.3)\n'
     '            active = r["status"].startswith("ACTIVE"); s = num(r["score"]); return (0 if active else 1, 0 if (r.get("crime") or "").startswith("R ") else 1, -(s if s is not None else -999))\n'),
]

def patch_c(s):
    for old, new in PATCHES:
        assert s.count(old) == 1, "anchor missing or repeated: " + old[:90]
        s = s.replace(old, new, 1)
    return s

if __name__ == "__main__":
    raw = open(sys.argv[1], "rb").read(); bom = raw.startswith(b"\xef\xbb\xbf"); crlf = b"\r\n" in raw
    src = raw.decode("utf-8-sig").replace("\r\n", "\n"); out = patch_c(src)
    if crlf: out = out.replace("\n", "\r\n")
    open(sys.argv[2], "wb").write((b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8"))
    import py_compile; py_compile.compile(sys.argv[2], doraise=True); print("patched and compiled:", sys.argv[2], len(src), "->", len(out))
