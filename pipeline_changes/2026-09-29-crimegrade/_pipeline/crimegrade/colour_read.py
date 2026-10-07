#!/usr/bin/env python3
"""Read the CrimeGrade Overall Crime grade for an address from a georeferenced map image.

CrimeGrade fills each census block group with one colour from its legend ramp; the colour edges follow block-group
lines and the fill is close to uniform inside each group. So the reader takes the address's block group (from the
Census geocoder), draws its polygon on the image, and places every pixel inside it on the legend ramp. Pixels more
than TOL colour units from the ramp are discarded: white streets, anti-aliased street edges, labels, the watermark
and the darkened "Click the map to explore" band. The block group's median ramp position is the reading.

Ramp position runs from 0 at the A+ end of the legend to 1 at the F end. The legend prints only A+, B, C, D and F,
so the thirteen steps are inferred. The primary reading splits the ramp into CrimeGrade's thirteen equal percentile
bands (A+ above the 92.31st percentile ... F below the 7.72nd). The alternative anchors each printed letter where the
legend prints it and interpolates the steps between. On the 25 Ohio addresses of 2026-09-29 the two readings
disagreed on four, each time within the D family.
"""
import json, math, os, time, urllib.parse, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
TIGER_BG = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/1/query"
STEPS = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]
TOL = 6.0
UA = {"User-Agent": "duplex-campaign-crimegrade/1.0"}

_ramp = json.load(open(os.path.join(HERE, "ramp.json")))["ramp"]
_ramp = [(p, c) for p, c in _ramp if 0.004 <= p <= 0.996]          # drop the bar's rounded end caps
RAMP_P = np.array([p for p, _ in _ramp], np.float32)
RAMP_C = np.array([c for _, c in _ramp], np.float32)


def merc_y(lat):
    return math.degrees(math.log(math.tan(math.radians(lat) / 2 + math.pi / 4)))


def grade_equal_bands(p):
    return STEPS[min(12, int(p * 13))]


def grade_label_anchored(p):
    anchors = [(0.02, 0), (0.26, 4), (0.50, 7), (0.74, 10), (0.98, 12)]
    if p <= anchors[0][0]:
        return "A+"
    if p >= anchors[-1][0]:
        return "F"
    for (p0, i0), (p1, i1) in zip(anchors, anchors[1:]):
        if p0 <= p <= p1:
            return STEPS[i0 + int((p - p0) / (p1 - p0) * (i1 - i0) + 0.5)]


def band_line_note(p, width=0.005):
    """Names the grade line p sits on, when it is within `width` of one."""
    k = round(p * 13)
    if 0 < k < 13 and abs(p - k / 13) < width:
        return f"on the {STEPS[k - 1]}/{STEPS[k]} line"
    return ""


def ramp_positions(pixels):
    """Ramp positions of the pixels (N x 3) that lie on the legend ramp; off-ramp pixels are dropped."""
    if len(pixels) == 0:
        return np.zeros(0, np.float32)
    u, inv = np.unique(pixels.reshape(-1, 3), axis=0, return_inverse=True)
    d = np.sqrt(((u[:, None, :].astype(np.float32) - RAMP_C[None, :, :]) ** 2).sum(-1))
    k = d.argmin(1)
    pos = np.where(d[np.arange(len(u)), k] <= TOL, RAMP_P[k], np.nan)[inv.ravel()]
    return pos[~np.isnan(pos)]


def _get_json(params, tries=4):
    url = TIGER_BG + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * 2 ** i)


def block_groups_near(lat, lon, cache_dir, r=0.004):
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"bg_near_{lat:.5f}_{lon:.5f}.json")
    if os.path.exists(path):
        return json.load(open(path))["features"]
    d = _get_json({"geometry": f"{lon - r * 1.3},{lat - r},{lon + r * 1.3},{lat + r}", "geometryType": "esriGeometryEnvelope",
                   "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "GEOID", "returnGeometry": "true",
                   "outSR": 4326, "f": "geojson"})
    json.dump(d, open(path, "w"))
    return d["features"]


def block_group_at(lat, lon):
    d = _get_json({"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                   "spatialRel": "esriSpatialRelIntersects", "outFields": "GEOID", "returnGeometry": "false", "f": "json"})
    f = d.get("features", [])
    return f[0]["attributes"]["GEOID"] if f else None


def _rings(g):
    return [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]


def _all_rings(g):
    return g["coordinates"] if g["type"] == "Polygon" else [r for p in g["coordinates"] for r in p]


def _mask(geom, proj, W, H, erode):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for r in _rings(geom):
        d.polygon([proj(lo, la) for lo, la in r], fill=255)
    if erode:
        m = m.filter(ImageFilter.MinFilter(2 * erode + 1))
    return np.asarray(m) > 0


def edge_distance_m(lat, lon, geom):
    kx, best = 111320 * math.cos(math.radians(lat)), 1e12
    for r in _all_rings(geom):
        for (x1, y1), (x2, y2) in zip(r, r[1:]):
            ax, ay, bx, by = (x1 - lon) * kx, (y1 - lat) * 110574, (x2 - lon) * kx, (y2 - lat) * 110574
            dx, dy = bx - ax, by - ay
            L = dx * dx + dy * dy
            t = 0 if L == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L))
            best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best


def read_address(A, fit, lat, lon, block_group, cache_dir=os.path.join(HERE, "cache")):
    """A: RGB array of the map image; fit: output of georef.georeference; block_group: 12-digit GEOID."""
    H, W, _ = A.shape
    s, tx, ty = fit["s"], fit["tx"], fit["ty"]
    proj = lambda lo, la: (s * lo + tx, -s * merc_y(la) + ty)
    x, y = proj(lon, lat)
    if not (0 <= x < W and 0 <= y < H):
        return {"error": "the address falls outside the image"}
    keep = np.ones((H, W), bool)
    for x0, y0, x1, y1 in fit.get("exclusions", []):
        keep[y0:y1, x0:x1] = False
    feats = block_groups_near(lat, lon, cache_dir)
    own = [f for f in feats if f["properties"]["GEOID"] == block_group]
    if not own:
        return {"error": f"block group {block_group} not found near the address"}
    g = own[0]["geometry"]
    P = ramp_positions(A[_mask(g, proj, W, H, 2) & keep])
    if len(P) < 20:
        return {"error": "too few map pixels inside the block group"}
    pos = float(np.median(P))
    q25, q75 = (float(v) for v in np.percentile(P, [25, 75]))
    near = _mask(g, proj, W, H, 1) & keep
    yy, xx = np.ogrid[:H, :W]
    for rad in (5, 7, 9, 12, 16, 22):
        Lp = ramp_positions(A[near & ((xx - x) ** 2 + (yy - y) ** 2 <= rad * rad)])
        if len(Lp) >= 20:
            break
    neighbours = []
    for f in feats:
        gid = f["properties"]["GEOID"]
        if gid == block_group:
            continue
        dm = edge_distance_m(lat, lon, f["geometry"])
        if dm <= 60:
            Pn = ramp_positions(A[_mask(f["geometry"], proj, W, H, 2) & keep])
            if len(Pn) >= 20:
                pn = float(np.median(Pn))
                neighbours.append({"block_group": gid, "distance_m": round(dm), "position": round(pn, 3), "grade": grade_equal_bands(pn)})
    return {"pixel": [round(x), round(y)], "block_group": block_group, "position": round(pos, 3),
            "position_iqr": [round(q25, 3), round(q75, 3)], "pixels_on_ramp": int(len(P)),
            "grade": grade_equal_bands(pos), "label_anchored_grade": grade_label_anchored(pos),
            "at_address_position": round(float(np.median(Lp)), 3) if len(Lp) else None,
            "at_address_radius_px": rad, "edge_distance_m": round(edge_distance_m(lat, lon, g)),
            "neighbours_within_60m": neighbours, "line_note": band_line_note(pos)}
