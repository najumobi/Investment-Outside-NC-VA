#!/usr/bin/env python3
"""Check every fitted view of a batch by the one-colour test.

Usage: check_fits.py <batch folder> [<batch folder> ...]

CrimeGrade fills each 2020 block group with a single colour, so under a correct fit nearly every block group
with 300 or more pixels on the legend ramp reads as one colour (interquartile range of its ramp positions 0.02
or less; across the 2026-09-30 to 10-02 batches it is 100 percent). Under a wrong fit the outlines straddle
colour edges and the share falls. Prints, per view: the street-match score, the block groups tested and the
share that read as one colour; views under 90 percent (or with fewer than 5 testable block groups) are flagged.
"""
import sys, os, json, math, collections
import numpy as np
PIPE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, PIPE)
from georef import load_rgb, map_bounds
from colour_read import ramp_positions, _mask, merc_y
from build_crime_bg import fetch_bgs

def view_check(folder, v, files, fit):
    s, tx, ty = fit['s'], fit['tx'], fit['ty']; proj = lambda lo, la: (s * lo + tx, -s * merc_y(la) + ty)
    out = []
    for f in files[:2]:
        A = load_rgb(os.path.join(folder, 'x', f)); H, W, _ = A.shape; top, left, right = map_bounds(A); bottom = H - 48
        def inv(px, py):
            lon = (px - tx) / s; my = (ty - py) / s; return lon, math.degrees(2 * math.atan(math.exp(math.radians(my))) - math.pi / 2)
        lon0, lat1 = inv(left, top); lon1, lat0 = inv(right, bottom)
        keep = np.ones((H, W), bool)
        for x0, y0, x1, y1 in fit.get('exclusions', []): keep[y0:y1, x0:x1] = False
        keep[:top, :] = False; keep[bottom:, :] = False; keep[:, :left] = False; keep[:, right:] = False
        for ft in fetch_bgs([lon0, lat0, lon1, lat1]):
            if (ft['properties'].get('POP100') or 0) < 150 or not ft.get('geometry'): continue
            P = ramp_positions(A[_mask(ft['geometry'], proj, W, H, 2) & keep])
            if len(P) >= 300: q = np.percentile(P, [25, 75]); out.append(q[1] - q[0] <= 0.02)
    return len(out), (float(np.mean(out)) if out else float('nan'))

def main():
    for folder in sys.argv[1:]:
        folder = os.path.abspath(folder); man = json.load(open(os.path.join(folder, 'manifest.json')))
        views = collections.defaultdict(list)
        for f, m in man.items(): views[m['view']].append(f)
        for v in sorted(views):
            fp = os.path.join(folder, 'fits', 'view_%02d.json' % v)
            if not os.path.exists(fp): print('%s view %d: no fit' % (os.path.basename(folder), v)); continue
            fit = json.load(open(fp)); n, share = view_check(folder, v, sorted(views[v]), fit)
            flag = '  <-- check' if (n < 5 or not share >= 0.9) else ''
            print('%s view %2d zip %s score %.3f: %d block groups tested, %.0f%% one colour%s' % (
                os.path.basename(folder), v, man[views[v][0]]['zip'], fit.get('score') or 0, n, 100 * share if n else 0, flag), flush=True)

if __name__ == '__main__': main()
