# restate_novice_0929.py - one-shot restatement of the "novice" column of file 14 in the grammar of memo 66 (2026-09-29).
# Run from anywhere: python "<PIPE>/restate_novice_0929.py" [--dry] [--f14=<path>] [--out=<path>] [--map=<path>]
# Safe to re-run: it backs up first, refuses to run if the file does not round-trip byte for byte, and skips rows already restated.
#
# The grammar (memo 66, section 5):
#   GRADE: <C-rating and what it was read from>; <why this grade, one clause>; <what is unseen or must be confirmed>[; flood factor N, itself a YELLOW driver] (<date of the read>)
#   GRADE is one of GREEN, GREEN-verify, YELLOW, RED, RED pending, not graded. The flood clause appears only when the factor is 5 or more
#   (the file 08 threshold); the flood column carries the number for every row. The date is the date of the read the cell rests on.
#
# Rows the 9/28 regional sweep folded are restated mechanically from their own note (the judgment's "cond" line) with novice_cell(),
# the same function weekly_sweep.py now uses when it folds a row. Every other row is restated by hand from the read the campaign's
# verified layer holds for it (the decision boards 32a to 49a and memos 31 to 49), listed in HAND below.
import csv, io, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parsers import key
CAMP = "C:/Users/najum/Dropbox/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign/"
PIPE = CAMP + "_pipeline/"
F14 = CAMP + "14 Live status and ranking of the 42 tracked candidates (2026-09-11).csv"
MAP = CAMP + "66a Novice designations, 136 rows before and after (2026-09-29).csv"
DRY = "--dry" in sys.argv; TAG = "0929"
for a in sys.argv[1:]:
    if a.startswith("--f14="): F14 = a[6:]
    if a.startswith("--out="): MAP = a[6:]
OUT14 = next((a[8:] for a in sys.argv[1:] if a.startswith("--out14=")), F14)
BACKUP = next((a[9:] for a in sys.argv[1:] if a.startswith("--backup=")), PIPE + f"_backup_14_before_{TAG}.csv")

GRADES = ("GREEN-verify", "GREEN", "YELLOW", "RED")

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

def mmdd_of(event):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", event or "")
    return f"{int(m.group(2))}/{int(m.group(3))}" if m else "?"

# Hand restatements, keyed by the street part of the address (parsers.key). Each rests on the read named in its date tag.
HAND = {
 "118 & 120 S Poplar St": "RED: tarped chimney, stair-step foundation crack and porch rot, each a file 08 RED item; C3 finishes, built 1938 (19 MLS frames, 9/15; advisory 33)",
 "1114 Lafayette Blvd NW": "YELLOW: C4 in 20 MLS frames; no cooling, electric baseboard upstairs, two rear openings boarded, lead paint presumed; the 9/9 GREEN-verify rested on the remarks' renovation claim, not on the frames (9/15)",
 "223 Spruce St": "not graded: no photo or record read yet; for sale by owner with 27 Zillow photos, built 1955; unit count and condition unverified (remarks only, 9/11)",
 "3704 Mariner Ave": "not graded: no photo read on the board yet; built 1940, renovated side-by-side duplex per the listing, so GREEN-verify once the scope is documented; advisory 60a of 9/25 proposed a read that is not yet assimilated (remarks only, 9/11)",
 "515-517 N Daughtry St": "YELLOW: C4 exterior in every frame from 2008 to 2026; no interiors, no HVAC permit ever, roof age unknown (at least 12 years), 1940 crawl space, original wood dormer siding, lead paint presumed (2 frames plus 4 dated Street View captures, 9/25)",
 "556 Bellwood Rd Unit A": "YELLOW: C4 on the front photo, built 1938, no renovation language (9/9)",
 "202 Lee St NE": "YELLOW: C4 in 11 MLS frames; Unit A repainted and refloored but its kitchen incomplete (one sink base, no uppers, range, fridge or hood), water heater in the hall; no cooling, electric floor and wall furnaces per the county card; Unit B unseen (9/16)",
 "163 Choate St": "YELLOW: C4 in 27 MLS frames; both units vacant, MLS 'Fixer upper', unit B carpet worn, two heat-pump condensers, new rear steps; no RED item; flood factor 5, itself a YELLOW driver (9/16)",
 "1934 Oakland St": "GREEN-verify: C3 with a documented renovation, built 1946; the 43 MLS frames are the 2023 lease-up set and the building has been vacant since; renovation scope to confirm (9/15)",
 "4102 Richland Ave NW": "YELLOW: C3 on the front photo, built 1973, no renovation language, so pre-1980 systems unknown (9/9)",
 "104 Day Street St": "YELLOW: C4 on the front photo, built 1754 per the record; the only photo is a third-party Street View, so condition is a verification demand (9/15)",
 "207 Tunstall Ave": "YELLOW: C4 in 14 MLS frames; open porch ceiling, tree over the roof, fiberboard ceiling tiles to test for asbestos, lead paint presumed; basement and drive-under garage unseen (9/16)",
 "515 Albemarle Ave SE": "YELLOW: C3 to C4 on the one listing photo, built before 1980; no renovation detail beyond charm language (round 4, 9/11)",
 "325 Ranch Farm Rd Unit A - B": "RED pending: the second unit is a 480 sf addition with no permit of record, a file 08 RED item (county card single-family, Wake layer verified); C3 to C4 finishes (36 MLS frames, 9/19)",
 "413-415 Gilmer Cir": "YELLOW: C4 in 11 MLS frames of the 413 side; 415 unseen; HVAC stripped since 2016; flood factor 7, itself a YELLOW driver (9/25)",
 "610 /612 S 2nd St": "YELLOW: C3 interiors on both sides, C4 exterior (porch beam on 2x4 posts, broken slab edge, bare fascia, 3-tab roof of unknown age, crushed foundation louver); kitchens in frames 4 and 8 unfinished, crawl space unseen (9 MLS frames, 9/25)",
 "407 Industrial Ave": "YELLOW: C4 on the front photo, built 1940, no renovation language (9/9)",
 "208 Scarborough St Unit A AND B": "YELLOW: C3 interiors of the 2026 unit, C3 to C4 exterior; occupied unit unseen since its 2023 ad; crawl space, chimneys, low-slope rear roof, water heater without a pan and 2012-vintage condensers to inspect (8 current frames plus the 2021 gallery, 9/25)",
 "215 Saint Andrew St": "YELLOW: C4 on the front photo, built 1914, no renovation language; flood factor 5, itself a YELLOW driver (9/9)",
 "639 Conover Rd": "GREEN: C1, built 2025; moot after the Gate 3 FAIL (89 frames spot-checked, 9/26)",
 "126 & 128 Troy Ave NE": "YELLOW: C4 in 20 MLS frames; two detached cottages of about 1973, no ranges or refrigerators, painted subfloors, no cooling, electric hydronic boiler without a flue, tree limb over the roof (9/16)",
 "7 Barney Pl": "RED: vacant unit stripped to the subfloor with sections open to the joists (wet-wall footprint), a file 08 RED item; flood factor 5 (14 MLS frames, 9/14; file 31)",
 "133 Hugh Caldwell Rd": "YELLOW: C3 exterior on the one usable MLS frame (the second evidence frame shows 201 Hugh Caldwell, the wrong building), built 1945; upfit permits finaled 1/2024 are the only renovation evidence, interiors unseen; the round-10 GREEN-verify rested on the front photo (9/16)",
 "2326 Elm Ave": "YELLOW: C3 on the front photo, built 1924, no renovation language, so pre-1960 systems unknown; flood factor 7, itself a YELLOW driver (9/9)",
 "2102 Rogers Dr": "YELLOW: C4 exterior (three-tab roof streaked in 2022 and debris-laden in 2026, no gutters, original wood sash with failed paint); the 33 frames mix the 2022 sale set of Unit B with 2026 phone photos of both occupied units; the 9/9 'GREEN pending proof of renovation' is withdrawn (9/23)",
 "814 Varsity Dr Unit A-B": "GREEN-verify: Unit A interior C3 (fresh cosmetic turn over 1983 all-electric systems), exterior C3; Unit B unseen (15 MLS frames, 9/23)",
 "749 Mt Airy St": "YELLOW: C4 on the 9/9 front photo and C3 on the 9/21 Zillow photo, built 1974; the listing's renovation language unverified (front photos only, 9/9 and 9/21)",
 "605 Washington St": "YELLOW: C4 exterior in 2 MLS frames (painted-block side-by-side, two window AC units, bare yard, chain-link); one occupied bathroom interior; no kitchen, heat or roof frames (9/19)",
 "301 S High St": "YELLOW: C4 on the front photo, built 1900; public record says single-family (9/9)",
 "28-30 Hillcrest Ave NE": "YELLOW: C4 on the front photo, built 1967, no renovation language (9/9)",
 "108 S Pine St": "YELLOW: C3 on the front photo, built 1950, no renovation language; 4 MLS frames with no kitchens, baths or mechanicals; flood factor 6, itself a YELLOW driver (9/15)",
 "1121 35th St": "YELLOW: C3, built 1930; kitchen and bath updates per the listing but systems unknown; the one frame is a Google Street View of May 2026 (9/15)",
 "334 Rhew St": "YELLOW: C4 on the front photo, built 1959, no renovation language; the only MLS photo is a 2020 Street View, so condition is a verification demand (9/15)",
 "1021 Penmar Ave SE": "GREEN-verify: vinyl siding, replacement windows, two condensers and laundry in both units in 26 MLS frames; renovation dates to confirm; reclassified from YELLOW on 9/15 (9/15)",
 "417 Squirrel St": "YELLOW: C3 to C4 renovated units and C5-leaning unfinished units in 45 shared MLS frames; surface-run romex evidenced in one unit, capped stub-outs and no range in frame 45, broken slabs and a block-wall fragment at the 417 line; mini-split heads plus baseboard heat (9/19)",
 "421 Squirrel St": "YELLOW: C3 to C4 renovated units and C5-leaning unfinished units in 45 shared MLS frames; surface-run romex evidenced in one unit, capped stub-outs and no range in frame 45, broken slabs and a block-wall fragment at the 417 line; mini-split heads plus baseboard heat (9/19)",
 "425 Squirrel St": "YELLOW: C3 to C4 renovated units and C5-leaning unfinished units in 45 shared MLS frames; surface-run romex evidenced in one unit, capped stub-outs and no range in frame 45, broken slabs and a block-wall fragment at the 417 line; mini-split heads plus baseboard heat (9/19)",
 "429 Squirrel St": "YELLOW: the same 45 shared MLS frames as 417 to 425, but the county card rates its condition FAIR 66 percent, the only non-A of the four, so it leans worse (9/19)",
 "1702 Birchwood Dr SE": "YELLOW: C4 exterior on a single MLS frame; roofs streaked and mossy (original 1990-92 roofs assumed); no interiors (9/16)",
 "1706 Birchwood Dr SE": "YELLOW: C4 exterior on a single MLS frame; roofs streaked and mossy (original 1990-92 roofs assumed); no interiors (9/16)",
 "1707 Birchwood Dr SE": "YELLOW: C4 exterior on a single MLS frame; roofs streaked and mossy (original 1990-92 roofs assumed); no interiors (9/16)",
 "1703 Birchwood Dr SE": "YELLOW: C4 exterior on a single MLS frame; roofs streaked and mossy (original 1990-92 roofs assumed); no interiors (9/16)",
 "1708 Birchwood Dr SE": "YELLOW: C4 exterior on a single winter-2025 MLS frame; its brown roof reads newer than its four siblings; no interiors; flood factor 6, itself a YELLOW driver (9/16)",
 "741-745 Tamarack Dr": "YELLOW: no current photo; all 5 evidence frames are the October 2017 MLS set and the 2026 listing's only image is a map-app street-level screenshot; no interior ever shown; roof and HVAC claims are 2017 recollections (9/24)",
 "716 31st St": "YELLOW: C3 on the listing's interior-only photos, built 1940; updated windows, HVAC and LVP per the listing, unverified; exterior unseen; flood factor 6, itself a YELLOW driver (9/11)",
 "307 S Jacob St": "YELLOW: C3 exterior; the 9/25 re-read of 15 MLS frames shows an unvented wall heater on a flex line (fuel source unverified), a capped floor stub with a receptacle and an electric water heater beside the toilet (9/25)",
 "2316 Edgar St": "YELLOW: C4 exterior in 4 frames (two-gang meter stack, hardboard lap siding with face nails and mildew banding, no gutters under an oak canopy, lifted shingle tab, algae streak below the line-set penetration); no interior evidenced; no RED item (9/20)",
 "307 N Church St": "YELLOW: C3 to C4 upper unit in the 2026 rental frames (new finishes over 1952 supply); lower unit unseen since the 2013 gutted-kitchen frames; crawl space by the creek and the propane-to-gas history to verify (22 frames, 9/26)",
 "2614 Pecan Dr": "YELLOW: C4 exterior, no RED item visible; walks under file 08 because the visible exterior list alone runs 2 to 4 times the 10 percent bid cap; RED candidates open (1946 wiring and panel, heat type, asbestos-shingle siding, permits) (2 MLS frames, 9/24)",
 "2311 Nickey Ave": "YELLOW: C4 in 20 MLS frames; cosmetic turn on a 1963 shell, algae-streaked siding, space heater in unit A (9/15)",
 "27 Carver Cir": "YELLOW: 23 exterior MLS frames, no interiors; 1942 brick; the second unit needs renovation per the listing, so written bids are required (9/15)",
 "132 Kemper Rd Unit A & B": "YELLOW: C4 interiors and a C5 bath in 16 MLS frames over two sessions; no RED item (9/15)",
 "503 Granville St": "YELLOW: C3 exterior, C3 to C4 lower unit, C4 upper unit needing a turn; inspection targets named (upper turn, stacked water signature, toilet on a raised platform, porch ceiling and beam); no mechanicals shown, lower heat unknown (30 MLS frames, 9/24)",
 "117 Motley Ave": "YELLOW: C4 on the round-5 front photo, built 1915; 18 MLS frames plus the assessor's 2023 photo show three households, a Gate 3 disqualifier (9/15)",
 "224 S Jefferson St": "YELLOW: C4 on the front photo, built 1900, renovation language unverified (9/9)",
 "739 S Rosemont Rd": "YELLOW: no photo read on the board yet; built 1999, sold as-is with month-to-month tenants of five-plus years; advisory 58b of 9/25 read six exterior frames at C3 with no interior, roof or mechanical evidence, not yet assimilated (remarks only, 9/11)",
 "306 & 308 Troy Ave NE": "GREEN: C2 on the front photo, built 1984, renovation language in the listing (9/9)",
 "125 The Blvd": "YELLOW: C2 to C3 finishes in 36 MLS frames, but a 1930 masonry storefront converted to two 2BR units; new TPO roof; small high bedroom windows raise an egress question; the 9/9 GREEN-verify is withdrawn (9/16)",
 "918 Star St": "GREEN-verify: C2 to C3 in 33 frames; the structure below the floor is the documented weak point (2007 joist permits at both units, 2012 floor patch, 2021 'dilapidated', boarded 2022 to 2024); two chimneys removed and roof re-covered in 2025 without a visible permit trail; no crawl or panel frame (9/25)",
 "306 Auburndale St": "YELLOW: lower unit C4 in 8 frames (kitchen, living room, two bedrooms, bath); upper unit unseen; basement post-and-brace beam, wall band, chimney stack and half-story egress to inspect; no RED item visible (9/25)",
 # 9/28 regional rows whose judgment line does not start with the grade, so the mechanical form would misread it
 "426 Washington Ave": "YELLOW: no usable photo (the Zillow page returned only navigation text on three fetches); unit count, condition and legal status unverified; graded YELLOW so the row reaches review, not as a condition read (9/28)",
 "840 Work Dr": "YELLOW: C3 on the one listing photo, graded only so the row reaches review; no remarks retrievable (the page returned navigation text), unit count unverified; CONTINGENT on Zillow (9/28)",
}
HANDK = {key(a): v for a, v in HAND.items()}
assert len(HANDK) == len(HAND), "two hand entries share a key"

def rd_raw(fn):
    raw = open(fn, "rb").read(); text = raw.decode("utf-8")           # the BOM stays inside the first field name, as weekly_sweep.py keeps it
    rows = list(csv.DictReader(io.StringIO(text, newline=""))); fields = list(rows[0].keys())
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\r\n"); w.writeheader(); w.writerows(rows)
    if buf.getvalue().encode("utf-8") != raw: sys.exit("HALT: file 14 does not round-trip byte for byte through the csv module; nothing written")
    return rows, fields

def wr(fn, rows, fields):
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\r\n"); w.writeheader(); w.writerows(rows)

rows, fields = rd_raw(F14); IF = fields[0]
keys = [key(r["address"]) for r in rows]
dups = {k for k in keys if keys.count(k) > 1}; assert not dups, f"file 14 rows share a key: {dups}"
if not DRY:
    if os.path.exists(BACKUP): print(f"backup exists: {os.path.basename(BACKUP)}")
    else: shutil.copy2(F14, BACKUP); print(f"backed up file 14 -> {os.path.basename(BACKUP)}")
mapping = []; n_hand = n_mech = n_skip = 0; used = set()
for r in rows:
    k = key(r["address"]); old = r["novice"]
    if re.match(r"^(GREEN-verify|GREEN|YELLOW|RED pending|RED|not graded): .*\(\d{1,2}/\d{1,2}[^)]*\)$", old) and k not in HANDK and " / photo " not in old:
        n_skip += 1; mapping.append((r[IF], r["address"], r["status"], old, old, "already restated")); continue
    if k in HANDK:
        new = HANDK[k]; basis = "hand, from the verified read named in the cell"; n_hand += 1; used.add(k)
    else:
        m = re.match(r"^(GREEN-verify|GREEN|YELLOW|RED)\s*/\s*photo\s*([^;]+?)\s*(?:;\s*flood factor\s*(\S+))?$", old)
        if not m: sys.exit(f"HALT: no rule for row {r[IF]} {r['address']}: {old!r}")
        grade, c = m.group(1), m.group(2).strip()
        new = novice_cell(grade, c, r["note"], r["flood"], mmdd_of(r["event"])); basis = "mechanical, from the judgment line in the note"; n_mech += 1
    src = "grade token changed" if re.match(r"^(GREEN-verify|GREEN|YELLOW|RED|not graded|unrated)", old).group(0).replace("unrated", "not graded") != re.match(r"^(GREEN-verify|GREEN|YELLOW|RED pending|RED|not graded)", new).group(0) else ""
    mapping.append((r[IF], r["address"], r["status"], old, new, basis + ("; " + src if src else "")))
    r["novice"] = new
unused = set(HANDK) - used
if unused: print("WARNING: hand entries that matched no row:", sorted(unused))
print(f"{len(rows)} rows: {n_hand} restated by hand, {n_mech} mechanically, {n_skip} already in the grammar; token changes: {sum(1 for m in mapping if 'token changed' in m[5])}")
for i, a, st, old, new, basis in mapping:
    if old != new: print(f"\n{i:6s} {a[:46]}\n   was: {old}\n   now: {new}" + (f"\n   ** {basis.split('; ')[1]}" if "; " in basis else ""))
lens = sorted(len(m[4]) for m in mapping); print(f"\ncell length: min {lens[0]}, median {lens[len(lens)//2]}, max {lens[-1]}")
if DRY: print("dry run: nothing written"); sys.exit()
wr(OUT14, rows, fields); print(f"wrote {os.path.basename(OUT14)} ({len(rows)} rows)")
with open(MAP, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, lineterminator="\r\n"); w.writerow(["i", "address", "status", "novice_before", "novice_after", "basis"]); w.writerows(mapping)
print(f"wrote {os.path.basename(MAP)}")
