"""Compare CrimeGrade Robbery block-group colours (read from screenshots) with recorded robbery rates.
Philadelphia: incidents from OpenDataPhilly (Carto), 2024-2025, point-in-polygon into 2020 block groups.
Cleveland: Cleveland Division of Police incidents 2024-2025 (to 2025-11-11), pre-tagged with CENSUS_BG_GEOID."""
import json, math, os, sys, csv, numpy as np
CG='/home/user/Investment-Outside-NC-VA/pipeline_changes/2026-09-29-crimegrade'
sys.path.insert(0,CG+'/_pipeline/crimegrade')
from colour_read import ramp_positions, _mask, merc_y, grade_equal_bands
from georef import load_rgb, map_bounds
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
meta=json.load(open('meta.json'))
def rings(g): return [g['coordinates'][0]] if g['type']=='Polygon' else [p[0] for p in g['coordinates']]
def pip(ring,xs,ys):
    r=np.asarray(ring); x0,y0=r[:-1,0],r[:-1,1]; x1,y1=r[1:,0],r[1:,1]
    inside=np.zeros(len(xs),bool)
    for a,b,c,d in zip(x0,y0,x1,y1):
        cond=((b>ys)!=(d>ys)) & (xs < (c-a)*(ys-b)/(d-b+1e-12)+a)
        inside^=cond
    return inside
def read_map(m):
    A=load_rgb(m['img']); H,W,_=A.shape; fit=m['fit']; s,tx,ty=fit['s'],fit['tx'],fit['ty']
    proj=lambda lo,la:(s*lo+tx,-s*merc_y(la)+ty)
    keep=np.ones((H,W),bool)
    for x0,y0,x1,y1 in fit.get('exclusions',[]): keep[y0:y1,x0:x1]=False
    top,left,right=map_bounds(A); keep[:top,:]=False; keep[H-48:,:]=False; keep[:,:left]=False; keep[:,right:]=False
    return A,H,W,proj,keep
def bg_positions(m,feats):
    A,H,W,proj,keep=read_map(m); out={}
    for f in feats:
        g=f['geometry']; pts=[proj(lo,la) for r in rings(g) for lo,la in r]
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        bx0,bx1,by0,by1=min(xs),max(xs),min(ys),max(ys)
        if bx1<0 or by1<0 or bx0>W or by0>H: continue
        inside_frac=(max(0,min(bx1,W)-max(bx0,0))*max(0,min(by1,H)-max(by0,0)))/max(1e-9,(bx1-bx0)*(by1-by0))
        if inside_frac<0.6: continue
        mk=_mask(g,proj,W,H,2)&keep
        P=ramp_positions(A[mk])
        if len(P)<300: continue
        out[f['properties']['GEOID']]=(float(np.median(P)),float(np.percentile(P,75)-np.percentile(P,25)),int(len(P)))
    return out
rows=[]
# ---- Philadelphia
for zc in ['19139','19131']:
    m=meta[zc]; feats=json.load(open(f'bg_{zc}.geojson'))['features']; pts=json.load(open(f'rob_{zc}.json'))
    xs=np.array([p['x'] for p in pts],float); ys=np.array([p['y'] for p in pts],float)
    pos=bg_positions(m,feats)
    for f in feats:
        gid=f['properties']['GEOID']
        if gid not in pos: continue
        n=0
        for r in rings(f['geometry']): n+=int(pip(r,xs,ys).sum())
        pop=f['properties']['POP100'] or 0
        rows.append(dict(city='Philadelphia',map=zc,geoid=gid,pop=pop,position=pos[gid][0],iqr=pos[gid][1],pixels=pos[gid][2],count=n,years=2.0))
# ---- Cleveland
import gzip
cuy={f['properties']['GEOID']:f for f in json.load(gzip.open('bg_cuyahoga.geojson.gz','rt'))['features']}
counts=json.load(open('cle_counts_2024_25.json'))
YEARS_CLE=1+ (31+28+31+30+31+30+31+31+30+31+11)/365   # 2024 + 2025 through Nov 11
for key,m in meta.items():
    if m['city']!='cleveland': continue
    lon0,lat0,lon1,lat1=m['bounds']
    feats=[f for f in cuy.values() if any(lon0<=lo<=lon1 and lat0<=la<=lat1 for r in rings(f['geometry']) for lo,la in r)]
    pos=bg_positions(m,feats)
    for gid,(p,iq,npx) in pos.items():
        f=cuy[gid]; pop=f['properties']['POP100'] or 0
        rows.append(dict(city='Cleveland',map=key,geoid=gid,pop=pop,position=p,iqr=iq,pixels=npx,count=counts['Robbery'].get(gid,0),years=YEARS_CLE))
    print(key,'block groups read:',len(pos),flush=True)
# ---- combine: one row per city+geoid (mean position over maps)
from collections import defaultdict
agg=defaultdict(list)
for r in rows: agg[(r['city'],r['geoid'])].append(r)
final=[]
for (city,gid),rs in agg.items():
    ps=[r['position'] for r in rs]
    r0=rs[0]; final.append(dict(city=city,geoid=gid,pop=r0['pop'],n_maps=len(rs),position=float(np.mean(ps)),position_spread=float(max(ps)-min(ps)),
        letter=grade_equal_bands(float(np.mean(ps))),count=r0['count'],years=r0['years'],rate_per_1000=(r0['count']/r0['years']/r0['pop']*1000) if r0['pop']>0 else None))
with open('results_bg.csv','w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(final[0].keys())); w.writeheader(); w.writerows(final)
def spearman(a,b):
    a=np.asarray(a); b=np.asarray(b); ra=a.argsort().argsort(); rb=b.argsort().argsort(); return float(np.corrcoef(ra,rb)[0,1])
summary={}
for city in ['Philadelphia','Cleveland']:
    F=[r for r in final if r['city']==city and r['pop']>=150]
    pos=[r['position'] for r in F]; rate=[r['rate_per_1000'] for r in F]; lr=[math.log1p(x) for x in rate]
    multi=[r for r in F if r['n_maps']>1]
    s=dict(block_groups=len(F),robberies=sum(r['count'] for r in F),spearman=round(spearman(pos,rate),3),pearson_log=round(float(np.corrcoef(pos,lr)[0,1]),3),
           multi_map_bgs=len(multi),median_spread_between_maps=round(float(np.median([r['position_spread'] for r in multi])),3) if multi else None,
           zero_count_bgs=sum(1 for r in F if r['count']==0),mean_annual_count=round(float(np.mean([r['count']/r['years'] for r in F])),2))
    # by letter: median actual rate
    bands={}
    for L in ['A+','A','A-','B+','B','B-','C+','C','C-','D+','D','D-','F']:
        rr=[r['rate_per_1000'] for r in F if r['letter']==L]
        if rr: bands[L]=dict(n=len(rr),median_rate=round(float(np.median(rr)),2),p25=round(float(np.percentile(rr,25)),2),p75=round(float(np.percentile(rr,75)),2))
    s['by_letter']=bands
    # deciles of position vs mean rate
    order=np.argsort(pos); dec=[]
    for k in range(5):
        idx=order[k*len(order)//5:(k+1)*len(order)//5]; dec.append(dict(position_range=[round(min(pos[i] for i in idx),3),round(max(pos[i] for i in idx),3)],mean_rate=round(float(np.mean([rate[i] for i in idx])),2),median_rate=round(float(np.median([rate[i] for i in idx])),2),n=len(idx)))
    s['position_quintiles']=dec
    summary[city]=s
json.dump(summary,open('summary.json','w'),indent=1)
print(json.dumps(summary,indent=1))
