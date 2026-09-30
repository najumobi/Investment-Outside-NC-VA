#!/usr/bin/env python3
"""Patch weekly_sweep.py (Dropbox copy of 2026-09-30) so the sweep reads block-level crime from model/crime_bg.json (memo 69).

Usage: patch_weekly_sweep_0930.py <weekly_sweep.py in> <weekly_sweep.py out>   (exits 1 if any anchor is missing)
Also exposes patch_prompt(text) for the five weekly_task_prompt_*.md files (step 8a).
"""
import sys, re

HELPERS = '''
# 2026-09-30 (memo 69, the block-level crime read): the crime input is the CrimeGrade legend position of the listing's 2020 census block group
#   on six crime tabs (Robbery, Assault, Burglary, Vandalism, Drug, Murder), read from model/crime_bg.json, which build_crime_bg.py fills from
#   hand screenshots of the ZIP pages; the ZIP-level Overall letter (constants crime_zip) is retired. Robbery carries the score penalty and the
#   vacancy rule; Robbery F together with Burglary or Vandalism F is a knockout; a block group no map covers reads "maps needed".
import urllib.parse
CB_FN = MODEL + "crime_bg.json"; _CB = {}
def crime_table():
    if not _CB and os.path.exists(CB_FN): _CB.update(jl(CB_FN).get("bg", {}))
    return _CB
BGC_FN = MODEL + "geo_cache_bg.json"; _BG = {}
def block_group_for(address):
    """12-digit 2020 block group of an address: the batch geocoder's block from ingest (geo_cache_bg.json), else one call to the one-line geocoder, cached."""
    if not _BG and os.path.exists(BGC_FN): _BG.update(jl(BGC_FN))
    if address in _BG: return _BG[address]
    try:
        q = urllib.parse.urlencode({"address": address, "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"})
        with urllib.request.urlopen(urllib.request.Request("https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress?" + q, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as resp: d = json.load(resp)
        m = d["result"]["addressMatches"]; bg = m[0]["geographies"]["2020 Census Blocks"][0]["GEOID"][:12] if m else ""
    except Exception: bg = ""
    _BG[address] = bg; js(BGC_FN, _BG); return bg
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
def crime_knockout(cr): return bool(cr) and cr["R"] >= 12 / 13 and (cr.get("B", 0) >= 12 / 13 or cr.get("V", 0) >= 12 / 13)   # memo 69 section 4.4: Robbery F with Burglary or Vandalism F (the second tab stands in for the across-the-street check)
MMDD = f"{int(DATE[5:7])}/{int(DATE[8:10])}"
'''

def patch(s):
    n0 = len(s)
    def rep(old, new, count=1):
        assert old in s_[0], "anchor missing: " + old[:80]
        s_[0] = s_[0].replace(old, new, count)
    s_ = [s]
    rep("#   of the event only (price, status, novice and note are kept, so a row whose verdict becomes OUT stays on the list for Najum's review; no new rows; the tally is untouched).\n",
        "#   of the event only (price, status, novice and note are kept, so a row whose verdict becomes OUT stays on the list for Najum's review; no new rows; the tally is untouched).\n"
        "# 2026-09-30 (memo 69): crime is read at block-group level from model/crime_bg.json (six CrimeGrade tabs, hand screenshots) instead of the ZIP letter;\n"
        "#   ingest knocks out Robbery F + Burglary or Vandalism F and sorts Robbery-F rows behind the rest of the detail queue; underwrite scores the Robbery\n"
        "#   position (crime_penalty), applies the 8% vacancy at Robbery F, writes the six readings into file 14's crime column and lists \"crime maps needed\".\n")
    rep('def akey(a):', HELPERS.lstrip("\n") + 'def akey(a):')
    # ingest: keep the block group beside the tract in the geocode cache
    rep('    cache_fn = MODEL + "geo_cache.json"; cache = jl(cache_fn) if os.path.exists(cache_fn) else {}\n',
        '    cache_fn = MODEL + "geo_cache.json"; cache = jl(cache_fn) if os.path.exists(cache_fn) else {}\n'
        '    bgc = jl(BGC_FN) if os.path.exists(BGC_FN) else {}   # 2026-09-30: block groups from the same batch geocode\n')
    rep('                if len(rec) >= 12 and rec[2] == "Match": cache[raw[int(rec[0])][\"address\"]] = rec[8] + rec[9] + rec[10]\n            js(cache_fn, cache)\n',
        '                if len(rec) >= 12 and rec[2] == "Match":\n'
        '                    cache[raw[int(rec[0])]["address"]] = rec[8] + rec[9] + rec[10]\n'
        '                    if len(rec) >= 12 and rec[11]: bgc[raw[int(rec[0])]["address"]] = rec[8] + rec[9] + rec[10] + rec[11][:1]\n'
        '            js(cache_fn, cache); js(BGC_FN, bgc); _BG.update(bgc)\n')
    rep('        if rec["rent_to_price_pct"] != "" and rec["rent_to_price_pct"] < 0.9: ko.append("rent-to-price under 0.9%")\n        rec["knockouts"] = "; ".join(ko)\n',
        '        if rec["rent_to_price_pct"] != "" and rec["rent_to_price_pct"] < 0.9: ko.append("rent-to-price under 0.9%")\n'
        '        # 2026-09-30: block-level crime for the rows that could reach the detail queue (the rest would cost a geocode each for nothing)\n'
        '        could = (rec["delta"] in ("new", "relisted") or rec["delta"].startswith("price cut") or idx.get(k, {}).get("detail_pending") == "yes") and not ko and p and p <= C["practical_ceiling"]\n'
        '        cr = crime_read(r["address"]) if could else None\n'
        '        rec["block_group"] = cr["bg"] if cr else ""; rec["crime_R"] = round(cr["R"], 3) if cr else ""; rec["crime_cell"] = crime_cell(cr, MMDD) if cr else (f"maps needed {k.split(chr(124))[1]}" if could else "")\n'
        '        if cr and crime_knockout(cr): ko.append(f"crime: Robbery {cgrade(cr[\'R\'])}, Burglary {cgrade(cr.get(\'B\', 0))}, Vandalism {cgrade(cr.get(\'V\', 0))}")\n'
        '        rec["knockouts"] = "; ".join(ko)\n')
    rep('    else: shortlist.sort(key=lambda s: (1 if r2p_of(s) >= BAND else 0, -r2p_of(s)))\n',
        '    else: shortlist.sort(key=lambda s: (1 if r2p_of(s) >= BAND else 0, 1 if (s.get("crime_R") != "" and s.get("crime_R") is not None and float(s["crime_R"]) >= 12 / 13) else 0, -r2p_of(s)))   # 2026-09-30: Robbery-F rows go behind the band (memo 69 section 4.3)\n')
    rep('    js(RUN + "detail_plan.json", [{"address": s["address"], "url": s["url"], "zurl": s.get("zurl", ""), "rent_to_price_pct": s["rent_to_price_pct"], "delta": s["delta"]} for s in shortlist])\n',
        '    js(RUN + "detail_plan.json", [{"address": s["address"], "url": s["url"], "zurl": s.get("zurl", ""), "rent_to_price_pct": s["rent_to_price_pct"], "delta": s["delta"], "crime": s.get("crime_cell", "")} for s in shortlist])\n'
        '    need_maps = sorted({s["crime_cell"].split(" ")[-1] for s in shortlist if str(s.get("crime_cell", "")).startswith("maps needed")})\n'
        '    if need_maps: note(f"## Crime maps needed ({len(need_maps)} ZIPs on the shortlist have no block-level read; six CrimeGrade tabs each, see memo 69): " + ", ".join(need_maps))\n')
    # underwrite
    rep('    def crime_for(city, z):\n        return C["crime"].get(city) or C["crime_zip"].get(z, "")\n    def crime_pen(g):\n        g = g.split(" ")[0] if g else ""; return {"F": 3, "D-": 2, "D": 1, "D+": 0.5}.get(g, 0)\n    ORDER = {"ENTRANT": 0, "NEAR-MISS": 1, "OUT (negative cash flow)": 2, "OUT (RED)": 3, "OUT": 4}\n',
        '    def crime_for(city, z):   # the retired ZIP letter, kept in results.csv as crime_zip for reference only (2026-09-30)\n        return C["crime"].get(city) or C["crime_zip"].get(z, "")\n    ORDER = {"ENTRANT": 0, "NEAR-MISS": 1, "OUT (negative cash flow)": 2, "OUT (crime)": 2.5, "OUT (RED)": 3, "OUT": 4}\n')
    rep('        crime = crime_for(city, z)\n        grade = j.get("grade", "YELLOW"); units = j.get("units", 2)\n',
        '        crime = crime_for(city, z); cr = crime_read(f["address"])   # 2026-09-30: the block-level read decides; the letter is reference only\n        grade = j.get("grade", "YELLOW"); units = j.get("units", 2)\n')
    rep('        if not crime: missing.append(f"{city} {st} {z}: CrimeGrade letter")\n',
        '        if not cr: missing.append(f"{z}: crime maps needed (the six CrimeGrade tabs of the ZIP page, screenshot by hand; memo 69)")\n')
    rep('            vac = 0.08 if (grade == "RED" or crime.startswith("F")) else 0.05\n',
        '            vac = 0.08 if (grade == "RED" or (cr and cr["R"] >= 12 / 13)) else 0.05   # 2026-09-30: Robbery F, not the ZIP letter\n')
    rep('        elif grade == "OUT" or not rent or units != 2: verdict = "OUT"\n',
        '        elif grade == "OUT" or not rent or units != 2: verdict = "OUT"\n        elif crime_knockout(cr): verdict = "OUT (crime)"   # 2026-09-30\n')
    rep('            cp = crime_pen(crime)\n            if cp: pen += cp; why.append(f"crime {crime.split(\' \')[0]} -{cp}")\n',
        '            cp = crime_penalty(cr); pen += cp   # 2026-09-30: on the Robbery position\n            why.append((f"crime R {cpos(cr[\'R\'])} {cgrade(cr[\'R\'])} -{cp}" if cp else f"crime R {cpos(cr[\'R\'])} {cgrade(cr[\'R\'])} 0") if cr else "crime unread (maps needed)")\n')
    rep('"jurisdiction_flag": jflag, "crime_zip": crime, ',
        '"jurisdiction_flag": jflag, "crime_cell": crime_cell(cr, MMDD) if cr else f"maps needed {z}", "block_group": cr["bg"] if cr else "", "crime_zip": crime, ')
    rep('"crime": (o["crime_zip"] or "").split(" ")[0], ', '"crime": o["crime_cell"], ')
    rep('        r["score"] = o["score"]; r["coc_6.75"] = o["coc_6.75_full_expense_pct"]; r["dscr"] = o["dscr_6.75"]; r["why"] = o["why"]\n',
        '        r["score"] = o["score"]; r["coc_6.75"] = o["coc_6.75_full_expense_pct"]; r["dscr"] = o["dscr_6.75"]; r["why"] = o["why"]; r["crime"] = o["crime_cell"]   # 2026-09-30: the crime cell follows the read\n')
    return s_[0]

def patch_prompt(t):
    old = '(a) CrimeGrade letter for a ZIP: in the workbench run u,c,h = fetch("https://crimegrade.org/safest-places-in-ZIP/", 1) and apply the regular expression "The ([A-F][+-]?) overall grade" to c;'
    new = ('(a) "crime maps needed <ZIP>": the block-level crime read (memo 69) has no map for that ZIP; do NOT fetch CrimeGrade pages from the workbench; list the ZIPs in the report for Najum, who screenshots the six tabs of https://crimegrade.org/safest-places-in-ZIP/ (Robbery, Assault, Burglary, Vandalism, Drug-Related Crime, Murder; map north-up at the page zoom, dropdown closed, whole page in frame) and hands them to the cloud session, which extends PIPE\\model\\crime_bg.json; rerun underwrite after that file changes;')
    assert old in t, "prompt anchor (a) missing"
    t = t.replace(old, new)
    old2 = 'Record additions in PIPE\\constants.json under crime_zip (key = ZIP, value like "C+ (CrimeGrade, auto DATE)") or drive_wb (key = city, value = hours)'
    if old2 in t: t = t.replace(old2, 'Record additions in PIPE\\constants.json under drive_wb (key = city, value = hours)')
    return t

if __name__ == "__main__":
    src = open(sys.argv[1], encoding="utf-8").read()
    out = patch(src)
    open(sys.argv[2], "w", encoding="utf-8", newline="").write(out)
    import py_compile; py_compile.compile(sys.argv[2], doraise=True); print("patched and compiled:", sys.argv[2], len(src), "->", len(out))
