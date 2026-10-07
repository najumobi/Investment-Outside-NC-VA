#!/usr/bin/env python3
"""Copy a read batch into the pipeline folder: renamed images under maps/<tag>/, a manifest CSV (one row per
screenshot with its ZIP, crime, view and status), the readings CSV and an address-by-crime matrix.

Usage: package_batch.py <batch folder> <tag> <date> [--set-aside "<note>"]
The batch folder holds x/, manifest.json, optional dropped.json ({screenshot: {..., "reason"}}) and
samples_results.csv from grade_by_view.py. --set-aside marks every read screenshot with the note instead
of "read" (a batch whose address lies off the map)."""
import sys, os, json, csv, shutil, collections
import numpy as np
PIPE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(os.path.dirname(PIPE))
from colour_read import grade_equal_bands
folder=os.path.abspath(sys.argv[1]); tag=sys.argv[2]; date=sys.argv[3]
aside=sys.argv[sys.argv.index('--set-aside')+1] if '--set-aside' in sys.argv else None
man=json.load(open(os.path.join(folder,'manifest.json')))
dropped=json.load(open(os.path.join(folder,'dropped.json'))) if os.path.exists(os.path.join(folder,'dropped.json')) else {}
allm=dict(man); allm.update({f:dict(m) for f,m in dropped.items()})
os.makedirs(os.path.join(ROOT,'maps',tag),exist_ok=True); cnt=collections.Counter(); newname={}
for f in sorted(allm):
    m=allm[f]; slug=m['type'].lower().replace('-related crime','').replace(' ','_'); key=(m['zip'],slug); cnt[key]+=1
    nn='%s_%s%s.png'%(m['zip'],slug,'' if cnt[key]==1 else '_%d'%cnt[key]); newname[f]=nn
    shutil.copy2(os.path.join(folder,'x',f),os.path.join(ROOT,'maps',tag,nn))
with open(os.path.join(ROOT,'%s_manifest_%s.csv'%(tag,date)),'w',newline='') as fh:
    w=csv.writer(fh); w.writerow(['image','screenshot','zip_page','crime','view','type_inferred','status'])
    for f in sorted(allm,key=lambda f:(allm[f]['zip'],allm[f]['type'],f)):
        m=allm[f]; st='dropped: '+m.get('reason','') if f in dropped else ('set aside: '+aside if aside else 'read')
        w.writerow(['maps/%s/%s'%(tag,newname[f]),f,m['zip'],m['type'],m['view'],'yes' if m.get('inferred') else '',st])
res=os.path.join(folder,'samples_results.csv'); n=0
if os.path.exists(res):
    rows=list(csv.DictReader(open(res)))
    for r in rows:
        r['image']='maps/%s/%s'%(tag,newname.get(r['image'],r['image']))
        if r['type']=='?blank': r['type']=man.get(r['image'],{}).get('type',r['type'])
    if rows:
        with open(os.path.join(ROOT,'crimegrade_%s_readings_%s.csv'%(tag,date)),'w',newline='') as fh:
            w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        tab=collections.defaultdict(lambda: collections.defaultdict(list)); meta={}
        for r in rows:
            if r.get('position'): tab[r['id']][r['type']].append(float(r['position'])); meta[r['id']]=(r['address'],r['source'],r['address'].strip()[-5:])
        types=['Robbery','Assault','Burglary','Vandalism','Drug-Related Crime','Murder','Theft','Vehicle Theft','Arson']
        types=[t for t in types if any(t in tab[i] for i in tab)]
        with open(os.path.join(ROOT,'crimegrade_%s_%s.csv'%(tag,date)),'w',newline='') as fh:
            w=csv.writer(fh); w.writerow(['id','address','source','zip']+[t+'_pos' for t in types]+[t+'_grade' for t in types])
            for i in sorted(tab,key=lambda i:(meta[i][1]!='photo list',i)):
                a,src,z=meta[i]; pos={t:float(np.mean(v)) for t,v in tab[i].items()}
                w.writerow([i,a,src,z]+['%.3f'%pos[t] if t in pos else '' for t in types]+[grade_equal_bands(pos[t]) if t in pos else '' for t in types])
        n=len(rows)
print('%s: %d images, %d readings, %d dropped'%(tag,len(newname),n,len(dropped)))
