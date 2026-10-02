#!/usr/bin/env python3
"""Give a fit to screenshots whose street layer never loaded, from a fitted screenshot of the same map view.

Usage: align_streetless.py <folder> <streetless manifest.json> <zip> <reference view>

A ZIP-page map whose base tiles failed shows the coloured block groups with no white streets, so georef.py's street
matching cannot place it. When the same ZIP page was shot on other tabs with the streets loaded and the map not moved,
the block-group outlines sit at the same pixels. The colour edges between block groups are computed on both images
(on the fitted one only where it shows the colour layer, not streets, water or labels), and for each streetless shot the
integer offset within 12 px where the most edge pixels coincide exactly is found. The shots are accepted when every peak
lies within 1 px of the most common one and beats the best score more than 2 px away from it by 15 percent; the
reference fit is then shifted by the common offset. (Block-group edges are dense, so a peak is judged against its
surroundings, not against the median.) The streetless shots of the ZIP become a new view in manifest.json with
fits/view_NN.json beside the others; otherwise nothing is written. Check the new view's readings against block groups
that other pages also show before trusting it.
"""
import sys, os, json
import numpy as np
PIPE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, PIPE)
from georef import load_rgb, map_bounds, ui_exclusions

def colour_layer(A):
    """Pixels that show the block-group fill: saturated and not water blue."""
    A = A.astype(int); sat = (A.max(axis=2) - A.min(axis=2)) > 50
    water = (A[..., 2] > A[..., 0] + 40) & (A[..., 2] > A[..., 1] + 10)
    return sat & ~water

def edges(A, valid):
    A = A.astype(int); E = np.zeros(A.shape[:2], bool)
    dx = np.abs(A[:, 1:] - A[:, :-1]).sum(axis=2) > 45; E[:, :-1] |= dx & valid[:, 1:] & valid[:, :-1]
    dy = np.abs(A[1:] - A[:-1]).sum(axis=2) > 45; E[:-1] |= dy & valid[1:] & valid[:-1]
    return E

def surface(R_list, S, rng=12):
    """Exact-pixel edge coincidences for every offset (dx, dy) in [-rng, rng], with S(x + dx, y + dy) ~ R(x, y)."""
    H, W, _ = S.shape; top, left, right = map_bounds(S); bottom = H - 48
    ES = edges(S, colour_layer(S)); ES[:top + 5] = False; ES[bottom:] = False; ES[:, :left + 5] = False; ES[:, right - 5:] = False
    sc = np.zeros((2 * rng + 1, 2 * rng + 1))
    for R in R_list:
        ER = edges(R, colour_layer(R))
        for i, dy in enumerate(range(-rng, rng + 1)):
            for j, dx in enumerate(range(-rng, rng + 1)):
                a = ER[max(0, -dy):H - max(0, dy), max(0, -dx):W - max(0, dx)]
                b = ES[max(0, dy):H - max(0, -dy), max(0, dx):W - max(0, -dx)]
                sc[i, j] += (a & b).sum()
    return sc

def peak(sc, rng=12):
    i, j = np.unravel_index(sc.argmax(), sc.shape); away = np.ones_like(sc, bool); away[max(0, i - 2):i + 3, max(0, j - 2):j + 3] = False
    return (int(j - rng), int(i - rng)), float(sc.max() / max(sc[away].max(), 1))

def main():
    folder, sman, z, ref_view = os.path.abspath(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4])
    man = json.load(open(os.path.join(folder, 'manifest.json'))); st = json.load(open(sman))
    fit = json.load(open(os.path.join(folder, 'fits', 'view_%02d.json' % ref_view)))
    refs = [load_rgb(os.path.join(folder, 'x', f)) for f, m in man.items() if m['view'] == ref_view]
    files = sorted(f for f, m in st.items() if m['zip'] == z)
    peaks = []
    for f in files:
        o, r = peak(surface(refs, load_rgb(os.path.join(folder, 'x', f)))); peaks.append((o, r))
        print('%s %s: peak at dx=%d dy=%d, %.2f x the best score more than 2 px away' % (f, st[f]['type'], o[0], o[1], r))
    common = max(set(o for o, _ in peaks), key=lambda o: sum(1 for p, _ in peaks if p == o))
    if any(max(abs(o[0] - common[0]), abs(o[1] - common[1])) > 1 or r < 1.15 for o, r in peaks):
        print('the shots do not agree on one offset with a clear peak; nothing written'); return
    dx, dy = common
    nv = max(m['view'] for m in man.values()) + 1
    S0 = load_rgb(os.path.join(folder, 'x', files[0]))
    new = dict(fit, tx=fit['tx'] + dx, ty=fit['ty'] + dy, exclusions=ui_exclusions(S0), exemplar=files[0],
               streetless={'reference_view': ref_view, 'offset': [dx, dy], 'peaks': [[list(o), round(r, 2)] for o, r in peaks]})
    json.dump(new, open(os.path.join(folder, 'fits', 'view_%02d.json' % nv), 'w'))
    for f in files: man[f] = dict(st[f], view=nv)
    json.dump(man, open(os.path.join(folder, 'manifest.json'), 'w'), indent=0)
    print('view %d: %d streetless shots of %s, fit from view %d shifted by (%d, %d)' % (nv, len(files), z, ref_view, dx, dy))

if __name__ == '__main__': main()
