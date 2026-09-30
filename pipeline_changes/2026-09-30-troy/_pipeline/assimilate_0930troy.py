# -*- coding: utf-8 -*-
"""assimilate_0930troy.py  (2026-09-30, round 20: advisory 73/73a/73b/73c, 306 & 308 Troy Ave NE, Roanoke VA 24012,
file 14 row i=28, decision board 49a id 28; Roanoke tax map 3180117, LRSN 27013, building 3180117R01, 911 points 43574/43575).

Builds 68a (a LONG-FORM CLAIMS LEDGER in the shape memo 67 section 6.6 asked for: one row per attribute, the advisory's claim,
the 9/30 verification, its source and instrument, a status word and what superseded what) and 68b (the record set), patches
file 14 row 28 (status, event, score, coc, dscr, novice, note), APPENDS seven rows to the 67a asks register, extends the
Roanoke row of 32b, updates constants.json, and appends the round-20 lines to _advisory/README.md and the pipeline README.

It does NOT rebase decision board 49a (memo 67 sections 4.4 and 6.6: the dated-column boards are superseded by the ledger
plus file 14 as the view); the 49a id 28 base columns are recorded in 68a with status SUPERSEDED.

Re-runnable: backs up first (_pipeline/_backup_*_before_0930troy.*), refuses to patch a CSV that does not round-trip byte
for byte, and skips register rows and README lines already present. CAMP defaults to the Dropbox path; set CAMP_DIR to run
against a mirror (the cloud session ran it against a mirror and uploaded the outputs).

Private individuals are not named: the owner of record is 'a family living trust' with a Goodview VA 24095 mailing address;
the 2018 grantors are 'the trust's settlors'; the 1979 grantor is 'a private seller (inactive record)'. City inspectors named
in the TRAKiT zone layers are not reproduced here.
"""
import csv, json, os, io, shutil, datetime

CAMP = os.environ.get("CAMP_DIR") or r"C:/Users/najum/Dropbox/linked/FAMILY/Ogo/.Investment/2026-2027 Duplex Search Campaign/"
if not CAMP.endswith("/"): CAMP += "/"
PIPE = CAMP + "_pipeline/"
EVID = CAMP + "_evidence/306&308 Troy Ave NE Roanoke/records_2026-09-30/"
F14 = CAMP + "14 Live status and ranking of the 42 tracked candidates (2026-09-11).csv"
F32B = CAMP + "32b Jurisdiction rules ledger, tax, rental inspection, lead lines, zoning and preemption (2026-09-15).csv"
F67A = CAMP + "67a Asks register, seeded with the advisory's open asks on seven live NC-VA rows (2026-09-29).csv"
CONST = PIPE + "constants.json"
AREADME = CAMP + "_advisory/README.md"
PREADME = PIPE + "README - pipeline handoff (2026-09-11).md"
OUT68A = CAMP + "68a Claims ledger, long form, advisory 73 claims and the 9-30 verification pass, 306-308 Troy Ave NE Roanoke (2026-09-30).csv"
OUT68B = CAMP + "68b 306-308 Troy Ave NE record set, parcel, building, address points, zoning tables, overlays, impervious, mains, permits, code cases, duplex cohort, street roll, tax history, ACS, rents, rates, photos and transports (2026-09-30).csv"
TAG = "0930troy"
TODAY = "2026-09-30"
PROP = "306 & 308 Troy Ave NE, Roanoke, VA 24012"

def backup(src, dst):
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copyfile(src, dst)

for src, dst in ((F14, PIPE + f"_backup_14_before_{TAG}.csv"), (F32B, PIPE + f"_backup_32b_before_{TAG}.csv"),
                 (F67A, PIPE + f"_backup_67a_before_{TAG}.csv"), (CONST, PIPE + f"_backup_constants_before_{TAG}.json"),
                 (AREADME, PIPE + f"_backup_advisory_README_before_{TAG}.md"), (PREADME, PIPE + f"_backup_README_before_{TAG}.md")):
    backup(src, dst)

# ---------------------------------------------------------------- CSV round-trip helpers (BOM + CRLF, as memo 66 required)
def read_csv_bytes(path):
    b = open(path, "rb").read()
    bom = b[:3] == b"\xef\xbb\xbf"
    term = "\r\n" if b.count(b"\r\n") else "\n"
    rows = list(csv.reader(io.StringIO(b.decode("utf-8-sig"), newline="")))
    out = io.StringIO(); csv.writer(out, lineterminator=term).writerows(rows)
    rt = (("\ufeff" if bom else "") + out.getvalue()).encode("utf-8")
    if rt != b:
        raise SystemExit(f"HALT: {os.path.basename(path)} does not round-trip byte for byte; not patched")
    return rows, bom, term

def write_csv_bytes(path, rows, bom, term):
    out = io.StringIO(); csv.writer(out, lineterminator=term).writerows(rows)
    open(path, "wb").write((("\ufeff" if bom else "") + out.getvalue()).encode("utf-8"))

# ---------------------------------------------------------------- numbers (campaign formula)
def pay_factor(rate):
    r = rate / 12.0
    return 12 * r / (1 - (1 + r) ** -360)
K675, K740, K800 = pay_factor(0.0675), pay_factor(0.0740), pay_factor(0.0800)
PRICE = 246000
ASSESSED_2026, ASSESSED_2025 = 199900, 192100
RATE = 0.0122
SOLID_WASTE = 218.40
IMPERV_SF = 2295.5
STORM_UNITS = int(round(IMPERV_SF / 500.0))          # 4.59 -> 5
STORM_RATE_MONTH = 1.55
STORM_FEE = STORM_UNITS * STORM_RATE_MONTH * 12        # 93.00
TAX_Y1 = round(ASSESSED_2026 * RATE + SOLID_WASTE + STORM_FEE)   # 2,750
TAX_LONGRUN_ASK = round(PRICE * RATE + SOLID_WASTE + STORM_FEE)  # 3,313
INS = 1500
def noi(rent_unit, tax=TAX_Y1, owner_paid=0, vac=0.05):
    return rent_unit * 2 * 12 * (1 - vac - 0.10 - 0.08 - 0.05) - tax - INS - owner_paid
def coc_dscr(n, price, k):
    ds = 0.75 * price * k; return round((n - ds) / (0.3125 * price) * 100, 1), round(n / ds, 2)
def price8(n, k):
    return int(round(n / (0.025 + 0.75 * k), -3))
GRID = []
for rent, basis in ((923, "ACS tract 4 median contract rent (in-place floor case)"), (1000, "in-place guess (assumption)"),
                    (1100, "asking comps, low"), (1133, "ACS tract 4 median gross rent (the sweep's basis; retired for the board)"),
                    (1150, "asking comps, center"), (1200, "asking comps, high")):
    n = noi(rent); c1, d1 = coc_dscr(n, PRICE, K675); c2, d2 = coc_dscr(n, PRICE, K740)
    GRID.append({"rent_per_unit": rent, "basis": basis, "noi": round(n), "rtp_pct": round(rent * 2 * 100 / PRICE, 2), "coc_675": c1, "dscr_675": d1,
                 "coc_740": c2, "dscr_740": d2, "price8_675": price8(n, K675), "price8_740": price8(n, K740), "price8_800": price8(n, K800)})
n_center = noi(1150); n_center_longrun = noi(1150, tax=TAX_LONGRUN_ASK)
COC_CENTER_675, DSCR_CENTER_675 = coc_dscr(n_center, PRICE, K675)
COC_CENTER_LR, DSCR_CENTER_LR = coc_dscr(n_center_longrun, PRICE, K675)
RENT_NEEDED_8PCT = round((0.025 * PRICE + 0.75 * PRICE * K675 + TAX_Y1 + INS) / 0.72 / 24)
SENS_VAC75 = price8(noi(1150, vac=0.075), K675) - price8(n_center, K675)
SENS_WATER800 = price8(noi(1150, owner_paid=800), K675) - price8(n_center, K675)

# ---------------------------------------------------------------- 68a: the long-form claims ledger
L = []
def add(attribute, claimed, claimed_by, verified, source, instrument, status, note="", superseded_by="", date=TODAY):
    L.append({"n": len(L) + 1, "property": PROP, "attribute": attribute, "claimed_value": claimed, "claimed_by": claimed_by,
              "verified_value": verified, "source": source, "instrument": instrument, "date": date, "status": status,
              "superseded_by": superseded_by, "note": note})

# --- listing and status
add("listing status", "PENDING since 2026-09-18; listed 2026-09-03 at $246,000; 15 days on market; no price cuts (Redfin 9/29)", "advisory 73b n1",
    "Pending, $246,000; 'Listing updated: Sep 18, 2026 at 10:18am'; '15 days on Redfin, 23 views'; history Sep 18 Pending, Sep 3 Listed $246,000; MLSRV 931038, Virginia Realty Group",
    "Redfin listing page, 2026-09-30", "https://www.redfin.com/VA/Roanoke/306-Troy-Ave-NE-24012/home/131533637 via Bright Data djnicholasq scrape_as_markdown", "REPRODUCED")
add("status date on file 14", "PENDING (2026-09-21), the sweep date", "file 14 row 28 (refresh stage of 9/21)", "PENDING (2026-09-18), the MLS date; the 9/21 and 9/28 sweeps read PENDING with status_date 'Sep 18, 2026'",
    "_sweeps/2026-09-28/tracked.json; tracked_changes.csv", "campaign files", "CORRECTED", "file 14 cell set to the MLS date; the refresh stage still stamps the sweep date (pipeline note)", "file 14 row 28 as patched 2026-09-30")
add("MLS fields", "heat pump (electric); owner pays trash disposal and property management; two-unit property; built 1984; lot 6,969 sf; APN 3180117; zoning RM-1 with an AIRPORT tag", "advisory 73b n2",
    "reproduced on the Redfin page 9/30 (public record block: 4 beds, 2 baths, 2 stories, 1,848 sf, lot 7,040 sf, built 1984, APN 3180117; 'Last updated by owner on Aug 3, 2026'); the zoning card prints 'RM-1 / AIRPORT / Residential District' with an empty 'Zone overlays' list",
    "Redfin listing page, 2026-09-30", "as above", "REPRODUCED", "the MLS lot 6,969 sf against the record 7,040 sf is the usual MLS rounding")
add("AIRPORT tag", "does not appear in any city zoning or overlay layer; unverified", "advisory 73b n2 and n37",
    "identified: the tag sits in Redfin's third-party zoning card; the city's public GIS has no airport overlay service (Zoning/0 and the 22 TRAKiT layers carry none); Roanoke County's published Airport Overlay feature (one polygon named 'Airport') contains the parcel point; the city ordinance's AD airport overlay (36.2-330) is unchanged by the 2024 amendments and its text was not retrieved (municode is script-rendered). Reading: an FAA Part 77 height and obstruction overlay around Roanoke-Blacksburg Regional Airport (about 2.3 miles east-south-east of the airport reference point); no effect on the use or the existing two-story building; aircraft noise not assessed (no ROA Part 150 noise exposure map found)",
    "county Airport Overlay feature service; city GIS service list; Redfin zoning card", "https://services1.arcgis.com/VlZ73DcE2ya6FnSK/arcgis/rest/services/Airport_Overlay_Hosted/FeatureServer/0 (point query, 1 feature); https://maps.roanokeva.gov/arcgis/rest/services/Public?f=json", "EXTENDED", "AD overlay text open; height limits are irrelevant to an existing 2-story dwelling")
add("tax history", "2025 $2,649 on $192,100; 2024 $2,495 on $180,000; 2023 and 2022 on $152,300; 2021 $1,800 on $144,500; 2020 and 2019 on $125,200", "advisory 73b n3",
    "reproduced and extended: 2025 $2,649 on $192,100; 2024 $2,495 on $180,000; 2023 $2,148 on $152,300; 2022 $2,044 on $152,300; 2021 $1,800 on $144,500; 2020 $1,773 on $125,200; 2019 $1,730 on $125,200; 2018 $1,730 on $121,600; 2017 $1,538; 2016 $1,537 on $121,600; 2014 $1,529 on $127,000; city 2026 $199,900. The assessment is up 60 percent since 2020 and the roll moves every year",
    "Redfin tax history table, 2026-09-30; city parcel layer", "as above", "EXTENDED")
add("Zillow parcel page", "Off market; tax assessed $192,100; Rent Zestimate $1,853 a month for the whole building (model, not used)", "advisory 73b n4", "not re-fetched", "n/a", "n/a", "CARRIED")
add("sweep record", "PENDING with status date 2026-09-18 (tracked.json); PENDING 9/21; no change PENDING dom 15 on 9/28; seen_index gone on 9/21", "advisory 73b n7",
    "reproduced: tracked.json 9/28 status PENDING, status_date 'Sep 18, 2026', dom 15, price 246000, history 'Sep 18, 2026 Pending; Sep 3, 2026 Listed $246,000'; tracked_changes.csv 9/28 'no change | PENDING dom 15'",
    "_sweeps/2026-09-28", "campaign files (Dropbox)", "REPRODUCED")

# --- city record
add("parcel", "tax map 3180117; Lot 217 B, Fleming Court; 0.1616 acre (7,040 sf); RM-1; class Multi-Family Duplex; assessed $199,900 on 2026-01-01 (land $36,600, dwelling $163,300) and $192,100 on 2025-01-01; about 2,295 sf impervious", "advisory 73b n8",
    "reproduced: TAXID 3180117, LRSN 27013, LOCADDR 306 TROY AVE NE, LEGALDESC 'LOT 217 B FLEMING COURT', LEGALACRES 0.1616, SQFT 7040, ZONEDESC RM-1, PROPERTYDESC Multi-Family Duplex, TOTALVAL1 199900 (LANDVAL1 36600, DWELLINGVAL1 163300), TOTALVAL2 192100 (DWELLINGVAL2 155500), NEIGHBORHOODNUM 15, TOPODESC Level; owner a family living trust, mailing address Goodview VA 24095 (Bedford County, out of town). Lot edges from the ring: 75.8 ft (street), 87.5 and 97.3 ft (sides), 39.8 + 36.7 ft (rear, two segments)",
    "City of Roanoke parcel layer", "https://maps.roanokeva.gov/arcgis/rest/services/Public/Parcels/MapServer/0/query?where=TAXID='3180117' (plain urllib)", "EXTENDED", "the owner is out of town, consistent with the MLS 'owner pays property management'")
add("transfers", "1979-07 lot purchase $3,000 (conversion record); 2018-12-13 $0 deed into a family living trust, instrument 180011508; no arm's-length sale since 1979", "advisory 73b n9",
    "reproduced: SALEDATE1 2018-12-13 SALEAMT1 0 DOCNUM1 180011508 GRANTOR1 the trust's settlors; SALEDATE2 1979-07-09 SALEAMT2 3000 DOC2NUM CONV000000 GRANTOR2 a private seller (inactive record)",
    "City of Roanoke parcel layer", "as above", "REPRODUCED", "the 1984 building was put up by the 1979 lot buyers (owner-built, assumption); the deed image is in the Circuit Court's subscription land records, not read")
add("911 address points", "306 (ADDR_ID 43574) and 308 (43575), both ACTIVE and field verified on tax map 3180117", "advisory 73b n10",
    "reproduced: two points, STATUS ACTIVE, VERIFIED 'Field Verified', TAX_ID 3180117, LRSN 27013, PSAP 7192, ESN 4, Site_NGUID SSAP43574@roanokeva.gov and SSAP43575@roanokeva.gov, Condo false, PROPERTYDESC Multi-Family Duplex on both",
    "TRAKiT layer 0 Addresses", "https://maps.roanokeva.gov/arcgis/rest/services/Public/Trakit_20221221/MapServer/0/query?where=ADDR_ID IN (43574,43575)", "REPRODUCED")
add("building record", "3180117R01: Duplex; 1984; 2 stories; 1,848 sf; wood frame; brick veneer; foundation None; heat pump; central AC; 4 bedrooms; 2 full baths; condition normal for age; asbestos flag false; footprint about 1,074 sf", "advisory 73b n11",
    "reproduced and extended: BldgID 3180117R01, ImprType DWELLING, UseCode 2 UseDesc Duplex, BldgType '21 Older 2 Story', Stories 2.0, YrBuilt 1984, FinSize 1848, Foundat None, ConstFr Wood frame, ExtDesc1 Brick veneer, CondDesc normal for age, NumRms 4, NumBdRms 4, Num3Baths 2 (full), HeatType 3 Heat pump, CentrlAC Y, Attic None, BsmtArea 0, Asbestos false, footprint Shape_Area 1,074.4 sf",
    "TRAKiT layer 4 Buildings", "https://maps.roanokeva.gov/arcgis/rest/services/Public/Trakit_20221221/MapServer/4/query?where=PIN='3180117'", "EXTENDED", "attic none and basement 0 support the slab reading (assumption stands)")
add("city property class", "class Multi-Family Duplex", "advisory 73b n8",
    "NEW test: the parcel is present in Real_Estate/Parcels_Duplexes/0 and Parcels_Residential/0 and absent from Parcels_MultiFam/0; 126-128 Troy (3180105) is the reverse (300-Multifamily, absent from Duplexes). The city's own class layers read this building as a duplex to any third party who queries them",
    "Real_Estate class layers", "https://maps.roanokeva.gov/arcgis/rest/services/Real_Estate/Parcels_Duplexes/MapServer/0/query?where=TAXID='3180117'", "NEW", "Gate 3 evidence a lender or appraiser can reproduce")
add("zoning", "RM-1 Res Mixed Density, conditional 0; an R-5 single-family boundary within about 40 m", "advisory 73b n12",
    "reproduced: Zoning/0 and TRAKiT layer 15 both return ZONING 11 'RM-1: Res Mixed Density', CONDITIONAL 0; the R-5 distance was not re-measured",
    "City zoning layer", "https://maps.roanokeva.gov/arcgis/rest/services/Public/Zoning/MapServer/0 (point query)", "REPRODUCED")
add("two-family use in RM-1", "RM-1 not conditional; Gate 3 PASS on city record", "advisory 73c gate3",
    "NEW: the 9/16/2024 readoption's use table (36.2-311) shows the pre-2024 row 'Dwelling, two-family' permitted (P) in RM-1 and the new row 'Dwellings' permitted in every residential district under 36.2-409.1; so a two-unit building on one lot is a by-right use in RM-1 under the text in force AND under the text a rollback would restore (the July 2026 council vote shelved the staff compromise; the 2024 rules remain). Dimensional (36.2-312): old table RM-1 minimum lot area 5,000 sf, 3,500 sf per dwelling unit, 50 ft frontage; new table 4,000 sf, 1,500 sf per dwelling, 40 ft (as read in advisory 36 on 9/16); the lot's 7,040 sf and about 76 ft of frontage clear both",
    "City of Roanoke, Ord. 43049 final draft (2024 amendments), pdf text", "https://www.roanokeva.gov/DocumentCenter/View/20166 (plain curl + pymupdf)", "NEW", "unlike 126-128 Troy (two detached dwellings, which rests on 36.2-409.1(c)(4)), this row does not depend on the 2024 reform surviving")
add("overlays", "none: rental inspection, historic, design, sign, conservation rehab, flood hazard, river and creek corridor, flood reduction easements; census tract 4, block group 1; code enforcement zone 3; layer 22 refused", "advisory 73b n13",
    "reproduced across 60 public layers at the parcel point: none for rental inspection districts, historic districts, National Register (properties and districts), conservation rehab, design overlay, sign overlay, neighborhood design districts, effective flood hazard (Flood_Zones, FloodPlain, FEMA, Special_Flood_Hazard_Areas, floodway), river and creek corridor, all easement classes, LeadSafe projects, HUD qualified census blocks, opportunity zones, enterprise zone 1A, VDOT chapter 527, service districts. Present: preliminary FEMA 2025 layer DFIRM 51161C zone X 'AREA OF MINIMAL FLOOD HAZARD' (SFHA F); watershed Tinker Creek (HUC6 RU13); annexed 1949; census tract 4 (51770000400, pop 4,761), block group 1 (1,556); layer 22 (2017 imagery) refuses point queries (HTTP 400, reproduced)",
    "City GIS, 60 layers", "https://maps.roanokeva.gov/arcgis/rest/services/Public/* (point-intersect script; results in _evidence/.../records_2026-09-30/point_layers_306troy.json)", "EXTENDED")
add("districts and programs", "not in HUD QCB, opportunity zones, enterprise zone 1A or Lead-Safe; character district Suburb; trash day Tuesday", "advisory 73b n14",
    "reproduced and extended: character district Suburb; trash Tuesday; recycling TUE zone 3 week B; snow zone 4N subzone 4B; neighborhood Preston Park in the Williamson Road Area plan (status Complete); code enforcement zone 3; development inspection zone 1; residential building, electrical, plumbing and mechanical inspection zone NE; civil process zone NE; schools Monterey Elementary, James Breckinridge Middle, William Fleming High",
    "City GIS district layers", "as above", "EXTENDED", "school zones are a tenant-pool note only (the family in one unit has children)")
add("water mains", "6-inch cast iron dated 1955; 8-inch cast iron dated 1963; mains only, no meters or service lines", "advisory 73b n15",
    "reproduced: within 60 m, PIPE-001890 8-inch CI installed 1963-01-01 and PIPE-009708 6-inch CI installed 1955-09-01, both DIST, INUSE, HGL 1263; no service line or meter features in the layer",
    "WVWA water layer on the city server", "https://maps.roanokeva.gov/arcgis/rest/services/Public/WVWA_Water/MapServer/0 (60 m buffer)", "REPRODUCED")
add("sewer collectors", "8-inch vitrified clay dated 1940 and 1949; one 8-inch PVC segment; lateral ownership rule not retrieved", "advisory 73b n16",
    "reproduced on the retry (three earlier queries answered HTTP 500): five segments within 60 m (see 68b for the attributes); the Authority's lateral ownership rule was not retrieved (westernvawater.org answers 403 to plain fetches and returned an empty body through Bright Data)",
    "WVWA sewer layer on the city server", "https://maps.roanokeva.gov/arcgis/rest/services/Public/WVWA_Sewer/MapServer/0 (60 m buffer)", "REPRODUCED", "camera scope at inspection stands as the settling instrument")
add("capital project", "Huntington curb, gutter and sidewalk, within about 500 m", "advisory 73b n17",
    "not reproduced: the Engineering_CIP line layer returned no features within 500 m of the parcel point on 9/30", "City engineering CIP layer", "https://maps.roanokeva.gov/arcgis/rest/services/Public/Engineering_CIP/MapServer/0 (500 m buffer)", "OPEN", "not load-bearing; a city CIP project carries no special assessment on abutters as a rule (assumption)")
add("street roll", "Troy Ave NE: 33 parcels, 30 single-family, 2 multifamily (126 and 227), 1 duplex (306); single-family sales $214,000 to $274,000 in 2024 and 2025 (121, 122, 125 and 132)", "advisory 73b n18",
    "reproduced: 33 parcels; 30 '200-SingleFamily', 126 and 227 '300-Multifamily', 306 'Multi-Family Duplex'; all RM-1; land value $36,600 on 31 parcels ($40,300 on the two 0.31-acre lots); 2024-25 single-family sales 121 ($254,950, 12/2024), 122 ($227,950, 6/2024), 125 ($214,000, 6/2024), 132 ($274,000, 2/2025); owner mailing addresses in Roanoke on 31 parcels, Daleville on 317, Goodview on 306; 307 Troy transferred 3/2023 for $10,000 (not arm's length)",
    "City of Roanoke parcel layer", "query ADDRSTREET='TROY' AND ADDRQUAD='NE' (records_2026-09-30/troy_ave_ne_street_roll.json)", "REPRODUCED")
add("duplex sale cohort", "89 single-parcel duplex transfers of $50,000 to $600,000 since 2024-01-01: median $215,000, sale to 2025 assessment 1.17, 17 percent at or under 0.95; 2025 and 2026: 58 sales, $213,500, 1.20, 16 percent; north side (neighborhoods 11 to 17 and 22): 21 sales, $230,000, 1.15, 24 percent", "advisory 73b n19",
    "reproduced to the decimal: 967 Multi-Family Duplex parcels citywide; 120 last transfers on or after 2024-01-01 in the band; 89 after removing same-date same-amount packages; median $215,000; median sale to 2025 assessment 1.18; 17 percent at or under 0.95; 2025-26 n=58, $213,500, 1.21, 16 percent; north side n=21, $230,000, 1.15, 24 percent. Extended: assessor neighborhood 15 (this parcel's) has ONE duplex transfer since 2024, 521 Fleming Ave NE on 2025-04-22 at $167,500 against a $192,800 assessment (0.87), and its 2026 assessment stayed $192,800",
    "City of Roanoke parcel layer, class Multi-Family Duplex, last transfer per parcel", "paged query (records_2026-09-30/duplex_parcels_all_967.json; duplex_cohort_since2024.csv)", "EXTENDED", "a below-assessment sale did not pull the roll down: the 8 percent price can carry the assessed-value tax, the ask cannot")
add("impervious surface and stormwater units", "about 2,295 sf impervious; stormwater about $87", "advisory 73b n8 and 73c tax_note",
    "reproduced and corrected: six polygons on the parcel (source 2011 VBMP): building 1,074.4; deck/patio 165.3 and 149.2; driveways 525.5 and 346.1; unknown 35.2; total 2,295.5 sf = 4.59 units, rounded to 5 billing units = $93.00 a year at $1.55 a month per unit. The $87 on the 2025 bill is 5 units at $17.40 (the $1.45 rate of that year); the 2024 bill implies about $1.34",
    "Impervious_Surface_Final_2026 layer; city stormwater fee page", "https://maps.roanokeva.gov/arcgis/rest/services/Public/Impervious_Surface_Final_2026/MapServer/0 (parcel polygon query); https://www.roanokeva.gov/1843/Storm-Utility-Fee-and-Credits", "CORRECTED", "each unit has its own driveway and rear patio polygon; the fee has risen about $0.10 a year (assumption on the next step)")

# --- rents and ACS
add("Zillow 24012 two-bedroom trends", "average $1,300; month over month -$80; year over year +$125; 41 available; range $850 to $3,360; most common band $1,200; COOL; updated 2026-09-27", "advisory 73b n20",
    "reproduced on the 9/28 refresh: average $1,300; month over month -$60; year over year +$201; 40 available; range $850 to $3,360; modal bands $1,100 and $1,200 (9 listings each), $1,300 (7); COOL; 2026 monthly averages Jan $1,223, Feb $1,200, Mar $1,217, Apr $1,200, May $1,223, Jun $1,199, Jul $1,400, Aug $1,350, Sep $1,300",
    "Zillow rental manager market trends, updated 2026-09-28", "https://www.zillow.com/rental-manager/market-trends/24012/?bedrooms=2 via Bright Data ajumobinicholasY", "REPRODUCED", "asking rents; the band $1,100 to $1,200 stands", "9/28 refresh")
add("Redfin 24012 two-bedroom rentals", "46 listings; small-landlord 2BR/1BA asks $850 to $1,395, median $1,100 (15 units); size-matched 855 to 950 sf: $995, $1,095, $1,100, $1,199, $1,199", "advisory 73b n21", "not re-fetched", "n/a", "n/a", "CARRIED")
add("ACS tract 4 (51770000400)", "contract rent $923 (186); gross rent $1,133 (191); 2BR gross $1,111 (78); MHI $47,045; renter MHI $30,639 (22,406); renters 903 of 2,078; vacant for rent 242 (178); poverty 33 percent", "advisory 73b n22",
    "reproduced exactly (ACS 2020-2024 5-year): B25058 $923 (+/-186); B25064 $1,133 (+/-191); B25031 2BR $1,111 (+/-78); B19013 $47,045 (+/-10,871); B25119 renter $30,639 (+/-22,406); B25003 renters 903 (+/-315) of 2,078; B25004 vacant for rent 242 (+/-178); B17001 1,750 of 5,365 = 32.6 percent",
    "Census Reporter API", "https://api.censusreporter.org/1.0/data/show/latest?table_ids=B25064,B25058,B25031,B19013,B25119,B25003,B25004,B17001&geo_ids=14000US51770000400,05000US51770 (plain curl, 200)", "REPRODUCED", "tract margins are wide, as the advisory said")
add("ACS Roanoke city", "contract rent $836 (22); gross rent $996 (30); 2BR gross $967 (39); renter MHI $40,701 (3,637); renters 20,723 of 43,575; vacant for rent 1,681 (380), rental vacancy 7.5 percent; poverty 18 percent", "advisory 73b n23",
    "reproduced exactly: B25058 $836; B25064 $996; B25031 $967; B25119 $40,701; B25003 20,723 of 43,575; B25004 1,681 -> 1,681 / (20,723 + 1,681) = 7.5 percent; B17001 17,729 of 96,723 = 18.3 percent", "Census Reporter API", "as above", "REPRODUCED")
add("Census API", "HTTP 302 to missing_key.html; switched to Census Reporter", "advisory 73b n24", "not re-tried (the campaign holds a key since 9/28, memo 64)", "n/a", "n/a", "CARRIED")
add("rent source in the sweep code", "weekly_sweep.py lines 169 and 249: rent = units x tract median_rent when no rent is stated; 494 of 543 rows scored on 9/28", "advisory 73b n25",
    "reproduced on the 9/29 version of weekly_sweep.py (the regional rebuild kept both lines): line 169 'rent = rent_stated or ((units or 2) * med ...)'; line 249 'rent = num(j.get(\"rents\")) or (2 * med ...)'",
    "_pipeline/weekly_sweep.py (2026-09-29 05:19 UTC)", "campaign file", "REPRODUCED")
add("tract model rent = ACS gross rent", "median_rent equals ACS B25064 gross rent in 25 of 25 sampled passing tracts; contract to gross median 0.83 (0.31 to 1.00); gross minus contract median $213", "advisory 73b n26",
    "reproduced for this tract and by the model's own field: tract_scores_x1.0.json['51770000400'].median_rent = 1133.0 = B25064 (not B25058's 923), and the model's annual_gross_rent field is median_rent x 24 (27,192), i.e. the model names its basis gross. The 25-tract sample was not re-run (Census Reporter answered 403 to the batch call after serving the single call)",
    "_pipeline/model/tract_scores_x1.0.json; Census Reporter", "local JSON; API", "REPRODUCED", "load-bearing; logged as pipeline DEFECT 4 for Najum's decision, not applied")
add("documented rolls against the sweep rent", "median 0.73: Daughtry 0.65, Scarborough 0.66, Star 0.73, Jacob 0.73, Rogers 0.75, Penmar 0.76, Auburndale 0.80 (seven rows, not random)", "advisory 73b n27", "not recomputed", "campaign boards", "n/a", "CARRIED")
add("effect on the 9/28 NC-VA sweep", "439 tract-rent rows with a rent to price: 125 pass Gate 5 as scored, 76 at x0.83, 54 at x0.73; entrants Floyd 20.3 to 12.3 and 7.6; Faison St E 14.7 to 7.6 and 3.4; 4 12 1/2 St SW 6.6 to 0.9 and -2.5", "advisory 73b n28",
    "reproduced exactly on scored.csv and results.csv: 440 tract-rent rows with a rent-to-price (the advisory's 439 is the same set less one blank); Gate 5 passes 125 / 76 / 54 at x1.0 / x0.83 / x0.73; the three ENTRANTs carry rent 'tract median x 2' (Floyd $2,018, Faison $1,508, 4 12 1/2 St $1,922) with CoC 20.3 / 14.7 / 6.6 as printed",
    "_sweeps/2026-09-28/scored.csv and results.csv", "campaign files", "REPRODUCED")

# --- tax and fees
add("FY2027 real estate tax rate", "$1.22 per $100 held, council vote 2026-05-11; an $18 million deficit closed with position and capital cuts", "advisory 73b n29",
    "reproduced: Cardinal News 5/12/2026: rate unchanged at $1.22 per $100 (one member voting against the rate as high), $421.5 million budget adopted 5-2 on Monday 5/11/2026, an $18 million deficit closed with about 30 position eliminations and $50.4 million removed from capital projects; the city's FY2027 highlights page: adopted 5/11/2026, $421.5 million, CIP $139.3 million",
    "Cardinal News; roanokeva.gov FY2027 highlights", "https://cardinalnews.org/2026/05/12/roanoke-budget-approved-by-5-2-vote-the-second-consecutive-year-of-significant-cuts/ ; https://www.roanokeva.gov/1837/Budget-Development (WebFetch)", "REPRODUCED", "confirms constants tax_assessed_combined_rate.Roanoke 0.0122 for FY2027")
add("real estate growth slowing", "the FY2027 revenue assumptions say real estate growth has begun to slow", "advisory 73b n30", "not re-read", "City budget briefing 2026-03-02", "n/a", "CARRIED")
add("solid waste fee", "$218.40 a year for properties with more than one home, on the tax bill", "advisory 73c tax_note; constants owner_side_municipal_fees.Roanoke",
    "reproduced on the city page 9/30: $109.20 a year single-family; $218.40 a year for properties with more than one home; billed as a separate charge on the real estate tax bills in the fall and spring; 10 percent penalty and 10 percent yearly interest when late",
    "City of Roanoke solid waste fee page", "https://www.roanokeva.gov/480/Solid-Waste-Fees-and-Enforcement (WebFetch)", "REPRODUCED")
add("stormwater fee rate", "about $87 a year", "advisory 73c tax_note",
    "corrected: the current rate is $1.55 a month per billing unit ($18.60 a year), one unit per 500 sf of impervious area rounded to the nearest whole number, with a residential credit of up to 50 percent; 5 units = $93.00. The 2025 bill's $87 = 5 x $17.40 (rate $1.45); the 2024 bill's implied $80.60 = 5 x $16.12 (rate about $1.34)",
    "City of Roanoke stormwater fee page; Redfin tax history", "https://www.roanokeva.gov/1843/Storm-Utility-Fee-and-Credits (WebFetch)", "CORRECTED", "the 50 percent residential credit (apply by June 1) is a $46 a year question")
add("tax year one", "$2,744 (assessed $199,900 x 1.22 percent = $2,439 + $218.40 + about $87); drop the separate $160 trash line", "advisory 73c tax_year1",
    f"corrected to ${TAX_Y1:,}: $2,438.78 + $218.40 + $93.00 = $2,750.18. The 2025 bill reconciles exactly: 192,100 x 0.0122 = 2,343.62 + 218.40 + 87.00 = 2,649.02 (Redfin prints $2,649). The trash-line double count on 49a id 28 (owner_paid_services 160 'Roanoke trash fee' on top of a tax line at price x 1.22 percent) is reproduced and dropped",
    "arithmetic on the city rate and fee pages; 49a", "n/a", "CORRECTED", "immaterial to the verdict (the 8 percent price moves about $70)")
add("tax long run at the ask", "(not stated)", "this pass",
    f"NEW: Roanoke reassesses every year and the roll has tracked the market (+6.7 percent for 2025, +4.1 percent for 2026, +60 percent since 2020); a purchase at $246,000 would be captured within one or two reassessments (assumption from the series), so the long-run bill at the ask is about ${TAX_LONGRUN_ASK:,} (246,000 x 0.0122 + $311.40), which takes cash-on-cash at the ask on the $1,150 comp center from {COC_CENTER_675} to {COC_CENTER_LR} percent at 6.75 (DSCR {DSCR_CENTER_675} to {DSCR_CENTER_LR}). At the 8 percent price (below the assessment) the assessed basis holds: the only neighborhood-15 duplex sale since 2024 closed at 0.87 x assessment and kept its assessment the next year",
    "city parcel layer; Redfin tax history; the 521 Fleming Ave NE precedent", "n/a", "NEW", "the 73c grid is unchanged at and below the 8 percent price; only the at-ask rows worsen")

# --- other advisory claims
add("polybutylene era", "supply pipe of 1978 to 1995 construction, heaviest in the mid-1980s; some insurers exclude plumbing losses; no seller disclosure duty; marked PB-2110", "advisory 73b n31", "not re-verified; no frame shows supply piping", "web sources cited by the advisory", "n/a", "CARRIED", "ask 73a row 5 stands")
add("radon", "Roanoke County on the VDH list of high-population Zone 1 counties; a local contractor cites 30 to 40 percent of area homes testing high; the city's zone assumed the same as the county", "advisory 73b n32",
    "county claim carried; the city's own designation was not retrievable (EPA's Virginia zone list answered 403; VDH's map page prints the map without a locality list; the sosradon fact sheet answered 404)", "VDH; EPA", "https://www.vdh.virginia.gov/radiological-health/indoor-radon-program/epa-radon-risk-map-for-virginia/ (WebFetch)", "OPEN", "the test in each unit is the answer either way")
add("contract cancellation rate", "about 14 percent of U.S. contracts written in July 2026 fell through; 13 to 14 percent band for four years", "advisory 73b n33", "not re-verified", "Redfin via PR Newswire", "n/a", "CARRIED")
add("Bright Data connectors", "search calls on djnicholasaY and djnicholasq failed authentication on 9/29", "advisory 73b n34",
    "superseded today: djnicholasq served the Redfin listing and ajumobinicholasY served the Zillow trends page; bjumobinicholasY (not tried by the advisory) returned an empty body for westernvawater.org; all three sessions expired once mid-run and reconnected", "Bright Data direct connectors", "scrape_as_markdown", "SUPERSEDED", "", "this pass")
add("code cases", "Real_Estate/RealEstate_CodeViolations has no layers; the CodeEnforcement folder is empty", "advisory 73b n35",
    "reproduced for the GIS, corrected for the record: eTrakit's case search answers a scripted full-field postback. Parcel 3180117: ONE case, AV20-0638 INOPERABLE VEHICLE at 308 Troy Ave NE, record id CRW:2009220958483594 (2020-09-22). Street: five inoperable-vehicle cases at 106 Troy (2006-2008) and nothing else on the first page (the grid pages at 20 rows)",
    "Roanoke eTrakit case search", "https://trakit.roanokeva.gov/etrakit/Search/case.aspx (POST SITE_APN EQUALS 3180117 with every form field; detail view login-gated)", "CORRECTED", "a tenant-behavior case, closed by inference (six years old); nothing on the building")
add("permits", "(not searched)", "advisory 73",
    "NEW: eTrakit permit search by tax ID returns ONE permit, ZVBL21-0310 at 308 Troy Ave NE, record id PLSS:210506020208704 (2021-05-06). No B, M, E, P, RELE, RMEC, RPLB or RMRP permit on the parcel (the street's corpus shows those series in use since 2002, e.g. RMEC20-0191 at 106 Troy), so any heat pump, water heater or electrical replacement since about 2002 was either never done or done without a permit. Decode of ZVBL (moderate): a zoning verification for a business licence: the ZVBL21 series ran 0300 to 0319 between 4/30 and 5/12/2021 across suites, apartments and houses (about 800 a year), ZVBL26 restarted at 0001 on 1/2/2026, and the city requires Permit Center verification of the use before a business licence issues (advisory 36 section 9). ZVBL21-0305 was issued at 307 Troy Ave NE the day before",
    "Roanoke eTrakit permit search", "https://trakit.roanokeva.gov/etrakit/Search/permit.aspx (POST SITE_APN EQUALS 3180117; PERMIT_NO BEGINS WITH ZVBL21-03 and ZVBL26)", "NEW", "if the 2021 verification was for rental of real estate, the city holds a written zoning answer on the two-unit use; a records request costs nothing (ask added to 67a)")
add("crime incidents", "the Police folder holds beats, districts, zones and school buffers only", "advisory 73b n36",
    "reproduced for the GIS; the city publishes incidents through CityProtect (hundred-block generalized, filterable by date and hour, no download or API); not queried", "roanokeva.gov crime mapping page", "https://www.roanokeva.gov/334/Crime-Mapping (WebFetch)", "EXTENDED", "the ZIP-level CrimeGrade F stands as the only measure")
add("photos", "23 frames, all SHA-256 distinct; blind read prefix 91892bc26503b93d written 07:17 UTC before the board was opened", "advisory 73b n38",
    "reproduced: the uploaded zip and the Dropbox folder (23 files, placed 2026-09-29 07:07 to 07:09 UTC) hold 23 JPEGs with 23 distinct SHA-256 hashes (list in records_2026-09-30/photo_sha256_23_frames.json); every frame was read on 9/30; the blind read's timestamp precedes the board being opened by the advisory's own account (not independently checkable)",
    "_evidence/306&308 Troy Ave NE Roanoke/306&308_troy_mls_photos_2026-09-29", "sha256sum", "REPRODUCED")
add("photo grade (inter-rater)", "board: GREEN, C2 on the front photo (9/9); advisory blind read: exterior C3, updated unit C3, other unit C3 to C4, no RED", "file 14 (9/9); advisory 73 appendix A",
    "this pass, all 23 frames: exterior C3 (brick sound; vinyl above with mildew streaking on the rear upper wall; aluminum gutters; white vinyl double-hung windows that read as replacements, assumption); the unit with stainless appliances C3 (fresh paint, new appliances, 1984 stained cabinets, laminate, sheet vinyl, carpet); the other unit C3 to C4 (worn original cabinets, older white and black appliances, worn sheet vinyl); no RED item under file 08. Front photo alone: C3. Agreement with the blind read on every grade; the board's 9/9 C2 was one step high",
    "the 23 frames", "Read tool, plus crops at 2x to 5x", "REPRODUCED", "logged in constants.inter_rater_log (memo 67 section 7.5)")
add("upstairs supply and heat", "ducted forced air in both units (ceiling and high-wall supplies, floor-level return on the laundry closet wall); water heater not shown", "advisory 73 appendix A",
    "extended and partly corrected: the second floor IS ducted: floor-level wall supply registers in the bath of the updated unit (frame 9) and in the bunk-bed room of the other unit (frame 17); but long baseboard-type units sit under the primary and second bedroom windows in both units (frames 7, 8, 16): baseboard diffusers of the same duct system or electric baseboard heaters, unresolved at this resolution. A digital thermostat with a surface-run wire (frame 12) reads as a retrofit control, i.e. a system replaced after 1984",
    "frames 7, 8, 9, 12, 16, 17 and crops", "Read tool", "EXTENDED", "added to the data-plate ask: whether the bedroom units are diffusers or resistance heaters, and whether the upstairs is on the heat pump duct")
add("kitchen ceiling access panel", "square access panel in the kitchen ceiling under the upstairs bath (possible past leak access), unit B", "advisory 73 appendix A",
    "reproduced: a square white panel in the kitchen ceiling of the unit with the white appliances (frames 13, 14, 15), under the bath by the Cubicasa plan; none in the other unit's kitchen (frames 3, 4)", "frames 3, 4, 13, 14, 15", "Read tool and crops", "REPRODUCED")
add("condenser and meters", "one outdoor condenser visible at the rear (left unit side); one meter base with meter plus two small disconnects on the left unit's rear wall; right unit's rear wall behind the fence", "advisory 73 appendix A",
    "reproduced: frame 19 shows one gray round-top condenser (a 2000s-2010s cabinet style, assumption; no data plate readable), one meter base and two disconnect boxes on the left unit's rear wall, two conduits to the eave lights, a downspout at the rear corner; the right unit's rear is behind the fence", "frame 19 and crops", "Read tool", "REPRODUCED")
add("roof", "not visible in any of the 23 frames", "advisory 73a row 3",
    "extended: ESRI World Imagery and the city's 2021 Pictometry export show a uniform gray shingle gable roof, ridge parallel to the street, gable ends on the sides, no visible patching, tarps or moss; age not readable from imagery. The assessor's photo of 5/1/2026 shows the left-front elevation only",
    "ESRI World_Imagery export; city Imagery_Pictometry_2021 export; assessor photo", "https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/export ; https://maps.roanokeva.gov/arcgis/rest/services/Public/Imagery_Pictometry_2021/MapServer/export ; https://maps.roanokeva.gov/img_photoshare/318/3180117-1.jpg", "EXTENDED", "roof age stays an ask (73a row 3)")
add("WVWA rates and lateral rule", "meter count not public; one shared owner-paid meter at about $800 a year (assumption)", "advisory 73b n3 note; 73c owner_paid_note",
    "not retrieved: westernvawater.org (rates, backup and service-line pages) answers 403 to plain fetches and returned an empty body through Bright Data; the Authority's water service line inventory web app is a private ArcGIS Online item (403 to the REST API); the mains layers on the city server carry no meters. The $800 a year assumption stands (it is the campaign's Roanoke two-unit figure since 9/14)",
    "westernvawater.org; arcgis.com item 6d8c90a0b035469d89b9c3a759bd2b53", "curl; Bright Data bjumobinicholasY; REST", "NOT RETRIEVED", "ask 73a row 2 stands; the inventory map is a browser-only check for Najum")
add("housing voucher program", "(payment standards not retrieved; voucher case not modelled)", "advisory 73",
    "NEW: the Roanoke Redevelopment and Housing Authority's Housing Choice Voucher page (read 9/30) says the program 'will pause issuing new vouchers until further notice' for budget reasons and the application process is closed; payment standards by bedroom are not on the page. A voucher floor for a vacant unit is therefore not available for a new tenancy in Roanoke now (applies to every Roanoke row)",
    "rkehousing.org HCV page", "https://rkehousing.org/housing-options/section-8/ (WebFetch)", "NEW", "constants.rrha_hcv_status_2026")
add("rate of the week", "6.75 / 7.40 triple; PMMS not quoted", "advisory 73c",
    "reproduced: PMMS 30-year 7.03 percent on 9/24/2026 (+8 bp), the latest print; the triple 6.75 / 7.40 / 8.00 unchanged", "Freddie Mac PMMS history", "https://www.freddiemac.com/pmms/docs/PMMS_history.csv (plain curl)", "REPRODUCED")
add("underwriting grid", "six rows at $923 to $1,200 a unit: CoC -3.5 to 2.8 at 6.75, DSCR 0.82 to 1.15, 8 percent price $140,000 / $134,000 to $198,000 / $189,000; rent needed at the ask $1,433", "advisory 73c underwriting_at_ask",
    f"reproduced to the dollar with the campaign formula (vacancy 5, management 10, maintenance 8, reserves 5 percent; 75 percent loan, 30 years, annual constants 0.077832 at 6.75 and 0.083087 at 7.40; cash in 31.25 percent; debt service $14,360 / $15,330): $923 row NOI $11,705, CoC -3.5, DSCR 0.82, 8 percent price $140,000; $1,150 row NOI $15,628, CoC {COC_CENTER_675}, DSCR {DSCR_CENTER_675}, $187,000 / $179,000; $1,200 row $198,000 / $189,000; rent needed at the ask ${RENT_NEEDED_8PCT:,}. With tax at ${TAX_Y1:,} the 8 percent prices move by less than $100. Sensitivities: vacancy 7.5 percent {SENS_VAC75:+,} on the 8 percent price; owner-paid water $800 {SENS_WATER800:+,}",
    "this script (GRID)", "n/a", "REPRODUCED", "the grid is in 68b")
add("probability", "about 0.01: contract fails about 0.15 x seller accepts the 8 percent price about 0.05 to 0.1", "advisory 73c probability_chain",
    "reproduced at one significant figure (memo 67 section 7.3): 0.01. Extended reading of the second factor: the listing pitches conversion to a single-family with an in-law suite, and a 1984 side-by-side on a single-family street went pending in 15 days at 1.23 x assessment with 23 Redfin views; the pending buyer is plausibly an owner-occupant on a low-down-payment two-unit loan (assumption), so the investor's 8 percent price ($134,000 to $198,000) sits 20 to 45 percent under what the market paid, and a relist after an inspection exit meets the same buyer pool",
    "Redfin listing; cohort", "n/a", "REPRODUCED", "memo 67 section 7.2, the market as inspector")
add("verdict", "PARK; out of the review queue under memo 67 section 6.1; relist tripwire only; no agent time", "advisory 73 and 73c",
    "reproduced: the row is PENDING today, so it fails the first test of the 6.1 queue rule; tripwire (ACTIVE again after a contract failure, or any list price at or under $198,000) adopted; first move on the tripwire: send the 67a asks the same day; offer at the 8 percent price on the documented roll", "memo 67 section 6.1", "n/a", "REPRODUCED")
add("49a id 28 base columns", "status ACTIVE; rent 2,075 'HUD FY2026 SAFMR x 0.83'; owner_paid_services 160 'Roanoke trash fee'; rtp 0.84; coc -1.4; dscr 0.92; g5 FAIL; gate_rank 'FAILS G5 #3'; tax at price x 1.22 percent", "decision board 49a (9/26)",
    "superseded: status PENDING (9/18); rent basis asking comps $1,100 to $1,200 with the tract contract rent $923 as the floor case; owner-paid 0 (the fee sits in the tax bill); tax $2,750 year one; CoC 1.6 / DSCR 1.09 at the comp center; Gate 5 marginal (0.89 to 0.98); Gate 6 FAIL. The board is not rebased (memo 67 section 6.6); file 14 row 28 is the view",
    "this pass", "n/a", "SUPERSEDED", "", "file 14 row 28 (2026-09-30) and this ledger")
add("file 14 novice cell", "GREEN: C2 on the front photo, built 1984, renovation language in the listing (9/9)", "file 14 row 28",
    "restated in the memo 66 grammar: GREEN-verify: C3 in 23 MLS frames ...; 1984, no RED; roof, heat pumps, water heaters, supply pipe, ceiling panel, bedroom heat units unconfirmed (9/30)", "this pass", "n/a", "CORRECTED", "GREEN-verify because a post-1978 C3 is GREEN by rule and the verify items are the system ages")
add("lead-based paint rule", "built after 1978, so the lead-based paint disclosure rules do not apply", "advisory 73 section 2.1", "reproduced (YrBuilt 1984 on the building record)", "TRAKiT layer 4", "as above", "REPRODUCED")
add("tenant ability to pay", "tract median renter income $30,639 (margin $22,406); poverty 33 percent; a $1,150 rent needs about $46,000 at 30 percent", "advisory 73 section 2.4", "reproduced from the ACS pull (the arithmetic holds: 1,150 x 12 / 0.30 = $46,000)", "Census Reporter", "as above", "REPRODUCED")
add("vacancy", "city ACS rental vacancy 7.5 percent (5.7 to 9.4) against the 5 percent constant; tract 21 percent (5 to 42), too noisy", "advisory 73 section 3.2", "reproduced: city 1,681 / 22,404 = 7.5 percent; tract 242 / 1,145 = 21 percent with a +/-178 margin on the numerator", "Census Reporter", "as above", "REPRODUCED", "a per-city vacancy constant is not adopted this round (it moves every VA row); flagged")
add("owner and manager", "the seller of record is a family living trust that bought the lot in 1979 and built the building; the MLS says the owner pays property management", "advisory 73 section 1",
    "extended: the trust's mailing address is in Goodview (Bedford County), about 30 minutes east; an out-of-town owner with a manager means the leases and the ledger sit with the manager, who is the right addressee for 73a row 1", "city parcel layer", "as above", "EXTENDED")
add("asks", "six asks drafted in 73a in the 67a register columns, none sent; send only if the listing returns to ACTIVE", "advisory 73a",
    "logged: the six rows appended to 67a with the property key and P 0.01 (9/30), plus a seventh (a records request to the City for permit ZVBL21-0310, which costs nothing and can go before any relist); sent_on blank", "67a asks register", "this script", "EXTENDED")

# ---------------------------------------------------------------- 68b: the record set
RS = []
def rec(section, item, record): RS.append({"section": section, "item": item, "record": record})
def load(name):
    try: return json.load(open(EVID + name, encoding="utf-8"))
    except Exception as e: return {"error": str(e)}
def ms(v):
    try: return str(datetime.datetime.utcfromtimestamp(v / 1000).date()) if v else ""
    except Exception: return str(v)
p = load("parcel_3180117.json")
if "features" in p:
    a = p["features"][0]["attributes"]
    rec("parcel", "3180117", "; ".join(f"{k}={v}" for k, v in a.items() if v not in (None, "", " ") and k not in ("OWNER", "OWNERADDR1", "GRANTOR1", "GRANTOR2", "OBJECTID") and not k.startswith("Shape")) + f"; SALEDATE1={ms(a.get('SALEDATE1'))}; SALEDATE2={ms(a.get('SALEDATE2'))}; OWNER=a family living trust; MAILCITY=GOODVIEW VA 24095; GRANTOR1=the trust's settlors; GRANTOR2=a private seller (inactive record)")
    rec("parcel", "lot_edges_ft", "75.8 (street), 87.5, 39.8, 36.7, 97.3 (six vertices; the rear is two segments); area 7,044 sf by the shape, 7,040 by the record")
b = load("building_3180117.json")
if "features" in b:
    a = b["features"][0]["attributes"]; rec("building", "3180117R01", "; ".join(f"{k}={v}" for k, v in a.items() if v not in (None, "", " ") and k != "OBJECTID"))
ad = load("addr_3180117.json")
for f in ad.get("features", []):
    a = f["attributes"]; rec("address_points", str(a.get("ADDR_ID")), f"{a.get('FULL_NAME')}; STATUS {a.get('STATUS')}; VERIFIED {a.get('VERIFIED')}; TAX_ID {a.get('TAX_ID')}; LRSN {a.get('LRSN')}; PSAP {a.get('PSAP')}; ESN {a.get('ESN')}; Site_NGUID {a.get('Site_NGUID')}; Condo {a.get('Condo')}; PROPERTYDESC {a.get('PROPERTYDESC')}; point {f.get('geometry')}")
MASK_KEYS = {"OWNER", "OWNERADDR1", "OWNER2", "Owner2", "GRANTOR1", "GRANTOR2", "Grantor1", "Grantor2", "INSPECTOR", "Fire", "RightofWay", "Development", "NDD",
             "Historic", "Building", "Electric", "Plumbing", "Mechanical", "Tent", "Manufactured", "Res_Building", "Res_Electric", "Res_Plumbing", "Res_Mechanical", "Res_Manufactured"}
def mask(o):
    """private individuals and city staff are not named in the deliverables; the raw pulls in _evidence keep the source values"""
    if isinstance(o, dict): return {k: ("[masked]" if k in MASK_KEYS and v not in (None, "", " ") else mask(v)) for k, v in o.items()}
    if isinstance(o, list): return [mask(x) for x in o]
    return o
pl = load("point_layers_306troy.json")
if isinstance(pl, dict) and "error" not in pl:
    for k, v in pl.items():
        rec("point_layers", k, json.dumps(mask(v))[:900])
rec("point_layers", "none_at_the_point", "Trakit 1 Planning BMPs, 5 Flood Reduction Easements, 8 Flood Hazard Areas, 9 River and Creek Corridor, 11 Sign Overlay, 12 Design Overlay, 14 Historic Districts, 16 Conservation Rehabilitation, 17 Rental Inspection Districts; Rental_Inspection/0; Historic_Districts/0; National_Register/0 and /1; Conservation_Rehab/0; Design_Overlay/0; Sign_Overlay/0; Neighborhood_Design_Districts/0; Flood_Zones/1; FloodPlain/1; FEMA/0-3; FEMA_Planning/0 Floodway; Special_Flood_Hazard_Areas/1; Preliminary_FEMA_Layers/0; River_Creek_Corridor/0; Easements/0; Easements_Access/0-2; Easements_Flood_Stormwater/0-2; Easements_Utilities/0; LeadSafe_public/0; HUD_Qualified_Census_Blocks/0; Opportunity_Zones/0; Enterprise_Zones/0; Service_Districts/0-1; Stormwater/0,1,3; Stormwater_Enviro_Mgmt/0-1; VDOT_Chapter_527/0; Hydrology/0-1 (40 m); Parcels_MultiFam/0")
im = load("impervious_2026_parcel.json")
for f in im.get("features", []):
    a = f["attributes"]; rec("impervious_2026", a.get("SURFACE", ""), f"IMPERV_AREA {round(a.get('IMPERV_AREA', 0), 1)} sf; TYPE {a.get('TYPE')}; STATUS {a.get('STATUS')}; SOURCE {a.get('SOURCE')}; BldgID {a.get('BldgID', '')}")
rec("impervious_2026", "total", f"{IMPERV_SF} sf = {IMPERV_SF/500:.2f} units -> {STORM_UNITS} billing units x $18.60 = ${STORM_FEE:.2f} a year at $1.55")
w = load("wvwa_water_mains_60m.json")
for f in w.get("features", []):
    a = f["attributes"]; rec("wvwa_water_60m", a.get("INFONETID", ""), f"{a.get('DIAMETER')}-inch {a.get('MATERIAL')} installed {ms(a.get('INSTALLDATE'))}; TYPE {a.get('TYPE')}; status {a.get('OPERATIONAL_STATUS')}; HGL {a.get('HGL')}")
s = load("wvwa_sewer_60m.json")
for f in s.get("features", []):
    a = f["attributes"]; rec("wvwa_sewer_60m", str(a.get("INFONETID") or a.get("OBJECTID")), "; ".join(f"{k}={ms(v) if 'DATE' in k.upper() and isinstance(v, (int, float)) else v}" for k, v in a.items() if v not in (None, "", " ") and not k.startswith("Shape")))
rec("street", "Troy Ave NE", "Streets/0 and Transportation_Streets/0: FULL_NAME TROY AVE NE, CARTO_CLASS Local, 25 mph, block 300-332 left / 301-333 right, ZIP 24012 both sides, locality CityofRnke")
st = load("troy_ave_ne_street_roll.json")
for f in sorted(st.get("features", []), key=lambda f: int(f["attributes"]["LOCADDR"].split()[0]) if f["attributes"]["LOCADDR"].split()[0].isdigit() else 0):
    a = f["attributes"]
    rec("street_roll", a.get("LOCADDR"), f"{a.get('PROPERTYDE')}; {a.get('ZONEDESC')}; 2026 ${a.get('TOTALVAL1'):,} (land ${a.get('LANDVAL1'):,}); last transfer {ms(a.get('SALEDATE1'))} ${a.get('SALEAMT1') or 0:,}; owner mail {a.get('MAILCITY')} {a.get('MAILSTATE')}; {a.get('ACRES')} ac")
rec("duplex_cohort", "method", "Parcels/0 where PROPERTYDE='Multi-Family Duplex' (967 parcels, paged); last transfer per parcel on or after 2024-01-01 with SALEAMT1 $50,000 to $600,000 (120); same-date same-amount packages removed (89); ratio = SALEAMT1 / TOTALVAL2 (the 2025 assessment); full rows in records_2026-09-30/duplex_cohort_since2024.csv")
rec("duplex_cohort", "all_single_parcel", "n=89; median $215,000; median sale/2025 assessment 1.18; share at or under 0.95: 0.17")
rec("duplex_cohort", "2025_2026", "n=58; median $213,500; 1.21; 0.16")
rec("duplex_cohort", "north_side_nbhd_11_17_22", "n=21; median $230,000; 1.15; 0.24")
rec("duplex_cohort", "neighborhood_15", "n=1: 521 Fleming Ave NE, 2025-04-22, $167,500 against $192,800 (0.87); 2026 assessment $192,800 (unchanged); 0.2067 ac")
rec("duplex_cohort", "2026_sales_north_side", "137 Princeton Cir NE 3/26 $255,000 (2025 assessment $201,600); 4524 Ohio St NE 3/26 $265,000 ($196,500); 4504 Pennsylvania Ave NE 4/1 $325,000 ($218,000); 330 Maddock Ave NE 4/23 $215,000 ($182,800); 3102 Angell Ave NW 9/1 $252,500 ($203,800)")
rec("class_layers", "Parcels_Duplexes", "TAXID 3180117 present (LOCADDR 306 TROY AVE NE, Multi-Family Duplex, neighborhood 15); Parcels_MultiFam: absent (126 TROY AVE NE, 3180105, 300-Multifamily, is present there)")
rec("airport_overlay", "county_feature", "Roanoke County 'Airport Overlay' (Airport_Overlay_Hosted/FeatureServer/0): one polygon named 'Airport' contains the parcel point; the city's GIS publishes no airport overlay; the 2024 amendment PDF does not touch 36.2-330 (AD); the AD text was not retrieved")
rec("permits", "ZVBL21-0310", "Tax ID 3180117; 308 TROY AVE NE; RECORDID PLSS:210506020208704 (2021-05-06); the only permit on the parcel; detail view login-gated")
rec("permits", "ZVBL21_series_sample", "ZVBL21-0300 154 Monterey Ave NE (PLRC:210430...); 0301 1730 Lonna Dr NW; 0302 321 Houston Ave NE; 0303 5202 Morwanda St NW; 0304 1613 Williamson Rd NE; 0305 307 TROY AVE NE (PLSP:210505...); 0306 401 Gainsboro Rd NW; 0307 5220 Williamson Rd NW STE A; 0308 1938 Hope Rd SW; 0309 401 Luck Ave SW; 0311 4009 Williamson Rd NW; 0313 3215 Hillcrest Ave NW APT 104; 0318 805 Elm Ave SE APT B; 0319 1660 Rugby Blvd NW (5/12/2021)")
rec("permits", "ZVBL26_series_sample", "ZVBL26-0001 306 Trinkle Ave NE (PLRB:260102...) through 0012 4419 Pheasant Ridge Rd SW STE 202 (1/7/2026): the series restarts each January and runs about three a day")
rec("permits", "street_corpus_page1", "20 rows (grid page size): LIND17-0003 and ROW17-0075 (block, 2017); 106 Troy E090470, RELE21-0035, RMEC20-0191, ROW17-0021, RPLB22-0187; 107 Troy M050069, PLB25-0221; 111 M030545; 112 P140094, RMRP18-0042; 115 P020696; 116 M040063, SP060225, Z060888; 121 ELE24-0647, PLB24-0323; 122 E070100, ELE25-0623. Prefix decode: R+ELE/MEC/PLB/MRP residential electrical, mechanical, plumbing and (repair or roof, assumption); legacy E/M/P/B/Z + two-digit year (advisory 36)")
rec("code_cases", "AV20-0638", "INOPERABLE VEHICLE; Tax ID 3180117; 308 TROY AVE NE; RECORDID CRW:2009220958483594 (2020-09-22); the only case on the parcel")
rec("code_cases", "street", "106 Troy: AV060301, AV060302, AV060303, AV061818 (2006), AV080602 (2008), all INOPERABLE VEHICLE; nothing else on the first page")
rec("etrakit_method", "postback", "GET the search page, submit every input and select on the form with __EVENTTARGET=ctl00$cplMain$btnSearch, ddSearchBy (Permit_Main.SITE_APN / Case_Main.SITE_APN / PERMIT_NO / SITE_ADDR), ddSearchOper (EQUALS / BEGINS WITH / CONTAINS), txtSearchString, ddlSelLogin=Public, with the session cookie, Origin and Referer headers; a partial field set answers 302 to etrakitError.aspx; the results grid pages at 20 rows; detail views are login-gated")
rec("tax_history", "redfin_9_30", "2025 $2,649 on $192,100 (36,600 + 155,500); 2024 $2,495 on $180,000 (31,900 + 148,100); 2023 $2,148 on $152,300; 2022 $2,044 on $152,300; 2021 $1,800 on $144,500; 2020 $1,773 on $125,200; 2019 $1,730 on $125,200; 2018 $1,730 on $121,600; 2017 $1,538 on $121,600; 2016 $1,537 on $121,600; 2014 $1,529 on $127,000")
rec("tax_history", "reconciliation", "2025: 192,100 x 0.0122 = 2,343.62 + 218.40 solid waste + 87.00 stormwater (5 units x $17.40) = 2,649.02; 2024: 180,000 x 0.0122 = 2,196.00 + 218.40 + 80.60 (5 x $16.12) = 2,495.00")
rec("rates", "fy2027_tax", "$1.22 per $100 held (council 5-2, 5/11/2026; $421.5 million; $18 million deficit; about 30 positions; $50.4 million capital removed) - Cardinal News 5/12/2026; roanokeva.gov/1837")
rec("rates", "solid_waste", "$109.20 single-family; $218.40 for properties with more than one home; on the real estate tax bill fall and spring; 10 percent penalty and 10 percent yearly interest - roanokeva.gov/480 (9/30)")
rec("rates", "stormwater", "$1.55 a month per billing unit (500 sf impervious, rounded to the nearest whole); residential credit up to 50 percent - roanokeva.gov/1843 (9/30)")
rec("rates", "pmms", "30-year 7.03 percent on 9/24/2026 (9/17 6.95; 9/10 6.76); the triple 6.75 / 7.40 / 8.00 unchanged")
rec("rates", "rrha_hcv", "'Due to budget constraints, RRHA's HCV/Section 8 program will pause issuing new vouchers until further notice'; application process closed - rkehousing.org/housing-options/section-8/ (9/30); payment standards not on the page")
cr = load("censusreporter.json")
if "data" in cr:
    for geo, label in (("14000US51770000400", "tract_4"), ("05000US51770", "roanoke_city")):
        g = cr["data"][geo]
        def v(t, c): return f"{g[t]['estimate'].get(c)} (+/-{g[t]['error'].get(c)})"
        rec("acs_2020_2024", label, f"B25064 gross rent {v('B25064','B25064001')}; B25058 contract rent {v('B25058','B25058001')}; B25031 2BR gross {v('B25031','B25031004')}; B19013 MHI {v('B19013','B19013001')}; B25119 renter MHI {v('B25119','B25119003')}; B25003 renters {v('B25003','B25003003')} of {v('B25003','B25003001')}; B25004 vacant for rent {v('B25004','B25004002')}; B17001 poverty {v('B17001','B17001002')} of {v('B17001','B17001001')}")
rec("rents", "zillow_24012_2br_9_28", "average $1,300; MoM -$60; YoY +$201; 40 available; range $850 to $3,360; frequencies $800:1 $900:3 $1,000:4 $1,100:9 $1,200:9 $1,300:7 $1,400:1 $1,500:2 $1,600:3 $1,700:5 $1,800:2 $1,900+:2; COOL; 2026 monthly Jan 1,223 Feb 1,200 Mar 1,217 Apr 1,200 May 1,223 Jun 1,199 Jul 1,400 Aug 1,350 Sep 1,300; 2025 Jan 1,050 ... Dec 1,200")
rec("listing", "redfin_9_30", "Pending; $246,000; listed 9/3/2026; 'Listing updated: Sep 18, 2026 at 10:18am'; 15 days on Redfin, 23 views; MLSRV 931038; Virginia Realty Group; remarks as in the 9/28 sweep (two units of 2BR/1BA, 'Unit 308 has been recently updated', 'convert this property into a single family residence with an in-law suite'); features: heat pump (electric), owner pays trash disposal and property management, two-unit property, duplex (multi-family), built 1984; public record 4 bd 2 ba 2 stories 1,848 sf lot 7,040 sf APN 3180117 'Last updated by owner on Aug 3, 2026'; zoning card RM-1 / AIRPORT / Residential District; First Street flood 1, fire 1, heat 5, wind 2, air 2; schools Monterey 2/10, Breckinridge 2/10, William Fleming 1/10 (GreatSchools)")
rec("sweep", "tracked_9_28", "status PENDING; status_date Sep 18, 2026; price 246000; dom 15; history 'Sep 18, 2026 Pending; Sep 3, 2026 Listed $246,000'; built 1984; tax_year 2025 tax_annual 2649; flood 1; photo 931038_0.jpg; tracked_changes 'no change | PENDING dom 15'")
rec("sweep", "gate5_multipliers_9_28", "440 tract-rent rows with a rent-to-price: passes at x1.0 125, x0.83 76, x0.73 54; ENTRANTs 1611 Floyd St ($119,000, rent $2,018 tract x 2, r2p 1.70, CoC 20.3, DSCR 2.09), 1006 Faison St E ($99,999, $1,508, 1.51, 14.7, 1.79), 4 12 1/2 St SW ($158,122, $1,922, 1.22, 6.6, 1.35)")
rec("sweep", "tract_model", "tract_scores_x1.0.json['51770000400']: median_rent 1133.0; annual_gross_rent 27192.0 (= median_rent x 24); gate PASS; tier 1; median_hh_income 47045")
rec("photos", "hashes", "23 files, 23 distinct SHA-256 (records_2026-09-30/photo_sha256_23_frames.json); front 931038_0 6f16494b...; rear 931038_19 b9661525...; plans 931038_21 d3cf384b... and 931038_22 5b8ff3a5...")
rec("photos", "read_9_30", "frames 1-2 living room of the unit with stainless appliances (ceiling registers, front door, stair); 3-5 its kitchen and eat-in area (electric coil range, dishwasher, floor-level return grille on the laundry closet wall, no ceiling panel); 6-7 its primary bedroom (ceiling fan, long baseboard-type unit under the window); 8 its second bedroom (same); 9 its bath (floor-level wall supply register, single-hung window, original vanity); 10-12 the other unit's living room (ceiling register, surface-wired digital thermostat, baby gate, air purifier); 13-15 its kitchen (white refrigerator, electric coil range, black dishwasher, worn cabinet edges, square ceiling access panel, return grille); 16 its primary bedroom (long unit under the window); 17 its bunk-bed room (floor-level wall supply register); 18 its bath; 19 rear (condenser, meter base, two disconnects, mildew streaking on the upper vinyl, concrete pad, weathered fence); 20 front; 21-22 Cubicasa plans; 0 front")
rec("assessor_photo", "3180117-1.jpg", "dated 5/1/2026 10:46:27 AM: left-front elevation, gravel drive along the left side, satellite dish on the left wall, a car in the drive, the neighbor's white vinyl fence on the right; roof not visible")
rec("aerials", "esri_and_city_2021", "ESRI World Imagery export (leaf-off) and the city's 2021 Pictometry export: gray shingle gable roof, ridge parallel to Troy Ave, no patches or tarps visible; gravel drive on the left, a second drive to the rear pad on the right; fenced rear yard; single-family houses on both sides")
for g in GRID:
    rec("underwriting_at_ask", f"rent_{g['rent_per_unit']}", json.dumps(g))
rec("underwriting_at_ask", "constants", f"price {PRICE:,}; tax year one {TAX_Y1:,} (assessed {ASSESSED_2026:,} x 1.22 percent + {SOLID_WASTE} + {STORM_FEE:.2f}); tax long run at the ask {TAX_LONGRUN_ASK:,}; insurance {INS}; owner-paid 0; K 6.75 {K675:.6f}, 7.40 {K740:.6f}, 8.00 {K800:.6f}; debt service {0.75*PRICE*K675:,.0f} / {0.75*PRICE*K740:,.0f}; cash in {0.3125*PRICE:,.0f}; rent needed at the ask for 8 percent {RENT_NEEDED_8PCT:,}; comp center at long-run tax: CoC {COC_CENTER_LR} DSCR {DSCR_CENTER_LR}; sensitivities on the 8 percent price: vacancy 7.5 percent {SENS_VAC75:+,}, owner-paid water $800 {SENS_WATER800:+,}")
rec("transports", "served", "city GIS (Parcels, TRAKiT 0-21, Zoning, Real_Estate class layers, WVWA water and sewer, Impervious_Surface_Final_2026, Streets, Schools, district layers, Imagery_Pictometry_2021 export) by plain urllib and curl; eTrakit permit and case searches by scripted full-field postback (curl); Census Reporter by curl (the batch tract sample then 403); Freddie Mac PMMS by curl; the 2024 zoning amendment PDF by curl + pymupdf; Redfin listing via Bright Data djnicholasq; Zillow trends via Bright Data ajumobinicholasY; roanokeva.gov fee, budget and crime-mapping pages, Cardinal News, VDH and rkehousing.org by WebFetch; the county Airport Overlay hosted feature service by urllib; ESRI World Imagery export by curl; Dropbox connector (list, download links) for the live campaign files; the 23 frames by the Read tool with Pillow crops")
rec("transports", "failed_or_not_retrieved", "westernvawater.org rates, backup and service-line pages (403 to WebFetch and curl; empty body via Bright Data bjumobinicholasY); WVWA service line inventory web app (private ArcGIS item, 403); EPA Virginia radon zone list (403); sosradon fact sheet (404); municode 36.2-330 (script-rendered, empty); Engineering_CIP within 500 m (no features); WVWA_Sewer (HTTP 500 on three calls, served on the fourth); TRAKiT layer 22 (HTTP 400, as the advisory found); Census Reporter batch call (403 after the first call served); eTrakit detail views (login-gated by design); RRHA payment standards (not on the HCV page; the 2026 annual plan PDF carries policy text only); the assessor photo -2 and -3 (404); pdftotext and pypdf unavailable in the container (pymupdf used)")
rec("transports", "not_done", "Roanoke Circuit Court land records (instrument 180011508; subscription); CityProtect incident query; ROA Part 150 noise map; the Williamson Road Area plan text; an appraiser's or insurer's read; the manager's identity")

# ---------------------------------------------------------------- write 68a and 68b
with open(OUT68A, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(L[0].keys()), lineterminator="\r\n"); w.writeheader(); w.writerows(L)
with open(OUT68B, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=["section", "item", "record"], lineterminator="\r\n"); w.writeheader(); w.writerows(RS)
from collections import Counter
print("68a rows:", len(L), dict(Counter(r["status"] for r in L)))
print("68b rows:", len(RS))

# ---------------------------------------------------------------- file 14 row 28
rows, bom, term = read_csv_bytes(F14)
hdr = rows[0]; idx = {h: i for i, h in enumerate(hdr)}
NOVICE = ("GREEN-verify: C3 in 23 MLS frames (exterior C3; the updated unit, 308 per the remarks, C3 with new paint and appliances over 1984 cabinets, laminate and sheet vinyl; "
          "the other unit C3 to C4); built 1984, no RED item; roof covering, heat pump and water heater ages, supply-pipe material (polybutylene era), the kitchen ceiling access panel "
          "under the bath in the other unit, and whether the long units under the bedroom windows are diffusers or electric baseboards unconfirmed (9/30)")
EVENT = "pending since 2026-09-18 at the full $246,000 list price after 15 days, no cuts (Redfin 9/29 and 9/30; MLSRV 931038); the sweep first saw it pending on 2026-09-21"
NOTE = (f"9/30 (round 20, advisory 73): PARK, P 0.01, out of the review queue under memo 67 6.1; relist tripwire: ACTIVE again after a contract failure, or any list price at or under $198,000, "
        f"then send the 67a asks the same day and offer in writing at the 8% price on the documented roll ($134,000 to $198,000 by rent and rate; $187,000 / $179,000 at the $1,150 comp center). "
        f"Gate 3 PASS on city record: Multi-Family Duplex class, present in the Parcels_Duplexes layer, building use Duplex (1984), 911 points 306 and 308 ACTIVE and field verified, RM-1 not conditional; "
        f"two-family is a by-right use in RM-1 before and after the 2024 reform; lot 7,040 sf with about 76 ft of frontage clears both dimensional tables. Gate 5 marginal (0.89 to 0.98% on $1,100 to $1,200 asking comps); "
        f"Gate 6 FAIL at the ask on every basis (needs $1,433 a unit). Tax year one ${TAX_Y1:,} (assessed $199,900 x 1.22% + solid waste $218.40 + stormwater 5 units $93; FY2027 rate held 5/11/2026); "
        f"long run at the ask about ${TAX_LONGRUN_ASK:,} (annual reassessment); no separate trash line. Insurance $1,500; water metering unknown (one owner-paid meter at ~$800/yr takes ~$10,000 off the 8% price). "
        f"Rent basis: asking comps $1,100 to $1,200 (Zillow 24012 2BR average $1,300 on 9/28, modal $1,100 to $1,200); ACS tract 4 contract rent $923 as the in-place floor; documented roll unknown; the $1,133 tract gross figure retired. "
        f"eTrakit: one permit, ZVBL21-0310 (5/6/2021 at 308; read as a business-licence zoning verification; records request drafted in 67a), no mechanical, electrical, plumbing or building permit on the parcel; "
        f"one code case, AV20-0638 inoperable vehicle (9/22/2020). Overlays none; preliminary FIRM Zone X; the MLS AIRPORT tag is the airport overlay (the county's polygon covers the parcel; height only). "
        f"RRHA paused new vouchers (9/30). Owner: an out-of-town family living trust with a manager. Ledger 68a, record set 68b. | rent basis: asking comps")
hit = 0
for r in rows[1:]:
    if r[idx["i"]] == "28" and r[idx["address"]].startswith("306 & 308 Troy"):
        r[idx["status"]] = "PENDING (2026-09-18)"; r[idx["event"]] = EVENT; r[idx["score"]] = "-5.4"; r[idx["coc_6.75"]] = str(COC_CENTER_675); r[idx["dscr"]] = str(DSCR_CENTER_675)
        r[idx["novice"]] = NOVICE; r[idx["note"]] = NOTE; hit += 1
if hit != 1: raise SystemExit(f"HALT: file 14 row 28 matched {hit} rows")
write_csv_bytes(F14, rows, bom, term); print("file 14 row 28 patched")

# ---------------------------------------------------------------- 67a asks register: append seven rows
rows, bom, term = read_csv_bytes(F67A)
hdr = rows[0]; have = {(r[0], r[2]) for r in rows[1:]}
P = "0.01 (9/30), PARK"
ASKS = [
    ("Both current leases and a 12-month rent ledger for 306 and 308, with deposits held, lease end dates and any housing-voucher contract", "property manager (the owner pays management) or the listing agent", "kills or clears Gate 6 (computed on the documented roll)", "send only if the listing returns to ACTIVE; 8% price $140,000 at $923 a unit to $198,000 at $1,200 (6.75); $134,000 to $189,000 (7.40)"),
    ("Water and sewer accounts with the Western Virginia Water Authority: one meter or two, who pays, and the last 12 bills", "property manager or listing agent", "sets the owner-paid line", "one shared owner-paid meter at about $800 a year (assumption) lowers the 8% price by about $10,000; the Authority's inventory map is a browser-only check"),
    ("Roof covering age and any replacement invoice", "listing agent", "file 08 bid cap", "not visible in the 23 frames; aerials show a uniform gray shingle gable, age unreadable; no roof permit is expected in the record"),
    ("Data-plate photos of both heat pumps, both air handlers and both water heaters (model, serial, refrigerant); whether the second floor is on the heat pump duct and whether the units under the bedroom windows are diffusers or electric baseboard heaters", "listing agent or property manager", "file 08 bid cap", "no mechanical permit on the parcel since the record began; one condenser visible (2000s-2010s cabinet, assumption); a retrofit thermostat in one unit; units before 2010 likely R-22 (assumption)"),
    ("Supply-pipe material (gray pipe marked PB-2110 at the water heaters or under sinks), electrical panel make and model, and the reason for the access panel in the kitchen ceiling under the bath (the unit with the white appliances)", "listing agent now; home inspector at contract", "insurance appetite and file 08 bid cap", "1984 sits in the polybutylene era (1978 to 1995); no disclosure duty; the panel is confirmed in frames 13 to 15"),
    ("Sewer camera scope of the lateral to the main, and a radon test in each unit", "home inspector at contract", "file 08 bid cap", "clay collectors dated 1940 and 1949 (WVWA layer); Roanoke County on the VDH Zone 1 list; the lateral ownership rule was not retrieved"),
    ("Records request to the City of Roanoke Permit Center for permit ZVBL21-0310 (5/6/2021, 308 Troy Ave NE): the use verified and the applicant type", "city or town office", "clears Gate 3 in writing if the verification was for rental of real estate; costs nothing", "can be sent before any relist (no agent time); the eTrakit detail view is login-gated; ZVBL21-0305 was issued at 307 Troy the day before"),
]
added = 0
for ask, addressee, kills, note in ASKS:
    if (PROP, ask) in have: continue
    rows.append([PROP, P, ask, addressee, "73a (rows 1-6) / 68 (row 7)", "2026-09-29" if not ask.startswith("Records request") else TODAY, "", "", "", "", kills, note]); added += 1
write_csv_bytes(F67A, rows, bom, term); print("67a rows appended:", added)

# ---------------------------------------------------------------- 32b Roanoke row
rows, bom, term = read_csv_bytes(F32B)
hdr = rows[0]; idx = {h.lstrip("\ufeff"): i for i, h in enumerate(hdr)}
EXT = {
    "real_estate_tax_rate": " | FY2027 held at $1.22 (council 5-2, 5/11/2026; round 20)",
    "rate_source_and_fy": " | Cardinal News 5/12/2026 and roanokeva.gov/1837, read 9/30/2026 (round 20)",
    "lead_service_line_inventory": " | round 20 (9/30): the inventory web app is a private ArcGIS Online item (403 to the REST API); browser only",
    "zoning_code_status": " | round 20 (9/30): two-family is permitted by right in RM-1 under both the pre-2024 use table ('Dwelling, two-family' P) and the 9/16/2024 readoption ('Dwellings' P, 36.2-409.1); the RM-1 dimensional tables old (5,000 sf, 3,500 per unit, 50 ft) and new (4,000 sf, 1,500 per dwelling, 40 ft) both clear a 7,040 sf lot; a rollback would not disturb a side-by-side two-family on one lot",
    "duplex_permission_summary": " | 306-308 Troy (round 20): Multi-Family Duplex class, present in Real_Estate/Parcels_Duplexes, building use Duplex, two 911 points; permit ZVBL21-0310 (2021) read as a business-licence zoning verification",
    "superfund_or_environmental": " | 306-308 Troy: Zone X on the preliminary FIRM 51161C, Tinker Creek watershed, outside LeadSafe and HUD QCB (round 20)",
    "board_rows_affected": " | 28 Troy (306-308) outside the districts, PARK (round 20); Roanoke fee stack: the tax bill carries solid waste ($218.40 for more than one home) and stormwater ($1.55 a month per 500 sf unit, rounded), so no separate trash line; RRHA paused new vouchers 9/30",
    "verified_on": "; Roanoke row extended 2026-09-30 (round 20)",
    "source_links": "; https://trakit.roanokeva.gov/etrakit/Search/permit.aspx (scripted full-field postback); https://maps.roanokeva.gov/arcgis/rest/services/Real_Estate/Parcels_Duplexes/MapServer/0; https://www.roanokeva.gov/480/Solid-Waste-Fees-and-Enforcement; https://www.roanokeva.gov/1843/Storm-Utility-Fee-and-Credits; https://cardinalnews.org/2026/05/12/roanoke-budget-approved-by-5-2-vote-the-second-consecutive-year-of-significant-cuts/; https://rkehousing.org/housing-options/section-8/; https://services1.arcgis.com/VlZ73DcE2ya6FnSK/arcgis/rest/services/Airport_Overlay_Hosted/FeatureServer/0",
}
hit = 0
for r in rows[1:]:
    if r[idx["jurisdiction"]] == "Roanoke" and r[idx["state"]] == "VA":
        for k, v in EXT.items():
            if "(round 20" in r[idx[k]] or "round 20" in r[idx[k]]: continue
            r[idx[k]] = r[idx[k]] + v
        hit += 1
if hit != 1: raise SystemExit(f"HALT: 32b Roanoke row matched {hit}")
write_csv_bytes(F32B, rows, bom, term); print("32b Roanoke row extended")

# ---------------------------------------------------------------- constants.json
cb = open(CONST, "rb").read(); term_c = "\r\n" if cb.count(b"\r\n") else "\n"
C = json.loads(cb.decode("utf-8"))
C["advisory_73_rules_adopted"] = {
    "_note": "Adopted 2026-09-30 (round 20, 306-308 Troy Ave NE Roanoke; advisory 73/73a/73b/73c written to memo 67's brief form). Verdict PARK, P 0.01, relist tripwire reproduced.",
    "roanoke_tax_bill_rule": "Roanoke real estate tax bills carry the solid waste fee and the stormwater fee; model tax = assessed x 0.0122 + $218.40 (more than one home) + stormwater units x $18.60; never add a separate trash line (73c suggestion roanoke-fee-double-count, verified on the 2025 bill: 2,343.62 + 218.40 + 87.00 = 2,649.02).",
    "stormwater_units_rule": "billing units = impervious sf on the parcel (Impervious_Surface_Final_2026 layer, parcel-polygon query) / 500, rounded to the nearest whole; 2,295 sf = 5 units = $93.00 a year at $1.55 (FY2027); the rate has stepped about $0.10 a year ($1.34 -> $1.45 -> $1.55, from the 2024 and 2025 bills).",
    "status_date_rule": "file 14 carries the MLS status date from the history line, not the sweep date that first saw it (73c suggestion status-date, applied to row 28 by hand; the refresh stage still stamps the sweep date: pipeline note).",
    "roanoke_prior": "Roanoke duplexes trade at a median 1.18 x the prior-year assessment (1.21 in 2025-26; north side 1.15); the campaign's 8 percent bar needs about 0.94 x; about one transfer in six closes at or under 0.95 x, several of them not arm's length. Read Roanoke as a distress-or-mispricing market for the bar (73c suggestion roanoke-prior; constants.roanoke_duplex_market).",
    "vacancy_by_city": "NOT adopted this round: Roanoke's ACS rental vacancy is 7.5 percent (5.7 to 9.4) against the 5 percent constant; a per-city constant from B25004 and B25003 would move every VA row; flagged for Najum (73c suggestion vacancy-by-city).",
    "sweep_rent_basis": "NOT applied: see sweep_rent_basis_finding (pipeline DEFECT 4, for Najum's decision).",
    "gate3_reading": "a two-family building on one lot in Roanoke RM-1 is a by-right use under both the pre-2024 use table and the 2024 readoption; the city's Real_Estate/Parcels_Duplexes layer is a third-party-readable duplex classification (306-308 Troy present; 126-128 Troy absent).",
    "photo_dating": "the photographer's front photo on the TV in both units dates all interiors to the same 2026 shoot (advisory 73 section 2.1; reproduced in frames 1, 2, 6, 10, 11, 17).",
}
C["roanoke_instruments"] = {
    "_note": "Roanoke record recipes verified 2026-09-30 (round 20); every endpoint served plain urllib or curl unless noted.",
    "parcels": "https://maps.roanokeva.gov/arcgis/rest/services/Public/Parcels/MapServer/0/query?where=TAXID='<taxid>' (fields TAXID, LRSN, LOCADDR, OWNER, MAILCITY, LEGALDESC, ZONEDESC, PROPERTYDE, LANDVAL1/2, TOTALVAL1/2 (1 = current year), DWELLINGVA/DWELLING_1, SALEDATE1/2, SALEAMT1/2, DOCNUM1, NEIGHBORHO, SQFT, ACRES); PROPERTYDE='Multi-Family Duplex' lists 967 parcels (page with resultOffset)",
    "class_layers": "Real_Estate/Parcels_Duplexes, Parcels_MultiFam, Parcels_Residential, Parcels_Apartments, Parcels_Commercial (MapServer/0, TAXID): the Duplexes layer is the Gate 3 class test",
    "trakit": "Public/Trakit_20221221/MapServer: 0 Addresses (ADDR_ID, TAX_ID, STATUS, VERIFIED, Site_NGUID, Condo), 4 Buildings (PIN, BldgID, UseDesc, YrBuilt, FinSize, Foundat, HeatDesc, CentrlAC, NumBdRms, Num3Baths, CondDesc, Asbestos), 6 Parcels, 7 HUC6, 10 Sub Watersheds, 13 Development Inspection Zones, 15 Zoning, 17 Rental Inspection Districts, 18 Building Inspection Zones, 19 Code Enforcement Zones, 20/21 Census; 22 (2017 imagery) refuses queries",
    "impervious": "Public/Impervious_Surface_Final_2026/MapServer/0 queried with the parcel polygon (esriGeometryPolygon, inSR 4326): SURFACE, IMPERV_AREA per polygon; sum / 500 rounded = stormwater billing units",
    "utilities": "Public/WVWA_Water/MapServer/0 and Public/WVWA_Sewer/MapServer/0 (mains only; INSTALLDATE, DIAMETER, MATERIAL); the sewer layer answered HTTP 500 three times then served; no meters or laterals anywhere public",
    "etrakit": "https://trakit.roanokeva.gov/etrakit/Search/permit.aspx and case.aspx: GET, then POST every input and select on the form with __EVENTTARGET=ctl00$cplMain$btnSearch, ctl00$cplMain$ddSearchBy=Permit_Main.SITE_APN (or Case_Main.SITE_APN, Permit_Main.PERMIT_NO, ..SITE_ADDR), ddSearchOper=EQUALS|BEGINS WITH|CONTAINS, txtSearchString, ddlSelLogin=Public, with the session cookie and Origin/Referer; a partial field set answers 302 to etrakitError.aspx; the grid pages at 20 rows; detail views login-gated; record ids encode the date (PLSS:YYMMDD..., CRW:YYMMDD...)",
    "permit_prefixes": "legacy E/M/P/B/Z/SP + two-digit year + sequence (2002-2016 conversion records); modern RELE/RMEC/RPLB/RMRP residential trades, ELE/PLB/MEC, ROW right of way, LIND (block-level, 2017), ZVBL = zoning verification for a business licence (moderate decode: about 800 a year, restarts each January, suites, apartments and dwellings)",
    "imagery": "Public/Imagery_Pictometry_2021/MapServer/export?bbox=<lon,lat,lon,lat>&bboxSR=4326&imageSR=3857&size=1000,800&format=jpg&f=image (served); ESRI World_Imagery export the same way; assessor photo https://maps.roanokeva.gov/img_photoshare/<first 3 digits>/<taxid>-1.jpg (dated; -2 and -3 404)",
    "fees": "https://www.roanokeva.gov/480/Solid-Waste-Fees-and-Enforcement ($109.20 / $218.40); https://www.roanokeva.gov/1843/Storm-Utility-Fee-and-Credits ($1.55 a month per 500 sf unit, rounded; 50 percent residential credit); tax rate: council adoption in May (FY2027 $1.22 held 5/11/2026)",
    "airport_overlay": "the city publishes no airport overlay layer; Roanoke County's Airport Overlay hosted feature (services1.arcgis.com/VlZ73DcE2ya6FnSK/.../Airport_Overlay_Hosted/FeatureServer/0) contains the Preston Park parcels; the city AD district (36.2-330) is a height and obstruction overlay (text not retrieved; municode is script-rendered)",
    "crime": "CityProtect map from roanokeva.gov/334 (hundred-block, no download); no incident layer in the city GIS; CrimeGrade ZIP letter remains the measure",
    "vouchers": "rkehousing.org/housing-options/section-8/: HCV new vouchers paused, applications closed (9/30/2026); payment standards not published on the page",
    "not_public": "WVWA rates and lateral rule (westernvawater.org 403 to plain fetches, empty via Bright Data); the WVWA service line inventory app (private ArcGIS item); Circuit Court land records (subscription); eTrakit detail views",
}
C["roanoke_duplex_market"] = {
    "_note": "City parcel layer, class Multi-Family Duplex, last transfer per parcel on or after 2024-01-01, $50,000 to $600,000, same-date same-amount packages removed; ratio to the 2025 assessment (TOTALVAL2). Computed 2026-09-30; advisory 73 (9/29) reproduced to the decimal.",
    "parcels_citywide": 967, "sales_since_2024_in_band": 120, "single_parcel": 89,
    "all": {"n": 89, "median_price": 215000, "median_sale_to_2025_assessment": 1.18, "share_at_or_under_0.95": 0.17},
    "2025_2026": {"n": 58, "median_price": 213500, "median_sale_to_2025_assessment": 1.21, "share_at_or_under_0.95": 0.16},
    "north_side_nbhd_11_17_22": {"n": 21, "median_price": 230000, "median_sale_to_2025_assessment": 1.15, "share_at_or_under_0.95": 0.24},
    "neighborhood_15": {"n": 1, "sale": "521 Fleming Ave NE 2025-04-22 $167,500 against $192,800 (0.87); 2026 assessment unchanged at $192,800"},
    "bar": "the 8 percent price on two units at the 24012 comp center sits at about 0.94 x assessment; at the city's median duplex price ($215,000) two units at $1,150 yield about 4.9 percent cash-on-cash at 6.75 (advisory 73 section 3.3, reproduced by the formula)",
    "rows": "carry the prior on Lafayette (r4), Penmar (r4), Albemarle (r4), Richland (12), Hillcrest (23), 126-128 Troy (18), 306-308 Troy (28), 4 12 1/2 St SW (9/28 entrant)",
}
C["sweep_rent_basis_finding"] = {
    "_note": "Logged 2026-09-30 (advisory 73 section 3.1, load-bearing; pipeline DEFECT 4). NOT applied: the change touches the four regional routines rebuilt on 9/28 and the calibration of memos 63 to 65; Najum decides.",
    "finding": "weekly_sweep.py lines 169 and 249 price an unstated rent at units x tract median_rent; the tract model's median_rent is ACS B25064 median GROSS rent (tenant-paid utilities included), not B25058 contract rent (the model's own field annual_gross_rent = median_rent x 24; tract 51770000400: 1,133 gross against 923 contract).",
    "evidence": "advisory: 25 of 25 sampled passing tracts equal B25064; contract to gross median 0.83 (0.31 to 1.00), gap median $213; the campaign's seven documented rolls ran a median 0.73 of the sweep figure. Local: the 9/28 NC-VA scored file reproduces exactly: 440 tract-rent rows, Gate 5 passes 125 at x1.0, 76 at x0.83, 54 at x0.73; ENTRANTs Floyd St 20.3 -> 12.3 / 7.6, Faison St E 14.7 -> 7.6 / 3.4, 4 12 1/2 St SW 6.6 -> 0.9 / -2.5.",
    "proposed_patch": "add constants.rent_basis_multiplier (0.83, with a per-state or per-region override) and apply it at both lines when the rent is modelled, label rent_basis 'tract contract-rent proxy (gross x 0.83)', keep the gross figure as a ceiling column, flag any stated rent under 0.73 of the modelled figure, and re-screen file 14 rows whose rent_basis is 'tract median x 2'; or rebuild the tract model on B25058 (memo 64's acs_build pulled B25064).",
    "why_not_applied": "the decision boards' SAFMR x 0.83 proxy already carries a deduction of this size; the sweep's does not; changing it halves the Gate 5 pass set and re-bases the area projection (memo 63) and the 9/28 regional folds.",
}
C["inter_rater_log"] = C.get("inter_rater_log", []) if isinstance(C.get("inter_rater_log"), list) else []
if not any(str(e.get("row", "")).startswith("28 306-308") and e.get("date") == TODAY for e in C["inter_rater_log"]):
    C["inter_rater_log"].append({"row": "28 306-308 Troy Ave NE", "date": TODAY, "sweep_grade": "GREEN C2 on the front photo (9/9)", "advisory_blind": "GREEN-verify: exterior C3, updated unit C3, other unit C3 to C4, no RED (23 frames, 9/29)",
                             "local": "GREEN-verify: exterior C3, updated unit C3, other unit C3 to C4, no RED; front photo alone C3 (23 frames, 9/30)", "agreement": "token: agree (GREEN family); C-rating: advisory and local agree on every frame set; the 9/9 front-photo C2 was one step high"})
C["rrha_hcv_status_2026"] = "City of Roanoke Redevelopment and Housing Authority (read 9/30/2026): 'Due to budget constraints, RRHA's HCV/Section 8 program will pause issuing new vouchers until further notice'; the application process is closed; payment standards not on the page. No voucher floor for a new tenancy on any Roanoke row until this lifts."
C["owner_side_municipal_fees"]["Roanoke"]["stormwater_billing_units"] = "impervious sf on the parcel / 500, rounded to the nearest whole (Impervious_Surface_Final_2026 layer, parcel-polygon query); 306-308 Troy 2,295.5 sf = 5 units = $93.00 a year at $1.55 (FY2027); the 2025 bill carried $87 (5 x $17.40 at $1.45); 126-128 Troy 2,982 sf = 6 units"
C["owner_side_municipal_fees"]["Roanoke"]["tax_bill_reconciliation"] = "tax bill = assessed x 0.0122 + solid waste + stormwater; never add a separate trash line (306-308 Troy 2025 bill $2,649 = 2,343.62 + 218.40 + 87.00; adopted 2026-09-30)"
C["tax_assessed_combined_rate"]["Roanoke"]["fy2027_note"] = "FY2027 rate $1.22 held (council 5-2, 5/11/2026; Cardinal News 5/12/2026); annual reassessment tracks sales (306-308 Troy +60 percent since 2020); model tax_year1 on the assessment and tax_longrun at the purchase price when the price exceeds the assessment; a below-assessment sale did not lower the roll (521 Fleming Ave NE, 2025-26)"
g3 = C.get("gate3_two_family_rule", {})
if isinstance(g3.get("applied_to"), dict): g3["applied_to"]["28 306-308 Troy Ave NE Roanoke"] = "PASS 2026-09-30: Multi-Family Duplex class (Parcels_Duplexes layer), building use Duplex 1984, two ACTIVE field-verified 911 points, RM-1 two-family by right pre- and post-2024"
elif isinstance(g3.get("applied_to"), list): g3["applied_to"].append("28 306-308 Troy Ave NE Roanoke: PASS 2026-09-30 (Parcels_Duplexes class, building use Duplex, two 911 points, RM-1 two-family by right pre- and post-2024)")
else: g3["applied_to_0930"] = "28 306-308 Troy Ave NE Roanoke: PASS 2026-09-30 (Parcels_Duplexes class, building use Duplex, two 911 points, RM-1 two-family by right pre- and post-2024)"
C["rate_of_the_week"]["_note_9_30_troy"] = "unchanged: PMMS 7.03 percent (9/24/2026); triple 6.75 / 7.40 / 8.00; advisory 73 used the triple; its six-row grid reproduces to the dollar"
_second = cb.decode("utf-8").split("\n")[1] if "\n" in cb.decode("utf-8") else " "
INDENT = max(1, len(_second) - len(_second.lstrip(" ")))
open(CONST, "wb").write(json.dumps(C, indent=INDENT, ensure_ascii=False).replace("\n", term_c).encode("utf-8"))
json.loads(open(CONST, "rb").read().decode("utf-8"))
print("constants.json updated (indent", INDENT, ")")

# ---------------------------------------------------------------- README lines
def append_line(path, marker, text):
    b = open(path, "rb").read(); t = b.decode("utf-8")
    if marker in t: print("already present:", os.path.basename(path)); return
    term_r = "\r\n" if b.count(b"\r\n") else "\n"
    if not t.endswith(term_r): t += term_r
    t += text.replace("\n", term_r) + term_r
    open(path, "wb").write(t.encode("utf-8")); print("appended:", os.path.basename(path))

cnt = Counter(r["status"] for r in L)
COUNTS = (f"{len(L)} ledger rows: {cnt.get('REPRODUCED',0)} reproduced, {cnt.get('EXTENDED',0)} extended, {cnt.get('CORRECTED',0)} corrected (stormwater 5 units = $93 not $87 so tax year one $2,750; the file 14 status date; the code-case read; the impervious figure; the novice cell), "
          f"{cnt.get('NEW',0)} new (a 2021 ZVBL permit read as a business-licence zoning verification and no mechanical permit ever; the Parcels_Duplexes class; two-family by right in RM-1 before and after 2024; the long-run tax at the ask; RRHA's voucher pause), "
          f"{cnt.get('CARRIED',0)} carried, {cnt.get('OPEN',0)} open, {cnt.get('NOT RETRIEVED',0)} not retrieved, {cnt.get('SUPERSEDED',0)} superseded")
append_line(AREADME, "files 73/73a/73b/73c", "- `2026-09-29 session am`, files 73/73a/73b/73c (306-308 Troy Ave NE Roanoke, file 14 row 28 / 49a id 28; the first package written to memo 67's brief form: a one-page decision brief with the evidence after it, asks in the 67a register columns, a records-and-transport map, a row update, and the blind photo read as an appendix with its hash) - assimilated 2026-09-30 as main files 68/68a/68b (round 20): verdict PARK, P 0.01 and the relist tripwire REPRODUCED; " + COUNTS + ". No board rebase (memo 67 section 6.6): 68a is a long-form claims ledger and file 14 row 28 is the view. The load-bearing campaign finding (the sweep prices unstated rents on ACS GROSS rent) reproduces exactly on the 9/28 files and is logged as pipeline DEFECT 4 for Najum's decision, not applied. The other 9/29 files (67 Bellwood, 68 Saint Andrew, 69 Jefferson, 70 Mt Airy, 71 Richland, 72 Hillcrest, 74 31st St, 75 Albemarle) await assimilation.")

PLINE = f"""## 2026-09-30: advisory round 20 assimilation, 306-308 Troy Ave NE Roanoke (files 68/68a/68b; applied from the cloud session)
- `assimilate_{TAG}.py`: builds 68a (a LONG-FORM CLAIMS LEDGER, memo 67 section 6.6: n, property, attribute, claimed_value, claimed_by, verified_value, source, instrument, date, status, superseded_by, note; 66 rows) and 68b (the record set, 100-plus rows) from the records in `_evidence/306&308 Troy Ave NE Roanoke/records_2026-09-30/`; patches file 14 row 28 (status to the MLS date 2026-09-18, event, score -5.4, coc 1.6, dscr 1.09 at the $1,150 comp center, the novice cell in the memo 66 grammar, the note); APPENDS seven rows to 67a (the six 73a asks plus a records request for permit ZVBL21-0310); extends the Roanoke row of 32b; adds constants `advisory_73_rules_adopted`, `roanoke_instruments`, `roanoke_duplex_market`, `sweep_rent_basis_finding`, `inter_rater_log`, `rrha_hcv_status_2026`, `owner_side_municipal_fees.Roanoke.stormwater_billing_units` and `.tax_bill_reconciliation`, `tax_assessed_combined_rate.Roanoke.fy2027_note`, `gate3_two_family_rule` applied_to, `rate_of_the_week._note_9_30_troy`. Decision board 49a is NOT rebased (memo 67 sections 4.4 and 6.6); its id 28 base columns are recorded in 68a as SUPERSEDED. Backups: `_backup_14_before_{TAG}.csv`, `_backup_67a_before_{TAG}.csv`, `_backup_32b_before_{TAG}.csv`, `_backup_constants_before_{TAG}.json`, `_backup_advisory_README_before_{TAG}.md`, `_backup_README_before_{TAG}.md`. Re-runnable (round-trips the CSVs byte for byte first; skips what is present).
- DEFECT 4 for Najum (advisory 73 section 3.1, reproduced 9/30): `weekly_sweep.py` lines 169 and 249 price an unstated rent at units x tract `median_rent`, and the tract model's `median_rent` is ACS B25064 median GROSS rent (the model's own `annual_gross_rent` = median_rent x 24; tract 51770000400 carries 1,133 gross against 923 contract). On the 9/28 NC-VA scored file: 440 tract-rent rows; Gate 5 passes 125 as scored, 76 at x0.83, 54 at x0.73; the three ENTRANTs were priced on gross x 2. Proposed patch in `constants.sweep_rent_basis_finding` (a `rent_basis_multiplier` of 0.83 at both lines, the basis relabelled 'tract contract-rent proxy', the gross figure kept as a ceiling, stated rents under 0.73 of the model flagged, file 14 'tract median x 2' rows re-screened; or rebuild the model on B25058). Not applied: it halves the Gate 5 pass set and re-bases memos 63 to 65 and the 9/28 regional folds.
- Pipeline note (73c suggestion status-date): the refresh stage writes `PENDING ({{DATE}})` with the sweep date; the detail parse already carries `status_date` ('Sep 18, 2026' for this row). One-line change when Najum approves: use `d.get('status_date')` in the PENDING and CONTINGENT branches as the SOLD branch already does. Row 28 was set to the MLS date by hand.
- Roanoke record recipes verified this round are in `constants.roanoke_instruments` (parcel and class layers, TRAKiT, the impervious layer for stormwater units, the eTrakit full-field postback for permits and code cases, the imagery exports, the fee pages, the airport overlay, CityProtect, RRHA). What did not serve: westernvawater.org (403; empty via Bright Data), the WVWA service-line inventory app (private item), the EPA Virginia radon list (403), municode (script-rendered), eTrakit detail views (login-gated), the Circuit Court land records (subscription).
- Three Roanoke rows with 9/29 advisory briefs (71 Richland, 72 Hillcrest, 75 Albemarle) and five others (67 Bellwood, 68 Saint Andrew, 69 Jefferson, 70 Mt Airy, 74 31st St) await assimilation; the Roanoke fee rule, the duplex-market prior and the RRHA pause apply to the three Roanoke rows when they are read."""
append_line(PREADME, f"assimilate_{TAG}.py", PLINE)
print("done")
