# merge_constants_0928.py - folds constants_additions_0928.json (2026-09-28: regional sweep, tier costs, rental tax adjustment,
# ZIP-level drive hours and tax rates for the Tuesday-Thursday regions) into constants.json. Re-runnable: existing keys are never
# overwritten (drive_wb / tax_state / insurance_state entries that already exist keep their values); backs up first.
import json, os, shutil, sys
PIPE = os.path.dirname(os.path.abspath(__file__)) + "/"
c = json.load(open(PIPE + "constants.json", encoding="utf-8")); a = json.load(open(PIPE + "constants_additions_0928.json", encoding="utf-8"))
bk = PIPE + "_backup_constants_before_0928.json"
if not os.path.exists(bk): shutil.copy2(PIPE + "constants.json", bk); print("backed up constants.json ->", os.path.basename(bk))
n = 0
for key, src in [("tax_state", "tax_state_add"), ("insurance_state", "insurance_state_add"), ("drive_wb", "drive_wb_add")]:
    c.setdefault(key, {})
    for k, v in a[src].items():
        if k not in c[key]: c[key][k] = v; n += 1
for key in ["tax_zip", "drive_zip", "zip_county", "zip_region", "rental_tax_adjust", "tier_costs", "jurisdiction_flags", "regions"]:
    if key not in c: c[key] = a[key]; n += 1
    elif isinstance(c[key], dict) and isinstance(a[key], dict):
        for k, v in a[key].items():
            if k not in c[key]: c[key][k] = v; n += 1
c.setdefault("drive_ec", {})   # Elizabeth City hours by city; the underwrite uses min(drive_wb, drive_ec) where both exist (memo 63 section 7.1 item 2)
c["_changelog_0928"] = "2026-09-28 (cloud session): regions ncva/phila/pitt/ohio; tier_costs and the Gate 5 bar shift replace the flat drive -2; rental_tax_adjust; tax_zip and drive_zip for the 300 Tuesday-Thursday ZIPs (county ACS 2020-24 owner rates; OSRM hours / 1.15); state defaults for PA OH NJ DE MD WV NY KY; insurance_state for those states = max($1,200, $1,550 x Insurance.com state premium / $2,869 NC-VA mean) - an assumption; jurisdiction_flags."
json.dump(c, open(PIPE + "constants.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(f"merged {n} entries; regions: {list(c['regions'].keys())}; tax_zip {len(c['tax_zip'])}; drive_zip {len(c['drive_zip'])}")
