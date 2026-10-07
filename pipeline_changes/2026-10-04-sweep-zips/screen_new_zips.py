# For each added sweep ZIP: block groups whose centroid lies in the 2020 ZCTA (TIGERweb), how many the crime table covers, and the Robbery-F share.
import json, urllib.request, urllib.parse, time, sys, os
S=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bg=json.load(open(f'{S}/mirror8/crime_bg.json'))['bg']; F=12/13
ADDED={"ncva":["23602","27330","27406"],"phila":["08012","08053","08079","08107","08332","19132","19320","19606"],"pitt":["25303","25309","25314","44432","44505"],
       "ohio":["43078","43537","43551","43567","43609","43611","45309","45322","45342","45356","45373","45377","45403","45410","45419","45426","45440"]}
UA={"User-Agent":"Mozilla/5.0"}
def get(url, q):
    for i in range(4):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url+"?"+urllib.parse.urlencode(q), headers=UA), timeout=90))
        except Exception as e: err=e; time.sleep(3)
    raise err
T="https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
def layer_id(service, must):
    info=get(T+service+"/MapServer", {"f":"json"})
    for l in info["layers"]:
        if all(m.lower() in l["name"].lower() for m in must): return l["id"], l["name"]
    raise SystemExit("no layer "+str(must)+" in "+str([l["name"] for l in info["layers"]]))
zl, zn = layer_id("PUMA_TAD_TAZ_UGA_ZCTA", ["zip code tabulation"]); bl, bn = 11, "Census Block Groups (Census 2020, with POP100)"
print("layers:", zl, zn, "|", bl, bn, flush=True)
zf=get(T+f"PUMA_TAD_TAZ_UGA_ZCTA/MapServer/{zl}", {"f":"json"}); zfield=[f["name"] for f in zf["fields"] if f["name"].upper() in ("ZCTA5","ZCTA5CE20","ZCTA5CE10","BASENAME")][0]
def inside(pt, rings):
    x,y=pt; ins=False
    for ring in rings:
        n=len(ring)
        for i in range(n):
            x1,y1=ring[i][0],ring[i][1]; x2,y2=ring[(i+1)%n][0],ring[(i+1)%n][1]
            if (y1>y)!=(y2>y) and x < (x2-x1)*(y-y1)/((y2-y1) or 1e-12)+x1: ins=not ins
    return ins
out={}
for region, zips in ADDED.items():
    for z in zips:
        zq=get(T+f"PUMA_TAD_TAZ_UGA_ZCTA/MapServer/{zl}/query", {"where":f"{zfield}='{z}'","outFields":zfield,"returnGeometry":"true","outSR":"4326","geometryPrecision":"5","f":"geojson"})
        feats=zq.get("features") or []
        if not feats: out[z]={"region":region,"error":"no ZCTA"}; print(z,"no ZCTA",flush=True); continue
        geom=feats[0]["geometry"]; polys=[geom["coordinates"]] if geom["type"]=="Polygon" else geom["coordinates"]
        xs=[p[0] for poly in polys for ring in poly for p in ring]; ys=[p[1] for poly in polys for ring in poly for p in ring]
        bq=get(T+f"Tracts_Blocks/MapServer/{bl}/query", {"geometry":f"{min(xs)},{min(ys)},{max(xs)},{max(ys)}","geometryType":"esriGeometryEnvelope","inSR":"4326","spatialRel":"esriSpatialRelIntersects","outFields":"GEOID,POP100,CENTLAT,CENTLON","returnGeometry":"false","f":"json"})
        rows=[]
        for ft in bq.get("features") or []:
            a=ft["attributes"]; g=a.get("GEOID"); pop=int(a.get("POP100") or 0)
            try: lat=float(a["CENTLAT"]); lon=float(a["CENTLON"])
            except Exception: continue
            if pop<150 or not any(inside((lon,lat),[poly[0]]) and not any(inside((lon,lat),[hole]) for hole in poly[1:]) for poly in polys): continue
            t=bg.get(g); rows.append({"g":g,"pop":pop,"R":t.get("R") if t else None,"B":t.get("B") if t else None,"V":t.get("V") if t else None,"M":t.get("M") if t else None,"D":t.get("D") if t else None})
        n=len(rows); cov=[r for r in rows if r["R"] is not None]; pop=sum(r["pop"] for r in rows); popc=sum(r["pop"] for r in cov)
        rf=[r for r in cov if r["R"]>=F]; nv=[r for r in rf if (r["B"] or 0)>=F or (r["V"] or 0)>=F]
        out[z]={"region":region,"bgs":n,"pop":pop,"covered":len(cov),"covered_pop_share":round(popc/pop,2) if pop else None,
                "robberyF_count_share":round(len(rf)/len(cov),2) if cov else None,"robberyF_pop_share":round(sum(r["pop"] for r in rf)/popc,2) if popc else None,
                "ncva_rule_pop_share":round(sum(r["pop"] for r in nv)/popc,2) if popc else None,
                "flags_pop_share":{k: round(sum(r["pop"] for r in cov if (r[k] or 0)>=F)/popc,2) for k in ("M","D")} if popc else None}
        print(z, json.dumps(out[z]), flush=True)
json.dump(out, open(f'{S}/newzips/screen.json','w'), indent=1); print("done", flush=True)
