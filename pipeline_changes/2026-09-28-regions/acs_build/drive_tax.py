import json, urllib.request, os, time, statistics
S=os.path.dirname(os.path.abspath(__file__))+'/..'
geo={}
for line in open(S+'/camp/_pipeline/model/US.txt',encoding='utf-8'):
    p=line.rstrip('\n').split('\t')
    if len(p)>10: geo[p[1]]=(p[2],p[4],float(p[9]),float(p[10]))
WB=(-76.7075,37.2707)  # Williamsburg VA (lon,lat)
out={}
for reg in ['phila','pitt','ohio']:
    for e in json.load(open(f'{S}/regions/sweep_zips_{reg}.json')):
        z=e['zip']; g=geo.get(z)
        if not g or z in out: continue
        url=f"https://router.project-osrm.org/route/v1/driving/{WB[0]},{WB[1]};{g[3]},{g[2]}?overview=false"
        for t in range(4):
            try:
                d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'najum-research/1.0'}),timeout=60))
                out[z]={'place':g[0],'st':g[1],'osrm_h':round(d['routes'][0]['duration']/3600,2),'google_eq_h':round(d['routes'][0]['duration']/3600/1.15,2)}; break
            except Exception as ex:
                time.sleep(1.5)
        time.sleep(0.4)
json.dump(out,open(S+'/regions/drive_hours_by_zip.json','w'),indent=1)
# county owner tax rates for the new states
key=os.environ['CENSUS_API_KEY']; tax={}
for st in ['42','39','34','10','24','54','36','21']:
    for t in range(15):
        try:
            r=urllib.request.urlopen(urllib.request.Request(f"https://api.census.gov/data/2024/acs/acs5?get=NAME,B25103_001E,B25077_001E&for=county:*&in=state:{st}&key={key}",headers={'User-Agent':'curl/8'}),timeout=60); b=r.read().decode()
            if b.startswith('['):
                for row in json.loads(b)[1:]:
                    T=float(row[1]) if float(row[1])>0 else None; V=float(row[2]) if float(row[2])>0 else None
                    tax[row[3]+row[4]]={'name':row[0],'T':T,'V':V,'rate':round(T/V,5) if T and V else None}
                break
        except Exception: pass
        time.sleep(2)
json.dump(tax,open(S+'/regions/county_owner_tax_2020-24.json','w'),indent=1)
print('drive',len(out),'tax',len(tax))
