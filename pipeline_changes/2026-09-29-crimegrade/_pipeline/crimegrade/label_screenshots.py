#!/usr/bin/env python3
"""Label a folder of CrimeGrade ZIP-page screenshots by the selected crime tab and the page's ZIP.

Screenshots of the ZIP page at the same window size render the tab label and the header line in the
same place, so identical crops mean identical text. `cluster` groups the tab crops, the ZIP-digit crops
and the map views (white-street mask, Jaccard > 0.9) and writes montages of one exemplar per cluster
to read by eye; `apply` takes the cluster labels and writes manifest.json for grade_by_view.py.

  label_screenshots.py cluster <folder>            # screenshots in <folder>/x/ (911x667 crops of the page)
  label_screenshots.py apply <folder> labels.json  # {"tab": {"0": "Robbery", ...}, "zip": {"0": "44104", ...}}

2026-10-02: a page shot in a window 940 px or wider (the 955x663 and 955x690 shots of 10/2) shows no header line; its ZIP is
read from the overview sentence above the tab bar ("... a single grade for 22903."). The crops are placed from the selected
tab's blue top border, found on each image, so a page scrolled a few pixels still crops the same text. A shot with no
selected tab (the page still loading, or an advert over it) cannot be labelled and is listed as set aside.
"""
import sys, os, json, collections
import numpy as np
from PIL import Image, ImageDraw
TAB=(8,96,208,127); ZIP=(583,2,642,26); MAP=(40,140,870,620)

def tab_marker_row(A):
    """Row of the selected tab's blue top border (None when no tab is selected)."""
    for y in range(int(A.shape[0] * 0.35)):
        seg = A[y, 12:200].astype(int)
        if ((seg[:, 2] - seg[:, 0]) > 60).mean() > 0.9 and (seg[:, 2] > 150).mean() > 0.9: return y
    return None

def boxes(path):
    """TAB, ZIP and MAP crop boxes for one screenshot. Narrower windows keep the fixed boxes the first batches used;
    a window 940 px or wider takes them from the selected-tab border (the ZIP from the overview sentence 91 px above it)."""
    im = Image.open(path).convert('RGB'); W, H = im.size
    if W < 940: return TAB, ZIP, MAP
    y = tab_marker_row(np.asarray(im))
    if y is None: return None
    return (8, y + 5, 208, y + 36), (590, y - 91, 700, y - 61), (40, y + 49, 870, y + 529)

def crops(d, files, which):
    out = {}
    for f in files:
        b = boxes(os.path.join(d, f))
        out[f] = np.asarray(Image.open(os.path.join(d, f)).convert('L').crop(b[which]), dtype=np.float32)
    return out

def cluster_text(arrs, tol_px):
    clusters=[]; assign={}
    for f,a in arrs.items():
        b=a<140; best=None
        for i,(ex,exb,mem) in enumerate(clusters):
            ham=int((b^exb).sum())
            if ham<tol_px and (best is None or ham<best[1]): best=(i,ham)
        if best is None: clusters.append([a,b,[f]]); assign[f]=len(clusters)-1
        else: clusters[best[0]][2].append(f); assign[f]=best[0]
    return clusters, assign

def frame_key(path):
    """Image height and selected-tab row: shots in one view must share both, since a fit is in pixel coordinates."""
    im=Image.open(path).convert('RGB'); return im.size[1], (tab_marker_row(np.asarray(im)) if im.size[0]>=940 else None)

def cluster_views(d, files):
    groups=[]; assign={}; keys={}
    for f in files:
        A=np.asarray(Image.open(os.path.join(d,f)).convert('RGB').crop(boxes(os.path.join(d,f))[2]), dtype=np.int16); m=A.min(axis=2)>235
        keys[f]=frame_key(os.path.join(d,f)); best=None
        for i,(gm,mem) in enumerate(groups):
            if keys[mem[0]]!=keys[f]: continue   # 2026-10-02: a scrolled page puts the same map at other pixels
            j=(m&gm).sum()/max((m|gm).sum(),1)
            if j>0.90 and (best is None or j>best[1]): best=(i,j)
        if best is None: groups.append([m,[f]]); assign[f]=len(groups)-1
        else: groups[best[0]][1].append(f); assign[f]=best[0]
    return assign

def montage(clusters, box, out, cols, scale):
    w=box[2]-box[0]; h=box[3]-box[1]; pad=8; labw=80; rows=(len(clusters)+cols-1)//cols
    M=Image.new('RGB',(cols*(w+labw+pad), rows*(h+pad)+pad),'white'); dr=ImageDraw.Draw(M)
    for i,(ex,exb,mem) in enumerate(clusters):
        r,c=divmod(i,cols); x=c*(w+labw+pad); y=pad+r*(h+pad)
        dr.text((x+2,y+7), '#%d n=%d'%(i,len(mem)), fill='red'); M.paste(Image.fromarray(ex.astype(np.uint8)).convert('RGB'),(x+labw,y))
    M.resize((M.width*scale,M.height*scale), Image.LANCZOS).save(out)

def main():
    cmd, folder = sys.argv[1], os.path.abspath(sys.argv[2]); d=os.path.join(folder,'x'); files=sorted(os.listdir(d))
    if cmd=='cluster':
        aside=[f for f in files if boxes(os.path.join(d,f)) is None]
        if aside: print('set aside, no selected tab:', ', '.join(aside))
        files=[f for f in files if f not in aside]
        tabs, ta = cluster_text(crops(d,files,0), 12)
        zips, za = cluster_text(crops(d,files,1), 10)
        va = cluster_views(d, files)
        montage(tabs, TAB, os.path.join(folder,'montage_tabs.png'), 3, 2)
        zb = ZIP if not files or boxes(os.path.join(d,files[0]))[1] == ZIP else (0, 0, 110, 30)
        montage(zips, zb, os.path.join(folder,'montage_zips.png'), 6, 3)
        json.dump({'tab':ta,'zip':za,'view':va,'set_aside':aside}, open(os.path.join(folder,'clusters.json'),'w'))
        print('tab clusters %d, zip clusters %d, views %d; label them from montage_tabs.png and montage_zips.png'%(len(tabs),len(zips),len(set(va.values()))))
    elif cmd=='apply':
        cl=json.load(open(os.path.join(folder,'clusters.json'))); lab=json.load(open(sys.argv[3]))
        man={f:{'zip':lab['zip'][str(cl['zip'][f])],'type':lab['tab'][str(cl['tab'][f])],'view':cl['view'][f]} for f in files
             if f not in cl.get('set_aside',[]) and lab['tab'].get(str(cl['tab'][f])) and lab['zip'].get(str(cl['zip'][f]))}
        json.dump(man, open(os.path.join(folder,'manifest.json'),'w'), indent=0)
        byview=collections.defaultdict(list)
        for f,m in man.items(): byview[m['view']].append(m)
        for v in sorted(byview): print(v, collections.Counter(m['zip'] for m in byview[v]), sorted(m['type'] for m in byview[v]))
if __name__=='__main__': main()
