# Duplex-sweep parsers, saved 2026-09-11 from the Composio remote workbench (session "noon").
# Re-exec this file in a fresh sandbox to rebuild the parsing state. Inputs are the
# /mnt/files/mex/<name>.json files written by COMPOSIO_MULTI_EXECUTE_TOOL with
# sync_response_to_workbench=true (20 BRIGHTDATA_WEB_UNLOCKER calls per file).
import re, json, collections
zipre = re.compile(r'/zipcode/(\d{5})/|-(\d{5})/duplex/')
HARD = 532643
fields = ['page_zip', 'address', 'price', 'beds', 'baths', 'sqft', 'built', 'listed_days', 'flags', 'units_text', 'package', 'land', 'rent_text', 'desc', 'source', 'url', 'zurl']
STATES = 'NC|VA|PA|OH|NJ|DE|MD|WV|NY|KY'   # 2026-09-28: the Tuesday-Thursday regions; the Redfin card and detail regexes were NC|VA only
RFC = re.compile(r'\[([^\]\n]+, (?:' + STATES + r') \d{5})\]\((/(?:' + STATES + r')/[^)\s]*/home/[^)\s]+)\)')
ZADDR = re.compile(r'\[\s*\n\s*(?P<addr>[^\n\]]+?, [A-Z]{2} \d{5})\s*\n\s*\]\((?P<link>https://www\.zillow\.com/homedetails/[^)\s]+)\)')
LABELS = '(Multi-family home for sale|New construction|House for sale|Condo for sale|Townhouse for sale|Lot / Land for sale|Apartment for sale|Home for sale|Auction|Foreclosure|Coming soon|Manufactured home for sale)'

def load2(path):
    fd=json.load(open(path)); return [((r['response'].get('data') or {}).get('url') or '', (r['response'].get('data') or {}).get('content') or '', ((r['response'].get('data') or {}).get('headers') or {}).get('x-brd-status-code')) for r in fd['results']]

def parse_redfin_full(url, c):
    pz = re.search(r'/zipcode/(\d{5})', url).group(1)
    main = c.split('Nearby homes that match')[0]
    out=[]; seen=set()
    for m in RFC.finditer(main):
        link='https://www.redfin.com'+m.group(2)
        if link in seen: continue
        seen.add(link)
        back = main[max(0, m.start()-1800):m.start()]; cut = back.rfind('/home/')
        if cut>0: back = back[cut:]
        fwd = main[m.end():m.end()+300]
        prices = re.findall(r'\$([\d,]{5,})(?![^\n]*(?:rent|month|annual|income|/mo))', back)
        bb = re.findall(r'([\d.—]+) beds?\s*([\d.—]+) baths?\s*([\d,—]+) sq ft', back)
        dm = re.findall(r'Homes for Sale\s*\n\s*\n?\s*(.{20,1200}?)\n', back, re.S)
        desc = re.sub(r'\s+',' ', dm[-1]) if dm else ''
        built = re.search(r'Built (\d{4})', back+fwd); listed = re.search(r'Listed (\d+) days', back+fwd)
        flags=[l for pat,l in (('NEW \\d+ HRS AGO|NEW TODAY|NEW','new'),('PRICE DROP','price drop'),('OPEN (?:SAT|SUN)','open house')) if re.search(pat, back[-400:]+fwd)]
        text=(desc+' '+fwd).lower(); units=None
        if re.search(r'\b(duplex|two[- ]unit|2[- ]unit|2 units)\b', text): units=2
        if re.search(r'\b(triplex|three[- ]unit|3[- ]unit|3 units)\b', text): units=3
        if re.search(r'\b(fourplex|quadplex|quad|four[- ]unit|4[- ]unit|4 units)\b', text): units=4
        big = re.search(r'\b(\d{1,3})[- ](?:unit|units|active leases|leases|apartments)\b', text)
        if big and int(big.group(1))>4: units=int(big.group(1))
        pkg = bool(re.search(r'\b(four|4|three|3) duplexes\b', text))
        sqft = bb[-1][2].replace(',','') if bb else ''
        land = bool(re.search(r'\b(lot|land|acres?)\b', text)) and not units and (not sqft or sqft=='—')
        rent_m = re.search(r'\$([\d,]{3,})\s*(?:in )?(?:per month|/mo|monthly|a month|month)', text); rent_a = re.search(r'\$([\d,]{4,})\s*(?:in )?(?:gross )?annual', text)
        rent = int(rent_m.group(1).replace(',','')) if rent_m else (round(int(rent_a.group(1).replace(',',''))/12) if rent_a else '')
        addr = re.sub(r'\s+',' ', m.group(1)).strip()
        out.append({'page_zip':pz,'address':addr,'zip':addr[-5:],'price':int(prices[-1].replace(',','')) if prices else '','beds':bb[-1][0] if bb else '','baths':bb[-1][1] if bb else '','sqft':sqft,'built':built.group(1) if built else '','listed_days':listed.group(1) if listed else '','flags':'; '.join(flags),'units_text':units or '','package':pkg,'land':land,'rent_text':rent,'desc':desc[:220],'source':'redfin','url':link})
    return out

def parse_zillow(content, url):
    mz = re.search(r'(\d{5}) Duplex & Triplex Homes For Sale - ([\d,]+) Homes', content)
    zipc = mz.group(1) if mz else None; title_total = int(mz.group(2).replace(',','')) if mz else None
    mr = re.search(r'^##\s*([\d,]+)\s*results?', content, re.M)
    n_in = int(mr.group(1).replace(',','')) if mr else None
    end = content.find('End of matching results'); split_at = end if end>=0 else len(content)
    rows=[]; seen=set(); prev_end=0
    for am in ZADDR.finditer(content):
        link=am.group('link')
        if link in seen: continue
        seen.add(link)
        win = content[max(prev_end, am.start()-1500):am.start()]; prev_end = am.end()
        after = content[am.end():am.end()+400]
        prices = re.findall(r'\$([\d,]{5,})', win)
        beds = re.findall(r'\*\*([^*\n]+)\*\*\s*bds', win); baths = re.findall(r'\*\*([^*\n]+)\*\*\s*ba\b', win); sqft = re.findall(r'\*\*([^*\n]+)\*\*\s*sqft', win)
        labels = re.findall(LABELS, win)
        tag = re.search(r'More\s*\n\s*\n\s*([^\n]+?)\s*\n\s*\n\s*Save', after)
        addr = am.group('addr').strip(); z = addr[-5:]
        rows.append({'page_zip':zipc,'section':'in' if am.start()<split_at else 'near','address':addr,'zip':z,'price':int(prices[-1].replace(',','')) if prices else None,'beds':beds[-1].replace('\\','') if beds else None,'baths':baths[-1].replace('\\','') if baths else None,'sqft':sqft[-1].replace('\\','') if sqft else None,'label':labels[-1] if labels else '','tag':tag.group(1) if tag else '','link':link})
    return {'zip':zipc,'title_total':title_total,'n_in':n_in,'rows':rows,'url':url,'len':len(content)}

def key(a):
    s=a.split(',')[0].lower(); s=re.sub(r'\b(street)\b','st',s); s=re.sub(r'\b(avenue)\b','ave',s); s=re.sub(r'\b(road)\b','rd',s); s=re.sub(r'\b(drive)\b','dr',s); s=re.sub(r'\b(boulevard)\b','blvd',s); s=re.sub(r'\b(court)\b','ct',s); s=re.sub(r'\b(lane)\b','ln',s); s=re.sub(r'\b(place)\b','pl',s); s=re.sub(r'\b(circle)\b','cir',s)
    # 2026-09-28: the portals spell the same street differently (Zillow "749 Mount Airy St" vs Redfin "749 Mt Airy St" slipped through as a new listing on 9/21), so fold the common variants before matching
    s=re.sub(r'\b(mount)\b','mt',s); s=re.sub(r'\b(fort)\b','ft',s); s=re.sub(r'\b(saint)\b','st',s); s=re.sub(r'\b(terrace)\b','ter',s); s=re.sub(r'\b(parkway)\b','pkwy',s); s=re.sub(r'\b(highway)\b','hwy',s); s=re.sub(r'\b(trail)\b','trl',s); s=re.sub(r'\b(square)\b','sq',s)
    s=re.sub(r'\b(north ?east)\b','ne',s); s=re.sub(r'\b(north ?west)\b','nw',s); s=re.sub(r'\b(south ?east)\b','se',s); s=re.sub(r'\b(south ?west)\b','sw',s); s=re.sub(r'\b(north)\b','n',s); s=re.sub(r'\b(south)\b','s',s); s=re.sub(r'\b(east)\b','e',s); s=re.sub(r'\b(west)\b','w',s)
    s=re.sub(r'\bunit .*$|\bapt .*$|#.*$','',s); s=re.sub(r'[^a-z0-9 ]','',s); s=re.sub(r'\s+',' ',s).strip()
    return re.sub(r'\b(\w+)( \1\b)+','\\1',s)   # 2026-09-28: Zillow repeats the suffix ("Main Street St", "Arthur Ave Ave") -> one token, so the Redfin row matches

def grab(c, pat, n=3, w=80, flags=re.I):
    out=[]
    for m in re.finditer(pat, c, flags):
        s=max(0,m.start()-w); e=min(len(c), m.end()+w)
        out.append(re.sub(r'\s+',' ', c[s:e]))
        if len(out)>=n: break
    return out

def num(x):
    try: return float(str(x).replace('$','').replace(',',''))
    except: return None

def make_round(zips):
    """Per-round merge state: returns (merged, counts, bad, add_pages). merged is keyed by key(address)+'|'+zip."""
    merged = {}; bad = []; counts = {z: {'redfin': None, 'zillow': None, 'z_title': None} for z in zips}
    def add_pages(pages):
        for url,c,brd in pages:
            m = zipre.search(url); z = m.group(1) or m.group(2)
            if 'redfin.com' in url:
                if not c or len(c) < 2000 or 'Page Not Found' in c[:200]:
                    bad.append((url,brd,len(c or ''))); continue
                rows = [r for r in parse_redfin_full(url,c) if r.get('zip') == z]
                counts[z]['redfin'] = len(rows)
                for r in rows:
                    k = key(r['address'])+'|'+z
                    if k in merged:
                        merged[k]['source'] = 'both'
                        for f,v in r.items():
                            if v and v != '—' and not merged[k].get(f): merged[k][f] = v
                    else:
                        r = dict(r); r['source'] = 'redfin'; merged[k] = r
            else:
                if not c or 'Duplex & Triplex Homes' not in c[:400]:
                    bad.append((url,brd,len(c or ''))); continue   # Zillow 404 (bad slug) or 502 (retry on another account)
                if counts[z]['zillow'] is not None: continue
                d = parse_zillow(c,url)
                rows = [r for r in d['rows'] if r.get('zip') == z]   # drops the nearby-ZIP cards Zillow pads zero pages with
                counts[z]['zillow'] = len(rows); counts[z]['z_title'] = d.get('title_total')
                for r in rows:
                    k = key(r['address'])+'|'+z
                    rr = {'page_zip': z, 'address': r['address'], 'zip': z, 'price': r.get('price'), 'beds': r.get('beds'), 'baths': r.get('baths'), 'sqft': r.get('sqft'), 'built': '', 'listed_days': r.get('tag',''), 'flags': r.get('label',''), 'units_text': '', 'package': False, 'land': ('lot' in (r.get('label') or '').lower() or 'land' in (r.get('label') or '').lower()), 'rent_text': '', 'desc': '', 'url': r.get('link','')}
                    if k in merged:
                        merged[k]['source'] = 'both'
                        merged[k]['zurl'] = rr['url']; merged[k]['zlabel'] = rr['flags']
                        for f in ('price','beds','baths','sqft'):
                            if rr.get(f) and rr[f] not in ('--','—') and (not merged[k].get(f) or merged[k].get(f) in ('--','—')): merged[k][f] = rr[f]
                    else:
                        rr['source'] = 'zillow'; merged[k] = rr
    return merged, counts, bad, add_pages

def flat(c): return re.sub(r'\s+', ' ', re.sub(r'!\[[^\]]*\]\([^)]*\)', '', c or ''))

def parse_detail(url, c, headers=None):
    """Facts from one Redfin detail page (markdown). Added 2026-09-14 for the weekly tracked-row refresh and shortlist details.
    status: ACTIVE / PENDING / CONTINGENT / SOLD / OFF MARKET / COMING SOON / UNKNOWN; page_address is compared with the tracked address by the caller."""
    f = flat(c); h = headers or {}
    d = {'url': url, 'ok': bool(c) and len(c) > 2000 and 'Page Not Found' not in c[:300], 'redirected_to': h.get('x-unblocker-redirected-to') or '', 'chars': len(c or '')}
    m = re.search(r'# ([^#]{5,90}?, (?:' + STATES + r') \d{5})', f); d['page_address'] = m.group(1).strip() if m else ''
    top = f[:6000]
    pill = re.search(r'\b(SOLD [A-Z]{3} \d{1,2}, \d{4}|PENDING|CONTINGENT|ACTIVE UNDER CONTRACT|OFF MARKET|COMING SOON)\b', top)
    if pill:
        p = pill.group(1); d['status'] = 'SOLD' if p.startswith('SOLD') else p; d['status_date'] = p[5:] if p.startswith('SOLD') else ''
    elif re.search(r'Home price \$[\d,]+', f) and re.search(r'days?\*{0,2} on Redfin', f): d['status'] = 'ACTIVE'; d['status_date'] = ''
    else: d['status'] = 'UNKNOWN'; d['status_date'] = ''
    m = re.search(r'Home price \$([\d,]+)', f); d['price'] = int(m.group(1).replace(',', '')) if m else None
    if d['price'] is None:
        m = re.search(r'Sold on [A-Za-z]{3} \d{4} \$([\d,]+)', f); d['price'] = int(m.group(1).replace(',', '')) if m else None
    m = re.search(r'\*{0,2}(\d+) days?\*{0,2} on Redfin', f); d['dom'] = int(m.group(1)) if m else None
    m = re.search(r'Date Event Price (.{0,400})', f)
    hist = m.group(1) if m else ''
    ev = re.findall(r'([A-Z][a-z]{2} \d{1,2}, \d{4}) (Listed|Sold|Price Changed|Pending|Contingent|Listing Removed|Delisted|Relisted)(?: \$([\d,]+))?', hist)
    d['history'] = '; '.join(f'{a} {b}' + (f' ${p}' if p else '') for a, b, p in ev[:6]); d['last_event'] = (' '.join(x for x in ev[0] if x)) if ev else ''
    # Redfin's markdown carries no status pill for pending/contingent listings; the newest history event is the signal
    if ev and d['status'] == 'ACTIVE' and ev[0][1] in ('Pending', 'Contingent'): d['status'] = ev[0][1].upper(); d['status_date'] = ev[0][0]
    if ev and d['status'] == 'UNKNOWN' and ev[0][1] in ('Listing Removed', 'Delisted'): d['status'] = 'OFF MARKET'; d['status_date'] = ev[0][0]
    m = re.search(r'(\d{4})Year Built|Year Built:? (\d{4})', f); d['built'] = int(m.group(1) or m.group(2)) if m else None
    m = re.search(r'Year Property tax Land \+ Additions Assessment\\?\*? (\d{4}) \$([\d,]+)', f); d['tax_year'] = int(m.group(1)) if m else None; d['tax_annual'] = int(m.group(2).replace(',', '')) if m else None
    m = re.search(r'(\d{1,2})/10 Flood Factor', f); d['flood'] = int(m.group(1)) if m else None
    m = re.search(r'(\d+) beds? ([\d.]+) ba • ([\d,]+) sq ft # ', f); d['beds'], d['baths'], d['sqft'] = (m.group(1), m.group(2), m.group(3).replace(',', '')) if m else ('', '', '')
    m = re.search(r'## About this home (.{20,1500}?) Show more', f); d['remarks'] = m.group(1).strip() if m else ''
    m = re.search(r'(https://ssl\.cdn-redfin\.com/photo/\d+/bigphoto/[^)\s"]+)', c or ''); d['photo'] = m.group(1) if m else ''
    m = re.search(r'Listed by ([^•]{2,60})•([^\n]{2,60}?) Listing updated', f); d['listed_by'] = (m.group(1).strip() + ' / ' + m.group(2).strip()) if m else ''
    m = re.search(r'MLS# ?([A-Z0-9\-]{5,15})|MLS #?([A-Z0-9\-]{5,15})', f); d['mls'] = (m.group(1) or m.group(2)) if m else ''
    m = re.search(r'Redfin Estimate(?: for [^$]{0,60})? \$([\d,]+)', f); d['redfin_estimate'] = int(m.group(1).replace(',', '')) if m else None
    m = re.search(r'Public record \* Zoning (.{0,120})', f); d['zoning_line'] = m.group(1) if m else ''
    m = re.search(r'Unit \d listed at \$([\d,]+)/month', f); d['unit_rent_text'] = m.group(0) if m else ''
    return d

def parse_zillow_detail(url, c, headers=None):
    """Facts from one Zillow homedetails page (markdown; ~4 KB pages, no status pill). Added 2026-09-14."""
    f = flat(c); h = headers or {}
    d = {'url': url, 'ok': bool(c) and len(c) > 2000, 'redirected_to': h.get('x-unblocker-redirected-to') or '', 'chars': len(c or ''), 'zillow': True, 'status_date': '',
         'flood': None, 'tax_annual': None, 'tax_year': None, 'listed_by': '', 'zoning_line': '', 'redfin_estimate': None, 'history': ''}
    m = re.search(r'\$([\d,]{5,}) # ([^#]{5,90}?, (?:' + STATES + r') \d{5}) (\d+) ?beds? ([\d.]+) ?baths? ([\d,\-]+) ?sqft', f)
    if m: d['price'] = int(m.group(1).replace(',', '')); d['page_address'] = m.group(2).strip(); d['beds'], d['baths'], d['sqft'] = m.group(3), m.group(4), m.group(5).replace(',', '')
    else:
        m = re.search(r'# ([^#]{5,90}?, (?:' + STATES + r') \d{5})', f); d['page_address'] = m.group(1).strip() if m else ''
        m = re.search(r'\$([\d,]{5,})', f); d['price'] = int(m.group(1).replace(',', '')) if m else None; d['beds'] = d['baths'] = d['sqft'] = ''
    m = re.search(r'\b(Pending|Contingent|Sold|Off market|For sale|Coming soon|Active under contract)\b', f[:6000])
    d['status'] = {'For sale': 'ACTIVE', 'Sold': 'SOLD', 'Off market': 'OFF MARKET', 'Pending': 'PENDING', 'Contingent': 'CONTINGENT', 'Coming soon': 'COMING SOON', 'Active under contract': 'CONTINGENT'}.get(m.group(1), 'UNKNOWN') if m else 'UNKNOWN'
    m = re.search(r'(\d+) days? on Zillow', f); d['dom'] = int(m.group(1)) if m else None
    m = re.search(r'Built in (\d{4})', f); d['built'] = int(m.group(1)) if m else None
    m = re.search(r'\$([\d,]+) Zestimate', f); d['zestimate'] = int(m.group(1).replace(',', '')) if m else None
    m = re.search(r"## What's special (.{20,1500}?)(?: Show more | ## |$)", f); d['remarks'] = m.group(1).strip() if m else ''
    m = re.search(r'((?:Duplex|Multi Family|Single Family Residence|Townhouse|Apartment|Triplex|Quadruplex|Lot|Land)[^#]{0,80}?) Built in', f); d['type_line'] = m.group(1).strip() if m else ''
    m = re.search(r'MLS ?#? ?([A-Z0-9\-]{4,15})', f); d['mls'] = m.group(1) if m else ''
    m = re.search(r'Price cut[^.]{0,80}', f); d['last_event'] = m.group(0) if m else ''
    m = re.search(r'(https://photos\.zillowstatic\.com/fp/[^)\s"]+)', c or ''); d['photo'] = m.group(1) if m else ''
    m = re.search(r'\$([\d,]{3,})\s*(?:/mo|per month|a month|monthly|/month)', d['remarks'], re.I); d['unit_rent_text'] = m.group(0) if m else ''
    return d

def detail_rows(pages):
    """pages = load2(path) output: [(url, content, brd_status)] plus headers are not carried by load2; use load3 for headers."""
    return [parse_detail(u, c) for u, c, b in pages]

def load3(path):
    fd = json.load(open(path)); out = []
    for r in fd['results']:
        dd = (r['response'].get('data') or {}); out.append((dd.get('url') or '', dd.get('content') or '', dd.get('headers') or {}))
    return out

# Usage in a fresh sandbox:
#   exec(open('/mnt/files/pass2/parsers.py').read())
#   merged, counts, bad, add_pages = make_round(ZIPS)
#   for fn in ['tent','lake','into','wore','cost']: add_pages(load2(f'/mnt/files/mex/{fn}.json'))
#   rows = sorted(merged.values(), key=lambda r:(r['page_zip'], r['address']))
#   then write rows with `fields` to a CSV, save it locally as roundN_listings.csv, and run roundN_score.py.
