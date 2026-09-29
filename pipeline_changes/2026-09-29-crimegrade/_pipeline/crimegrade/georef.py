#!/usr/bin/env python3
"""Georeference a CrimeGrade map image: the static map on a ZIP page (saved as an image), a screenshot of it, or a
screenshot of the interactive map.

CrimeGrade draws its maps in Web Mercator, so for zoom z an image pixel relates to longitude and latitude by
    x = s * lon + tx,    y = -s * merc_y(lat) + ty,    s = 256 * 2**z / 360 pixels per degree.
This module finds s, tx and ty by matching the image's white streets to Census TIGER street centrelines. For each
candidate zoom it draws the centrelines around a point known to be on the map (the address being graded) and slides
the image over the drawing; the zoom and offset with the highest normalised cross-correlation win. A coarse pass at
half resolution covers the zoom range, then a fine pass at full resolution refines around the best coarse zoom.

Validated 2026-09-29 against two label-calibrated maps: the Canton 44710 static map (address pixel within 1.6 px)
and the Akron 44320 static map (five neighbourhood labels within 1 px).

usage: python3 georef.py IMAGE LAT LON [--zmin 12.3] [--zmax 14.8] [--cache DIR]
"""
import argparse, colorsys, json, math, os, statistics, time, urllib.parse, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
TIGER_ROADS = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Transportation/MapServer/{}/query"
ROAD_LAYERS = ((2, 9), (6, 6), (8, 3))        # (TIGERweb layer, drawn width in px): primary, secondary, local roads
WHITE_MIN = 232                                 # a pixel is street when all three channels are at least this bright
COARSE_STEP = 0.04                              # zoom step of the coarse pass
FINE_HALF, FINE_STEP, FINE_PAD = 0.05, 0.005, 60
UA = {"User-Agent": "duplex-campaign-crimegrade/1.0"}


def merc_y(lat):
    return math.degrees(math.log(math.tan(math.radians(lat) / 2 + math.pi / 4)))


def px_per_degree(zoom):
    return 256 * 2 ** zoom / 360


def get_json(url, params, tries=4):
    full = url + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(full, headers=UA), timeout=180) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * 2 ** i)


def load_rgb(path):
    return np.asarray(Image.open(path).convert("RGB"))


def _hue(c):
    h = colorsys.rgb_to_hsv(*(v / 255 for v in c))[0]
    return h - 1 if h > 0.8 else h                  # red wraps round to just below zero


def find_legend(A):
    """The colour legend is a smooth gradient from green to red along one row. Returns (y, x0, x1) or None."""
    H, W, _ = A.shape
    sat = (A.max(axis=2).astype(int) - A.min(axis=2)) > 50
    best = None
    for y in range(int(H * 0.55), H):
        edges = np.diff(np.concatenate(([0], sat[y].astype(np.int8), [0])))
        for x0, x1 in zip(np.where(edges == 1)[0], np.where(edges == -1)[0] - 1):
            if x1 - x0 < 150 or (best and x1 - x0 <= best[2] - best[1]):
                continue
            hues = [_hue(tuple(int(v) for v in np.median(A[y, max(x0, int(x0 + t * (x1 - x0)) - 2):int(x0 + t * (x1 - x0)) + 3], axis=0)))
                    for t in np.linspace(0.02, 0.98, 20)]
            falling = sum(1 for a, b in zip(hues, hues[1:]) if b < a - 0.001)
            rising = sum(1 for a, b in zip(hues, hues[1:]) if b > a + 0.01)
            if hues[0] > 0.2 and hues[-1] < 0.05 and falling >= 12 and rising == 0:
                best = (y, int(x0), int(x1))
    return best


def ui_exclusions(A):
    """Rectangles (x0, y0, x1, y1) holding page furniture rather than map: the colour legend (the full-width bar with
    its letters, or the small 'Crime Risk' box and the colour-blind toggle beside it), the zoom buttons and the
    full-screen and info buttons. Map pixels inside them are ignored when matching streets and reading colours."""
    H, W, _ = A.shape
    rects = [(0, 0, 70, 110), (W - 70, 0, W, 70), (W - 60, H - 60, W, H)]
    leg = find_legend(A)
    if leg:
        y, x0, x1 = leg
        if x1 - x0 >= 0.6 * W:
            rects.append((0, max(0, y - 30), W, H))
        else:
            rects.append((max(0, x0 - 30), max(0, y - 60), min(W, x1 + 200), min(H, y + 60)))
    return rects


def street_mask(A, rects):
    m = (A.min(axis=2) >= WHITE_MIN).astype(np.uint8) * 255
    for x0, y0, x1, y1 in rects:
        m[y0:y1, x0:x1] = 0
    return m


def fetch_roads(lat, lon, half_lon, half_lat, cache_dir):
    """TIGER street centrelines inside a box around (lat, lon), cached as JSON."""
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"roads_{lat:.4f}_{lon:.4f}_{half_lon:.3f}_{half_lat:.3f}.json")
    if os.path.exists(path):
        return json.load(open(path))
    env = f"{lon - half_lon},{lat - half_lat},{lon + half_lon},{lat + half_lat}"
    roads = []
    for layer, width in ROAD_LAYERS:
        offset = 0
        while True:
            d = get_json(TIGER_ROADS.format(layer), {"geometry": env, "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                         "spatialRel": "esriSpatialRelIntersects", "outFields": "MTFCC", "returnGeometry": "true",
                         "outSR": 4326, "geometryPrecision": 5, "maxAllowableOffset": 0.00003,
                         "resultOffset": offset, "resultRecordCount": 20000, "f": "json"})
            feats = d.get("features", [])
            for f in feats:
                for p in f["geometry"].get("paths", []):
                    roads.append((width, p))
            if len(feats) < 20000 and not d.get("exceededTransferLimit"):
                break
            offset += len(feats)
    json.dump(roads, open(path, "w"))
    return roads


def _prepare(roads):
    out = []
    for width, p in roads:
        a = np.array([(x, merc_y(y)) for x, y in p], np.float64)
        out.append((width, a, a[:, 0].min(), a[:, 0].max(), a[:, 1].min(), a[:, 1].max()))
    return out


def _rasterise(roads, s, txc, tyc, Wc, Hc, f):
    im = Image.new("L", (Wc, Hc), 0)
    d = ImageDraw.Draw(im)
    lo0, lo1 = (-20 - txc) / s, (Wc + 20 - txc) / s
    my0, my1 = (tyc - Hc - 20) / s, (tyc + 20) / s
    for width, a, xmin, xmax, ymin, ymax in roads:
        if xmax < lo0 or xmin > lo1 or ymax < my0 or ymin > my1:
            continue
        pts = np.column_stack((s * a[:, 0] + txc, -s * a[:, 1] + tyc))
        d.line(pts.ravel().tolist(), fill=255, width=max(1, round(width * f)))
    return im


def _blur(im, r):
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), dtype=np.float32)


def _ncc_best(A, B):
    """Offset (dx, dy) of image A inside canvas B with the highest normalised cross-correlation."""
    ha, wa = A.shape
    hb, wb = B.shape
    A = A - A.mean()
    na = float(np.sqrt((A * A).sum())) or 1.0
    FA = np.fft.rfft2(A, s=(hb, wb))
    FB = np.fft.rfft2(B)
    corr = np.fft.irfft2(FB * np.conj(FA), s=(hb, wb))
    box = np.zeros((hb, wb), np.float32)
    box[:ha, :wa] = 1
    Fbox = np.conj(np.fft.rfft2(box))
    S1 = np.fft.irfft2(FB * Fbox, s=(hb, wb))
    S2 = np.fft.irfft2(np.fft.rfft2(B * B) * Fbox, s=(hb, wb))
    var = np.maximum(S2 - S1 * S1 / (ha * wa), 1e-6)
    v = (corr / (na * np.sqrt(var)))[: hb - ha + 1, : wb - wa + 1]
    iy, ix = np.unravel_index(np.argmax(v), v.shape)
    return float(v[iy, ix]), int(ix), int(iy)


def georeference(image_path, lat, lon, cache_dir=os.path.join(HERE, "cache"), zmin=12.3, zmax=14.8):
    """Returns {"s", "tx", "ty", "zoom", "score", "runner_up_zooms", "exclusions"} for the image, given one point on it."""
    A = load_rgb(image_path)
    H, W, _ = A.shape
    rects = ui_exclusions(A)
    mask = Image.fromarray(street_mask(A, rects))
    padx, pady = W // 2 + 40, H // 2 + 40            # the known point may sit anywhere on the image
    smin = px_per_degree(zmin)
    half_lon = (W / 2 + padx + 80) / smin
    half_lat = (H / 2 + pady + 80) / smin * math.cos(math.radians(lat))
    roads = _prepare(fetch_roads(lat, lon, half_lon, half_lat, cache_dir))

    f = 0.5
    Mc = _blur(mask.resize((int(W * f), int(H * f)), Image.BILINEAR), 1.5)
    Wc, Hc = int((W + 2 * padx) * f), int((H + 2 * pady) * f)
    coarse = []
    for z in np.arange(zmin, zmax + 1e-9, COARSE_STEP):
        s = px_per_degree(z) * f
        txc, tyc = Wc / 2 - s * lon, Hc / 2 + s * merc_y(lat)
        sc, dx, dy = _ncc_best(Mc, _blur(_rasterise(roads, s, txc, tyc, Wc, Hc, f), 1.5))
        coarse.append((sc, float(z), (txc - dx) / f, (tyc - dy) / f))
    coarse.sort(reverse=True)
    _, z0, tx0, ty0 = coarse[0]

    s0 = px_per_degree(z0)
    lon_c, my_c = (W / 2 - tx0) / s0, (ty0 - H / 2) / s0      # map position of the image centre
    Mf = _blur(mask, 2.0)
    Wc, Hc = W + 2 * FINE_PAD, H + 2 * FINE_PAD
    best = None
    for z in np.arange(z0 - FINE_HALF, z0 + FINE_HALF + 1e-9, FINE_STEP):
        s = px_per_degree(z)
        txc, tyc = Wc / 2 - s * lon_c, Hc / 2 + s * my_c
        sc, dx, dy = _ncc_best(Mf, _blur(_rasterise(roads, s, txc, tyc, Wc, Hc, 1.0), 2.0))
        if best is None or sc > best[0]:
            best = (sc, float(z), txc - dx, tyc - dy)
    sc, z, tx, ty = best
    return {"s": px_per_degree(z), "tx": tx, "ty": ty, "zoom": round(z, 3), "score": round(sc, 3),
            "runner_up_zooms": [[round(c[1], 2), round(c[0], 3)] for c in coarse[1:4]], "exclusions": rects}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("image"); ap.add_argument("lat", type=float); ap.add_argument("lon", type=float)
    ap.add_argument("--zmin", type=float, default=12.3); ap.add_argument("--zmax", type=float, default=14.8)
    ap.add_argument("--cache", default=os.path.join(HERE, "cache"))
    a = ap.parse_args()
    print(json.dumps(georeference(a.image, a.lat, a.lon, a.cache, a.zmin, a.zmax), indent=1))
