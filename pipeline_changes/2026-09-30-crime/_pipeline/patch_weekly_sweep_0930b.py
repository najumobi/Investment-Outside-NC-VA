#!/usr/bin/env python3
"""Second patch of weekly_sweep.py (2026-09-30, after patch_weekly_sweep_0930.py): the crime knockout as memo 69 section 4.4 wrote it.

The first patch applied one stand-in rule everywhere (Robbery F with Burglary or Vandalism F). Memo 69 splits it by region:
  regional sweeps (phila, pitt, ohio): OUT when Robbery is F and the block group across the street is also F;
  NC/VA: OUT when Robbery is F and Burglary or Vandalism is F.
"Across the street" is any other 2020 block group whose boundary lies within 15 m of the geocoded address point (the same 15 m the
address reader uses), found with one TIGERweb query per address and cached in model/crime_across_cache.json. A street that cannot be
checked, or a block group across it with no map, does not knock a row out. The geocode cache (model/geo_cache_bg.json) now keeps the
address point beside the block group; a one-line geocode strips unit suffixes and address ranges first, and a failed call is not cached.

Usage: patch_weekly_sweep_0930b.py <weekly_sweep.py in (already patched once)> <weekly_sweep.py out>
"""
import sys

OLD_BG = '''BGC_FN = MODEL + "geo_cache_bg.json"; _BG = {}
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
'''

NEW_BG = '''import math
BGC_FN = MODEL + "geo_cache_bg.json"; _BG = {}
def _geo(address):
    """{"bg", "lat", "lon"} of an address: the batch geocoder's result from ingest (geo_cache_bg.json), else one call to the one-line geocoder, cached.
    A value cached as a bare block group (the first patch) is upgraded; a failed call is not cached, so the next run tries again."""
    if not _BG and os.path.exists(BGC_FN): _BG.update(jl(BGC_FN))
    v = _BG.get(address)
    if isinstance(v, dict) and (v.get("lat") is not None or not v.get("bg")): return v
    a = re.sub(r"\\s+(Unit|Apt|#|Lot)\\b[^,]*", "", address, flags=re.I); a = re.sub(r"^(\\d+)\\s*[-&/]\\s*\\d+\\S*\\s", r"\\1 ", a.strip())
    try:
        q = urllib.parse.urlencode({"address": a, "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"})
        with urllib.request.urlopen(urllib.request.Request("https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress?" + q, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as resp: d = json.load(resp)
        m = d["result"]["addressMatches"]
        v = {"bg": m[0]["geographies"]["2020 Census Blocks"][0]["GEOID"][:12], "lat": m[0]["coordinates"]["y"], "lon": m[0]["coordinates"]["x"]} if m else ({"bg": v} if isinstance(v, str) and v else {"bg": ""})
    except Exception:
        return {"bg": v} if isinstance(v, str) else (v or {"bg": ""})
    _BG[address] = v; js(BGC_FN, _BG); return v
def block_group_for(address): return _geo(address).get("bg", "")
AX_FN = MODEL + "crime_across_cache.json"; _AX = {}
def across_street(address, radius_m=15):
    """[[GEOID, metres], ...] of the other 2020 block groups whose boundary lies within radius_m of the address point (the block group across
    the street), from one TIGERweb query, cached; [] when no boundary is that close; None when it cannot be checked."""
    if not _AX and os.path.exists(AX_FN): _AX.update(jl(AX_FN))
    if address in _AX: return _AX[address]
    g = _geo(address)
    if g.get("lat") is None or not g.get("bg"): return None
    lat, lon = g["lat"], g["lon"]; kx = 111320 * math.cos(math.radians(lat)); ky = 110540; e = 0.0015
    try:
        q = urllib.parse.urlencode({"geometry": f"{lon - e},{lat - e},{lon + e},{lat + e}", "geometryType": "esriGeometryEnvelope", "inSR": "4326", "spatialRel": "esriSpatialRelIntersects", "outFields": "GEOID", "returnGeometry": "true", "outSR": "4326", "f": "geojson"})
        with urllib.request.urlopen(urllib.request.Request("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/11/query?" + q, headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as resp: fc = json.load(resp)
    except Exception: return None
    if "features" not in fc: return None
    def seg(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay; t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy))) if (dx or dy) else 0.0
        return math.hypot(px - ax - t * dx, py - ay - t * dy)
    out = []
    for ft in fc["features"]:
        gid = (ft.get("properties") or {}).get("GEOID"); geom = ft.get("geometry") or {}
        if not gid or gid == g["bg"] or not geom: continue
        polys = [geom["coordinates"]] if geom.get("type") == "Polygon" else geom.get("coordinates", [])
        best = min((seg(0.0, 0.0, (x1 - lon) * kx, (y1 - lat) * ky, (x2 - lon) * kx, (y2 - lat) * ky)
                    for poly in polys for ring in poly for (x1, y1), (x2, y2) in zip(ring, ring[1:])), default=1e9)
        if best <= radius_m: out.append([gid, round(best)])
    _AX[address] = out; js(AX_FN, _AX); return out
'''

OLD_KO = '''def crime_knockout(cr): return bool(cr) and cr["R"] >= 12 / 13 and (cr.get("B", 0) >= 12 / 13 or cr.get("V", 0) >= 12 / 13)   # memo 69 section 4.4: Robbery F with Burglary or Vandalism F (the second tab stands in for the across-the-street check)
'''
NEW_KO = '''def crime_knockout(cr, address):
    """memo 69 section 4.4. Regional sweeps: Robbery F and the block group across the street also F. NC/VA: Robbery F and Burglary or Vandalism F.
    A street that cannot be checked, or a block group across it with no map, does not knock the row out."""
    if not cr or cr["R"] < 12 / 13: return False
    if REGION == "ncva": return cr.get("B", 0) >= 12 / 13 or cr.get("V", 0) >= 12 / 13
    ax = across_street(address)
    if ax is None: return False
    return all((crime_table().get(gid) or {}).get("R", 0) >= 12 / 13 for gid, _ in ax)
def crime_ko_text(cr):
    if REGION == "ncva": return f"crime: Robbery {cgrade(cr['R'])} with Burglary {cgrade(cr.get('B', 0))}, Vandalism {cgrade(cr.get('V', 0))}"
    return f"crime: Robbery {cgrade(cr['R'])} on this block and across the street"
'''

def patch_b(s):
    for old, new in [
        (OLD_BG, NEW_BG),
        (OLD_KO, NEW_KO),
        ('#   ingest knocks out Robbery F + Burglary or Vandalism F and sorts Robbery-F rows behind the rest of the detail queue; underwrite scores the Robbery\n',
         '#   ingest knocks out a row by memo 69 section 4.4 (regional: Robbery F on the block and across the street; NC/VA: Robbery F with Burglary or Vandalism F)\n'
         '#   and sorts Robbery-F rows behind the rest of the detail queue; underwrite scores the Robbery\n'),
        ('                    if len(rec) >= 12 and rec[11]: bgc[raw[int(rec[0])]["address"]] = rec[8] + rec[9] + rec[10] + rec[11][:1]\n',
         '                    if len(rec) >= 12 and rec[11]:\n'
         '                        try: lon_, lat_ = (float(x) for x in rec[5].split(","))\n'
         '                        except Exception: lon_ = lat_ = None\n'
         '                        bgc[raw[int(rec[0])]["address"]] = {"bg": rec[8] + rec[9] + rec[10] + rec[11][:1], "lat": lat_, "lon": lon_}\n'),
        ('        if cr and crime_knockout(cr): ko.append(f"crime: Robbery {cgrade(cr[\'R\'])}, Burglary {cgrade(cr.get(\'B\', 0))}, Vandalism {cgrade(cr.get(\'V\', 0))}")\n',
         '        if cr and crime_knockout(cr, r["address"]): ko.append(crime_ko_text(cr))\n'),
        ('        elif crime_knockout(cr): verdict = "OUT (crime)"   # 2026-09-30\n',
         '        elif crime_knockout(cr, f["address"]): verdict = "OUT (crime)"   # 2026-09-30 (memo 69 section 4.4)\n'),
    ]:
        assert old in s, "anchor missing: " + old[:90]
        s = s.replace(old, new, 1)
    return s

if __name__ == "__main__":
    src = open(sys.argv[1], encoding="utf-8").read(); out = patch_b(src)
    open(sys.argv[2], "w", encoding="utf-8", newline="").write(out)
    import py_compile; py_compile.compile(sys.argv[2], doraise=True); print("patched and compiled:", sys.argv[2], len(src), "->", len(out))
