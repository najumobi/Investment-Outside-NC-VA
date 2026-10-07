import urllib.request, json, os, time, sys
key=os.environ['CENSUS_API_KEY']; base='https://api.census.gov/data/2024/acs/acs5'
G1=['B01003_001E','B25003_001E','B25003_003E','B25004_002E','B25024_001E','B25024_004E','B25024_005E','B25032_015E','B19013_001E','B19013_001M','B25064_001E','B25064_001M','B25077_001E','B25077_001M','B25070_001E','B25070_007E','B25070_008E','B25070_009E','B25070_010E','B25070_011E','B17001_001E','B17001_002E','B23025_001E','B23025_002E','B23025_003E','B23025_004E','B22010_001E','B22010_002E']
G2=['B08303_001E','B08303_002E','B08303_003E','B08303_004E','B08303_005E','B08303_011E','B08303_012E','B08303_013E','B25034_001E','B25034_002E','B25034_003E','B25034_004E','B25034_005E','B25034_006E','B25034_007E','B25034_008E','B25034_009E','B25034_010E','B25034_011E','B15003_001E','B15003_021E','B15003_022E','B15003_023E','B15003_024E','B15003_025E','B25038_010E','B25038_011E','B25038_012E','B25038_013E','B25038_014E','B25038_015E','B14007_001E','B14007_017E','B14007_018E']
def get(url, tries=25):
    for t in range(tries):
        try:
            r=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'curl/8'}),timeout=120); body=r.read().decode()
            if r.geturl().endswith('.html') or not body.startswith('['): time.sleep(2); continue
            return json.loads(body), t+1
        except Exception as e: time.sleep(2)
    return None, tries
log=open(sys.argv[1]+'/pull.log','a')
for st in ['37','51','42','39','34','10','24','54','36','21']:
    out={}
    for gi,G in enumerate([G1,G2]):
        fn=f"{sys.argv[1]}/tract_{st}_g{gi+1}.json"
        if os.path.exists(fn): log.write(f"{st} g{gi+1} cached\n"); continue
        data,n=get(f"{base}?get=NAME,{','.join(G)}&for=tract:*&in=state:{st}&key={key}")
        if data: json.dump(data,open(fn,'w')); log.write(f"{st} g{gi+1} rows {len(data)-1} tries {n}\n")
        else: log.write(f"{st} g{gi+1} FAILED after {n}\n")
        log.flush()
log.write('DONE\n'); log.close()
