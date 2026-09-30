#!/usr/bin/env python3
"""Read every census block group under every fitted map view and write the block-group crime table.

Usage: build_crime_bg.py <out.json> <batch folder> [<batch folder> ...]
Each batch folder holds x/ (screenshots), manifest.json ({screenshot: {zip, type, view}}) and fits/view_NN.json
written by grade_by_view.py. For each view the 2020 block groups intersecting the map are fetched from
TIGERweb (cached in cache/bg_view_<md5>.json) and, on every tab image of that view, each block group's
median legend position is read (block groups with fewer than 150 residents, less than 60% of their box
on the map or fewer than 300 pixels on the legend ramp are skipped). Output: {GEOID: {"pop": n, "reads":
{type: [{"position", "grade", "zip_page", "batch", "view", "pixels"}...]}, "types": {type: mean position}}}
and a flat CSV beside it. An address is looked up by its 12-digit block group from the Census geocoder.
"""
import sys, os, json, csv, hashlib, collections, urllib.parse, urllib.request
import numpy as np
PIPE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(PIPE,'cache')
sys.path.insert(0,PIPE)
from georef import load_rgb, map_bounds
from colour_read import ramp_positions, _mask, merc_y, grade_equal_bands
TIGER='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Tracts_Blocks/MapServer/11/query'

def fetch_bgs(bbox):
    key=os.path.join(CACHE,'bg_view_'+hashlib.md5(json.dumps([round(v,4) for v in bbox]).encode()).hexdigest()[:12]+'.json')
    if os.path.exists(key): return json.load(open(key))
    feats=[]; offset=0
    while True:
        q={'geometry':','.join('%.6f'%v for v in bbox),'geometryType':'esriGeometryEnvelope','inSR':'4326','spatialRel':'esriSpatialRelIntersects',
           'outFields':'GEOID,POP100,HU100','returnGeometry':'true','outSR':'4326','f':'geojson','resultOffset':str(offset),'resultRecordCount':'1000'}
        req=urllib.request.Request(TIGER+'?'+urllib.parse.urlencode(q),headers={'User-Agent':'crimegrade-pipeline/1.0'})
        j=json.loads(urllib.request.urlopen(req,timeout=120).read())
        if 'error' in j: raise RuntimeError(str(j['error'])[:200])
        feats+=j.get('features',[])
        if not (j.get('exceededTransferLimit') or (j.get('properties') or {}).get('exceededTransferLimit')): break
        offset+=len(j.get('features',[]))
    json.dump(feats,open(key,'w')); return feats

def bbox_inside(geom,proj,top,left,right,bottom):
    xs=[];ys=[]
    polys=[geom['coordinates']] if geom['type']=='Polygon' else geom['coordinates']
    for poly in polys:
        for x,y in poly[0]: px,py=proj(x,y); xs.append(px); ys.append(py)
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys); area=max(x1-x0,1)*max(y1-y0,1)
    ix=max(0,min(x1,right)-max(x0,left)); iy=max(0,min(y1,bottom)-max(y0,top)); return ix*iy/area

def main():
    out_path=sys.argv[1]; table=json.load(open(out_path)) if os.path.exists(out_path) else {}
    for folder in sys.argv[2:]:
        folder=os.path.abspath(folder); batch=os.path.basename(folder)
        man=json.load(open(os.path.join(folder,'manifest.json')))
        views=collections.defaultdict(list)
        for f,m in man.items(): views[m['view']].append(f)
        for v,files in sorted(views.items()):
            fp=os.path.join(folder,'fits','view_%02d.json'%v)
            if not os.path.exists(fp): print('no fit for view',v,'in',batch); continue
            fit=json.load(open(fp)); s,tx,ty=fit['s'],fit['tx'],fit['ty']
            proj=lambda lo,la:(s*lo+tx,-s*merc_y(la)+ty)
            A0=load_rgb(os.path.join(folder,'x',files[0])); H,W,_=A0.shape; top,left,right=map_bounds(A0); bottom=H-48
            import math
            def inv(px,py):
                lon=(px-tx)/s; my=(ty-py)/s; lat=math.degrees(2*math.atan(math.exp(math.radians(my)))-math.pi/2); return lon,lat
            lon0,lat1=inv(left,top); lon1,lat0=inv(right,bottom)
            feats=fetch_bgs([lon0,lat0,lon1,lat1])
            keep=np.ones((H,W),bool)
            for x0,y0,x1,y1 in fit.get('exclusions',[]): keep[y0:y1,x0:x1]=False
            keep[:top,:]=False; keep[bottom:,:]=False; keep[:,:left]=False; keep[:,right:]=False
            imgs={f:load_rgb(os.path.join(folder,'x',f)) for f in files}
            n=0
            for ft in feats:
                pr=ft['properties']; gid=pr['GEOID']; pop=pr.get('POP100') or 0
                if pop<150 or not ft.get('geometry'): continue
                if bbox_inside(ft['geometry'],proj,top,left,right,bottom)<0.6: continue
                m=_mask(ft['geometry'],proj,W,H,2)&keep
                if m.sum()<300: continue
                rec=table.setdefault(gid,{'pop':pop,'reads':{}})
                for f in files:
                    P=ramp_positions(imgs[f][m])
                    if len(P)<300: continue
                    pos=float(np.median(P)); t=man[f]['type']
                    rec['reads'].setdefault(t,[]).append({'position':round(pos,3),'grade':grade_equal_bands(pos),'zip_page':man[f]['zip'],'batch':batch,'view':v,'pixels':int(len(P))})
                n+=1
            print('%s view %02d zip %s: %d block groups x %d tabs'%(batch,v,man[files[0]]['zip'],n,len(files)),flush=True)
    for gid,rec in table.items():
        rec['types']={t:round(float(np.mean([r['position'] for r in rs])),3) for t,rs in rec['reads'].items()}
    json.dump(table,open(out_path,'w'))
    types=sorted({t for rec in table.values() for t in rec['types']})
    with open(out_path.replace('.json','.csv'),'w',newline='') as fh:
        w=csv.writer(fh); w.writerow(['block_group','pop']+[t+'_pos' for t in types]+[t+'_grade' for t in types]+['pages'])
        for gid in sorted(table):
            rec=table[gid]; w.writerow([gid,rec['pop']]+[rec['types'].get(t,'') for t in types]+[grade_equal_bands(rec['types'][t]) if t in rec['types'] else '' for t in types]+[';'.join(sorted({r['zip_page'] for rs in rec['reads'].values() for r in rs}))])
    print('block groups in table:',len(table))
if __name__=='__main__': main()
