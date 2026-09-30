#!/usr/bin/env python3
"""Label a folder of CrimeGrade ZIP-page screenshots by the selected crime tab and the page's ZIP.

Screenshots of the ZIP page at the same window size render the tab label and the header line in the
same place, so identical crops mean identical text. `cluster` groups the tab crops, the ZIP-digit crops
and the map views (white-street mask, Jaccard > 0.9) and writes montages of one exemplar per cluster
to read by eye; `apply` takes the cluster labels and writes manifest.json for grade_by_view.py.

  label_screenshots.py cluster <folder>            # screenshots in <folder>/x/ (911x667 crops of the page)
  label_screenshots.py apply <folder> labels.json  # {"tab": {"0": "Robbery", ...}, "zip": {"0": "44104", ...}}
"""
import sys, os, json, collections
import numpy as np
from PIL import Image, ImageDraw
TAB=(8,96,208,127); ZIP=(583,2,642,26); MAP=(40,140,870,620)

def crops(d, files, box):
    return {f: np.asarray(Image.open(os.path.join(d,f)).convert('L').crop(box), dtype=np.float32) for f in files}

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

def cluster_views(d, files):
    groups=[]; assign={}
    for f in files:
        A=np.asarray(Image.open(os.path.join(d,f)).convert('RGB').crop(MAP), dtype=np.int16); m=A.min(axis=2)>235
        best=None
        for i,(gm,mem) in enumerate(groups):
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
        tabs, ta = cluster_text(crops(d,files,TAB), 12)
        zips, za = cluster_text(crops(d,files,ZIP), 10)
        va = cluster_views(d, files)
        montage(tabs, TAB, os.path.join(folder,'montage_tabs.png'), 3, 2)
        montage(zips, ZIP, os.path.join(folder,'montage_zips.png'), 6, 3)
        json.dump({'tab':ta,'zip':za,'view':va}, open(os.path.join(folder,'clusters.json'),'w'))
        print('tab clusters %d, zip clusters %d, views %d; label them from montage_tabs.png and montage_zips.png'%(len(tabs),len(zips),len(set(va.values()))))
    elif cmd=='apply':
        cl=json.load(open(os.path.join(folder,'clusters.json'))); lab=json.load(open(sys.argv[3]))
        man={f:{'zip':lab['zip'][str(cl['zip'][f])],'type':lab['tab'][str(cl['tab'][f])],'view':cl['view'][f]} for f in files}
        json.dump(man, open(os.path.join(folder,'manifest.json'),'w'), indent=0)
        byview=collections.defaultdict(list)
        for f,m in man.items(): byview[m['view']].append(m)
        for v in sorted(byview): print(v, collections.Counter(m['zip'] for m in byview[v]), sorted(m['type'] for m in byview[v]))
if __name__=='__main__': main()
