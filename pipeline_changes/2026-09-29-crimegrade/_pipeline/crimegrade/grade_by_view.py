#!/usr/bin/env python3
"""Read a batch of ZIP-page screenshots taken tab by tab (one crime per tab, same map view).

Usage: grade_by_view.py <folder>   where <folder> holds the screenshots in x/ and a manifest.json
written by label_screenshots.py ({screenshot: {"zip", "type", "view"}}). Views are georeferenced
once (one fit per identical map view), then every tab is read for every address that lands on the
map: the photo-list addresses of crimegrade_robbery_green_2026-09-29.csv and every file-14 row whose
ZIP is one of the pages. Fits go to <folder>/fits/, readings to <folder>/samples_results.csv."""
import sys, os, json, csv, re, time, urllib.request, urllib.parse, collections
from multiprocessing import Pool
PIPE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(os.path.dirname(PIPE)); CACHE=os.path.join(PIPE,'cache')
sys.path.insert(0,PIPE)
import numpy as np
from georef import georeference, load_rgb, map_bounds
from colour_read import read_address, merc_y, block_groups_near
from grade_addresses import census_geocode
S=os.path.abspath(sys.argv[1]); IMG=os.path.join(S,'x')
man=json.load(open(os.path.join(S,'manifest.json')))
views=collections.defaultdict(list)
for f,m in man.items(): views[m['view']].append(f)
view_zip={v:man[fs[0]]['zip'] for v,fs in views.items()}

def clean(a):
    a=re.sub(r'\s+Unit\s+[^,]*','',a,flags=re.I)
    a=re.sub(r'^(\d+)\s*(?:-|&|/|and)\s*\d+\s*','\\1 ',a,flags=re.I)
    a=re.sub(r'^(\d+)\s*/\s*(\d+)','\\1',a)
    a=re.sub(r'^(\d+)\.5\s','\\1 ',a)
    a=re.sub(r'\b(\w+) \1\b',r'\1',a)
    return re.sub(r'\s+',' ',a).strip()

def addresses():
    rows={}
    # the 15 photo-list addresses, with the block groups already validated on 2026-09-29
    for r in csv.DictReader(open(os.path.join(ROOT,'crimegrade_robbery_green_2026-09-29.csv'),encoding='utf-8-sig')):
        rows[r['id']]={'id':r['id'],'address':r['address'],'lat':float(r['lat']),'lon':float(r['lon']),'bg':r['block_group'],'zip':r['address'][-5:],'source':'photo list'}
    # cleaned addresses used by the earlier runs
    cleaned={}
    for fn in ['addresses_ohio_robbery_2026-09-29.csv','addresses_vawv_robbery_2026-09-29.csv','addresses_green_robbery_2026-09-29.csv']:
        for r in csv.DictReader(open(os.path.join(ROOT,fn),encoding='utf-8-sig')):
            if r.get('file14_address'): cleaned[r['file14_address'].strip()]=r['address'].strip()
    f14=os.path.join(ROOT,'..','2026-09-29','14 Live status and ranking of the 42 tracked candidates (2026-09-11).csv')
    have={r['address'] for r in rows.values()}
    n=0
    for i,r in enumerate(csv.DictReader(open(f14,encoding='utf-8-sig'))):
        a14=r['address'].strip(); z=a14[-5:]
        if z not in set(view_zip.values()): continue
        a=cleaned.get(a14) or clean(a14)
        if a in have: continue
        g=census_geocode(a,CACHE)
        if not g: print('no geocode:',a14,'->',a,flush=True); continue
        n+=1; rid='f%03d'%(i+1)
        rows[rid]={'id':rid,'address':a,'file14':a14,'lat':g['lat'],'lon':g['lon'],'bg':g['block'][:12],'zip':z,'source':'file 14'}
    print('addresses:',len(rows),'(file 14 extra:',n,')',flush=True)
    return rows

def nominatim_zip(z):
    """ZIP centroid from Nominatim, cached in the pipeline cache; retried with backoff on 429 (one request per second is the service's limit)."""
    cp=os.path.join(CACHE,'zipref_%s.json'%z)
    if os.path.exists(cp): return tuple(json.load(open(cp)))
    q=urllib.parse.urlencode({'postalcode':z,'country':'US','format':'json'})
    req=urllib.request.Request('https://nominatim.openstreetmap.org/search?'+q,headers={'User-Agent':'crimegrade-pipeline/1.0 (najumobi@gmail.com)'})
    for i in range(6):
        try:
            j=json.loads(urllib.request.urlopen(req,timeout=30).read()); ref=(float(j[0]['lat']),float(j[0]['lon']))
            json.dump(ref,open(cp,'w')); time.sleep(1.5); return ref
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(8*(i+1)); continue
            raise
    raise RuntimeError('nominatim kept returning 429 for '+z)

def fit_zip(args):
    z,vlist,ref=args
    out={}
    for v in vlist:
        ex=os.path.join(IMG,views[v][0])
        fp=os.path.join(S,'fits','view_%02d.json'%v)
        if os.path.exists(fp): out[v]=json.load(open(fp)); continue
        t=time.time()
        try:
            fit=georeference(ex,ref[0],ref[1],CACHE)
        except Exception as e:
            print('FIT FAIL',z,v,e,flush=True); continue
        fit['ref']=ref; fit['exemplar']=views[v][0]; fit['seconds']=round(time.time()-t)
        json.dump(fit,open(fp,'w')); out[v]=fit
        print('fit zip %s view %d zoom %.3f score %.3f (%ds)'%(z,v,fit['zoom'],fit['score'],fit['seconds']),flush=True)
    return out

def bbox_inside(geom,proj,W,H,top,left,right,bottom):
    xs=[];ys=[]
    rings=geom.get('rings') or geom.get('coordinates')
    def walk(o):
        if isinstance(o[0],(int,float)): xs.append(o[0]); ys.append(o[1])
        else:
            for p in o: walk(p)
    walk(rings)
    px=[proj(x,y) for x,y in zip(xs,ys)]
    x0=min(p[0] for p in px); x1=max(p[0] for p in px); y0=min(p[1] for p in px); y1=max(p[1] for p in px)
    area=max(x1-x0,1)*max(y1-y0,1)
    ix=max(0,min(x1,right)-max(x0,left)); iy=max(0,min(y1,bottom)-max(y0,top))
    return ix*iy/area

def main():
    os.makedirs(os.path.join(S,'fits'),exist_ok=True)
    rows=addresses(); json.dump(rows,open(os.path.join(S,'addresses.json'),'w'),indent=0)
    # reference point per zip
    byzip=collections.defaultdict(list)
    for v,z in view_zip.items(): byzip[z].append(v)
    jobs=[]
    for z,vl in sorted(byzip.items()):
        cands=[r for r in rows.values() if r['zip']==z]
        cands.sort(key=lambda r:(r['source']!='photo list',r['id']))
        if cands: ref=(cands[0]['lat'],cands[0]['lon']); print('zip',z,'ref',cands[0]['address'],flush=True)
        else: ref=nominatim_zip(z); print('zip',z,'ref nominatim',ref,flush=True); time.sleep(1.2)
        jobs.append((z,sorted(vl),ref))
    fits={}
    with Pool(3) as pool:
        for out in pool.imap_unordered(fit_zip,jobs): fits.update(out)
    print('fits done:',len(fits),'of',len(views),flush=True)
    # reads
    res=[]
    for v in sorted(views):
        if v not in fits: continue
        fit=fits[v]; z=view_zip[v]
        for f in sorted(views[v]):
            A=load_rgb(os.path.join(IMG,f)); H,W,_=A.shape
            top,left,right=map_bounds(A); bottom=H-48
            s,tx,ty=fit['s'],fit['tx'],fit['ty']; proj=lambda lo,la:(s*lo+tx,-s*merc_y(la)+ty)
            for r in rows.values():
                x,y=proj(r['lon'],r['lat'])
                if not (left+4<x<right-4 and top+4<y<bottom-4): continue
                rr=read_address(A,fit,r['lat'],r['lon'],r['bg'],CACHE)
                rec={'id':r['id'],'address':r['address'],'source':r['source'],'zip_page':z,'view':v,'type':man[f]['type'],'image':f,
                     'zoom':fit['zoom'],'fit_score':fit['score']}
                if 'error' in rr: rec['note']=rr['error']
                else:
                    feats=block_groups_near(r['lat'],r['lon'],CACHE); own=[q for q in feats if q['properties']['GEOID']==r['bg']][0]
                    frac=bbox_inside(own['geometry'],proj,W,H,top,left,right,bottom)
                    rec.update(block_group=rr['block_group'],grade=rr['grade'],position=rr['position'],position_iqr='%s-%s'%tuple(rr['position_iqr']),
                               at_address_position=rr['at_address_position'],pixels=rr['pixels_on_ramp'],edge_distance_m=rr['edge_distance_m'],
                               neighbours='; '.join('%s %s at %d m'%(n['block_group'],n['grade'],n['distance_m']) for n in rr['neighbours_within_60m']),
                               bg_inside=round(frac,2),note='; '.join([n for n in [rr['line_note'],'block group partly off the map' if frac<0.6 else ''] if n]))
                res.append(rec)
                print('%s %-42s %-18s %s %s'%(r['id'],r['address'][:42],man[f]['type'],rec.get('grade','-'),rec.get('position','-')),flush=True)
    cols=['id','address','source','zip_page','view','type','image','zoom','fit_score','block_group','grade','position','position_iqr','at_address_position','pixels','edge_distance_m','neighbours','bg_inside','note']
    with open(os.path.join(S,'samples_results.csv'),'w',newline='') as fh:
        w=csv.DictWriter(fh,fieldnames=cols); w.writeheader()
        for rec in res: w.writerow({c:rec.get(c,'') for c in cols})
    print('DONE',len(res),'readings',flush=True)
if __name__=='__main__': main()
