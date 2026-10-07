#!/usr/bin/env python3
"""Grade street addresses from CrimeGrade Overall Crime map images.

usage: python3 grade_addresses.py ADDRESSES.csv RESULTS.csv [--check-side] [--zmin 12.3] [--zmax 14.8] [--cache DIR]

ADDRESSES.csv columns: address (one line with city, state and ZIP), image (path of the map image, relative to the
CSV), and optionally id. Several addresses may share one image; the image is georeferenced once, from the first.

The script never downloads anything from CrimeGrade. Save each ZIP's map yourself: on the ZIP page
(crimegrade.org/safest-places-in-<ZIP>/) right-click the map and save the image, or take a screenshot of the map
with its legend. It uses three free public services: the Census geocoder (address -> coordinates and census block),
Census TIGERweb (street centrelines and block-group polygons) and, with --check-side only, OpenStreetMap Nominatim
(house points, at most one request a second, per its usage policy).

--check-side: when a block group with a different grade lies within 15 m (the house is on a street that divides two
block groups), look the house up in OpenStreetMap and read the block group that contains the house point instead.
"""
import argparse, csv, json, os, sys, time, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from georef import georeference, load_rgb
from colour_read import read_address, block_group_at, grade_equal_bands, grade_label_anchored

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "duplex-campaign-crimegrade/1.0"}
_last_osm = [0.0]


def _get(url, params):
    with urllib.request.urlopen(urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers=UA), timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def census_geocode(address, cache_dir):
    path = os.path.join(cache_dir, "geocode_" + "".join(c if c.isalnum() else "_" for c in address)[:120] + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    d = _get("https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress",
             {"address": address, "benchmark": "Public_AR_Current", "vintage": "Current_Current", "format": "json"})
    m = d["result"]["addressMatches"]
    out = None
    if m:
        m = m[0]
        out = {"matched": m["matchedAddress"], "lat": m["coordinates"]["y"], "lon": m["coordinates"]["x"],
               "block": m["geographies"]["2020 Census Blocks"][0]["GEOID"]}
    json.dump(out, open(path, "w"))
    return out


def osm_house_point(address):
    wait = 1.1 - (time.time() - _last_osm[0])
    if wait > 0:
        time.sleep(wait)
    _last_osm[0] = time.time()
    for x in _get("https://nominatim.openstreetmap.org/search", {"q": address, "format": "json", "limit": 3, "addressdetails": 1}):
        if x.get("address", {}).get("house_number"):
            return float(x["lat"]), float(x["lon"])
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("addresses"); ap.add_argument("results")
    ap.add_argument("--check-side", action="store_true")
    ap.add_argument("--zmin", type=float, default=12.3); ap.add_argument("--zmax", type=float, default=14.8)
    ap.add_argument("--cache", default=os.path.join(HERE, "cache"))
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    base = os.path.dirname(os.path.abspath(a.addresses))
    rows = list(csv.DictReader(open(a.addresses, newline="", encoding="utf-8-sig")))
    fits, images, out = {}, {}, []
    for i, r in enumerate(rows, 1):
        rid, address = r.get("id") or str(i), r["address"].strip()
        image = os.path.normpath(os.path.join(base, r["image"].strip()))
        rec = {"id": rid, "address": address, "image": r["image"].strip()}
        geo = census_geocode(address, a.cache)
        if not geo:
            rec["note"] = "the Census geocoder found no match"
            out.append(rec); print(f"{rid:>4} {address}: no geocode"); continue
        rec.update(matched_address=geo["matched"], lat=round(geo["lat"], 6), lon=round(geo["lon"], 6))
        if image not in fits:
            st = os.stat(image)
            key = os.path.join(a.cache, "fit_" + "".join(c if c.isalnum() else "_" for c in os.path.basename(image)) + f"_{st.st_size}_{int(st.st_mtime)}.json")
            if os.path.exists(key):
                fits[image] = json.load(open(key))
            else:
                print(f"georeferencing {r['image']} ...", flush=True)
                fits[image] = georeference(image, geo["lat"], geo["lon"], a.cache, a.zmin, a.zmax)
                json.dump(fits[image], open(key, "w"))
            images[image] = load_rgb(image)
        fit, A = fits[image], images[image]
        rec.update(zoom=fit["zoom"], fit_score=fit["score"])
        res = read_address(A, fit, geo["lat"], geo["lon"], geo["block"][:12], a.cache)
        if "error" in res:
            rec["note"] = res["error"]
            out.append(rec); print(f"{rid:>4} {address}: {res['error']}"); continue
        notes, side = [], ""
        across = [n for n in res["neighbours_within_60m"] if n["distance_m"] <= 15 and n["grade"] != res["grade"]]
        if across and a.check_side:
            hp = osm_house_point(address)
            if hp is None:
                side = "no OpenStreetMap house point"
            else:
                bg = block_group_at(*hp)
                if bg == res["block_group"]:
                    side = "OpenStreetMap house point confirms the side"
                elif bg:
                    alt = read_address(A, fit, hp[0], hp[1], bg, a.cache)
                    if "error" not in alt:
                        side = f"OpenStreetMap house point is in {bg}; that block group is read instead of {res['block_group']}"
                        res = alt
        across = [n for n in res["neighbours_within_60m"] if n["distance_m"] <= 15 and n["grade"] != res["grade"]]
        if across:
            notes.append("block group across the street is " + "/".join(sorted({n["grade"] for n in across})))
        if res["line_note"]:
            notes.append(res["line_note"])
        if res["label_anchored_grade"] != res["grade"]:
            notes.append(f"label-anchored reading gives {res['label_anchored_grade']}")
        if fit["score"] < 0.4:
            notes.append("weak street match; check the alignment")
        rec.update(block_group=res["block_group"], grade=res["grade"], position=res["position"],
                   position_iqr=f"{res['position_iqr'][0]}-{res['position_iqr'][1]}", at_address_position=res["at_address_position"],
                   label_anchored_grade=res["label_anchored_grade"], edge_distance_m=res["edge_distance_m"],
                   neighbours_within_60m="; ".join(f"{n['block_group']} {n['grade']} at {n['distance_m']} m" for n in res["neighbours_within_60m"]),
                   side_check=side, note="; ".join(notes))
        out.append(rec)
        print(f"{rid:>4} {address:45s} {res['grade']:2s} pos {res['position']:.3f}  {rec['note']}", flush=True)
    cols = ["id", "address", "matched_address", "lat", "lon", "block_group", "image", "zoom", "fit_score", "grade", "position",
            "position_iqr", "at_address_position", "label_anchored_grade", "edge_distance_m", "neighbours_within_60m", "side_check", "note"]
    with open(a.results, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for rec in out:
            w.writerow({c: rec.get(c, "") for c in cols})


if __name__ == "__main__":
    main()
