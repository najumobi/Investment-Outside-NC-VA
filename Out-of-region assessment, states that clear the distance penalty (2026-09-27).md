# Out-of-region assessment: which states clear the distance penalty

Written 2026-09-27 against the area-projection outputs of 2026-09-25/26. Companion workbook: `area_projection_189_areas_volume_distance_2026-09-27.csv` (one row per area, every number below traceable to a column).

## 0. The one-paragraph answer

Pennsylvania and Ohio are the only states whose prospects survive an honest distance penalty, and they do so by volume, not by hit rate: each delivers roughly two to three times the expected verified-lead flow of the entire NC/VA home region after the penalty. West Virginia has the best hit rates in the country but almost no duplex sales, so it is an extension of a Pennsylvania sweep, never a target on its own. Every other state, including all fifteen micropolitan "still likely lead" areas, fails on volume × distance, and several of the best-looking ones (SC, WV, AL, MS, IN, TX) are flattered by a tax-basis bias the projection cannot see. The penalty as coded (a flat −2 score points beyond 1.25 h from Williamsburg) is not the binding constraint; 74% of the current board already pays it.

---

## 1. What the projection measures, and what it does not

### 1.1 The method (from `project_areas.py`, `lead25.py`, `estimators_all.py`, `leaders_w2.py`)

1. Take every NC/VA listing the campaign sifted that carries a price, a rent-to-price figure and a county. The pipeline says 692; my rebuild from files 06c, 13a, the round 4–14 sweep files and the two weekly `scored.csv` runs finds 698.
2. Express each listing as a ratio to its home county's price level and rent-to-price level.
3. Re-price it into each target county at that county's levels under three price bases: **A** (ACS 2020-24 only), **Z** (Zillow ZHVI level, ACS rent moved by ZORI growth), **R** (Zillow level × Redfin's county duplex premium, shrunk toward the national ratio with k = 20).
4. Test the two money gates: price ≤ $532,643 (hard ceiling) and rent-to-price ≥ 0.9% plus a cost shift for the target county's tax rate and state insurance versus the listing's home county (`shift = 100 × Δ$/yr ÷ (8.4 × price)`).
5. Target pass share ÷ NC/VA pass share = factor applied to the stated NC/VA rate of 1 in 14. Non-money gates are assumed to pass at the NC/VA rate everywhere.
6. County rules first remove counties the campaign would not search: student market (≥ 25% enrolled; 15–25% drops campus-radius ZIPs), resort market (≥ 14% seasonal units), post-disaster (FEMA large awards ≥ 0.03 per home since 2023), price screen (CLOSED counties out; ELIMINATED/LIKELY ELIMINATED kept only under a ZIP-level cap when feasible sales ≥ 2/quarter; < 60 two-to-four-unit structures = no stock).
7. Worst case = minimum across the three price bases, three dispersion settings (×0.8/1.0/1.25), cost penalties only (no credits), non-money gates 1.35× harder, and three rule readings (strict / lenient / harsh).
8. Crediting: plain (every money-passer counts), 3-band (< 1.2% → 35.5/96; 1.2–1.8% → 24.5/54; ≥ 1.8% → 0.5/33), 2-band (< 1.8% → 59.5/149; ≥ 1.8% → 0.5/33). The final files use 2-band.
9. Verdict tiers (`lead25.py`): high-confidence lead = worst case better than 1 in 7; likely lead = both centrals better than 1 in 7 or worst case (before the 1.35× stress) better than 1 in 8.4; otherwise no confident call. Result on 2026-09-26: 30 likely leads, 159 no confident call, 0 high confidence. Re-weighted with 2-band survival: 15 of 30 still likely.

### 1.2 Three structural consequences

- **It measures caliber per listing, not flow.** A 1-in-6.5 area with six duplex sales a year and a 1-in-12 area with 2,400 are incommensurable until multiplied by volume. None of the eight projection files carries volume. That multiplication is the substance of this assessment.
- **Survival weighting is the decisive refinement.** NC/VA money-passers at 1.8%+ rent-to-price reached the live list 0.5 times in 33: they are shells, package sales and mis-listed units. `survival_driver.py` tested absolute vs county-relative yield as the predictor (logistic fits, leave-one-county-out, a transfer test from pricier to cheaper counties) and found absolute bands transfer better. This is what demotes the cheap Sun Belt micros between the unweighted and the weighted columns.
- **1 in 14 is slightly ambiguous.** The rebuild gives 181 money-passers of 698 (25.9%), survival-weighted 60.0; `lead25_surv.py` says the funnel is "59 of 692" to the live list, which is 1 in 11.7. The stricter 1 in 14 presumably counts a later stage. Rankings are unaffected (everything scales to the same baseline); absolute leads-per-quarter figures would rise ~1.2× under the looser reading. 1 in 14 is carried as stated.

### 1.3 Baseline distribution (rebuilt, 698 listings)

Money-passers by band: < 1.2% 96, 1.2–1.8% 53, ≥ 1.8% 32. Median price of all listings $339,900; of passers $190,000; median passer rent-to-price 1.17%. 104 passers at or under $200K, 53 at or under $150K.

Hit-rate erosion as the 0.9% bar rises (survival-weighted survivors as a share of the 0.9% count):

| Bar | Plain | Weighted |
|---|---|---|
| 0.90% | 100% | 100% |
| 0.95% | 82% | 80% |
| 1.00% | 75% | 72% |
| 1.05% | 68% | 64% |
| 1.10% | 61% | 57% |
| 1.15% | 54% | 48% |
| 1.20% | 47% | 41% |
| 1.30% | 37% | 27% |

This table is the conversion between any annual cost and its effect on the hit rate, and it is used for distance, management and tax below.

---

## 2. The distance penalty as it exists

Source: `weekly_sweep.py` line 190 and `round9_final.py` line 73 (`if drive and drive > 1.25: pen += 2`); README line 33 (score = cash-on-cash at 6.75% minus YELLOW −4, CrimeGrade F −3 / D− −2 / D −1 / D+ −0.5, drive over 1.25 h from Williamsburg −2, historic −1, flood factor 5+ −1, DSCR under 1.2 −2). Drive hours live in `constants.json` → `drive_wb` (54 cities, Google-derived).

Properties of the penalty:

1. **Binary.** Petersburg at 1.3 h and Pennington Gap at 6.7 h pay the same −2. Nothing scales beyond the threshold.
2. **Williamsburg-only.** File 14 carries `drive_ec` (Elizabeth City) on 45 of 61 rows; no script reads it. Fayetteville is 4.2 h / 3.7 h, Rocky Mount 2.4 / 2.0, Wilson 2.7 / 2.2; Florence SC, Columbia, Augusta and Savannah are 0.5 h closer from Elizabeth City. The model does not know.
3. **Already the norm.** 45 of 61 board rows (74%) exceed 1.25 h; 4 of the top 10 scores do, including #1 (118 & 120 S Poplar, Winston-Salem, 4.6 h, score 10.5) and #2 (1114 Lafayette, Roanoke, 3.8 h, 10.0). File 11's rule is that anything outside the radius is "Tier 2 with a property manager"; file 10 found only 4 of 40 candidates depend on self-management. The campaign is already a Tier-2 campaign confined to two states.
4. **Not a hit-rate effect.** The −2 reorders; it never removes. Inside the model an Ohio duplex "makes up for" the penalty as soon as its cash-on-cash is two points above a Roanoke duplex's, which cheap Rust Belt stock does trivially. The literal answer to "does any state make up for the penalty as assessed" is therefore "all of them", and that is a defect of the assessment, not a finding about geography.

---

## 3. The distance penalty re-specified as a cost

The pipeline's own cost-shift formula converts an annual dollar cost into a shift of the Gate-5 bar: `shift (pts) = 100 × Δ$/yr ÷ (8.4 × price)` (rent must cover the cost after ~30% variable expenses). Applied to the items distance actually creates:

| Item | Δ$/yr | Price | Shift |
|---|---|---|---|
| Management 12% instead of modeled 8%, $1,600/mo gross | $768 | $150K | +0.061 |
| File 30 minimum-fee effect (steady state, $100/unit floor + one placement per two years) | $1,280 | $120K / $190K | +0.127 / +0.080 |
| Two fly-in visits per year | $1,400 | $150K / $200K | +0.111 / +0.083 |
| Long day-drive increment over a Charlotte day trip | $600 | $150K | +0.048 |

The management items apply to any managed property, in-region Tier 2 included, so the *marginal* penalty of leaving the two states is travel plus jurisdiction ramp-up. Schedule used, relative to the campaign's existing Tier-2 rows (Roanoke 3.8 h, Fayetteville 4.2 h, Winston-Salem 4.6 h, Charlotte 5.0 h Google):

| Tier | Definition (OSRM hours from Williamsburg) | Marginal shift | Factor |
|---|---|---|---|
| A drive | ≤ 6.5 h (≈ ≤ 5.5 h Google; Charlotte-equivalent) | ≈ 0 | ×1.00 |
| B long drive / short hop | 6.5–9.5 h | +0.05 | ×0.80 |
| C fly-in | > 9.5 h | +0.08 to +0.11 | ×0.62 (harsh: ×0.50) |

Calibration: OSRM routes run 1.1–1.25× slower than the campaign's Google constants (Roanoke 4.5 vs 3.8; Fayetteville 4.6 vs 4.2; Charlotte 6.2 vs 5.0), so the 6.5 h OSRM cut-off is Charlotte.

Break-even caliber to match an in-region 1 in 14: Tier B needs a 2-band central of 1 in 11.2 or better; Tier C needs 1 in 8.7 (base) or 1 in 7 (harsh). 8 of 11 Tier-A areas, 16 of 22 Tier-B areas and 57 of 156 Tier-C areas clear their bar — but caliber without volume is worth nothing, which is the next section.

What distance does **not** degrade: the verification engine. Files 28–49 ran on CAMA cards, ArcGIS layers, Register of Deeds instruments, HUD workbooks, DEQ/EPA records, dated Street View and court portals; none requires presence. The true losses are (a) the photo-based condition grade cannot be checked by a drive-by, pushing a remote campaign toward GREEN-only stock; (b) each new jurisdiction costs the instrument-building that consumed about a day per NC town (`constants.json` holds `_instruments` blocks for Pinetops, Spring Lake, Rocky Mount, Oxford, Cherryville, Reidsville, Clayton and Durham); (c) lender friction is unchanged for the conventional two-unit investment loan Ogo is waiting on after 13 October 2026.

Routed drive times (OSRM, from Williamsburg / from Elizabeth City): Baltimore 3.9 / 5.7; Salisbury MD 4.0 / 4.0; Cumberland MD 5.1 / 6.9; Beckley 5.6 / 7.4; Philadelphia 5.9 / 7.0; Bluefield 6.2 / 7.5; Florence SC 6.2 / 5.7; Johnstown 6.5 / 8.2; Morgantown 6.5 / 8.3; Charleston WV 6.8 / 8.6; Fairmont 6.8 / 8.6; Columbia SC 7.6 / 7.1; Pittsburgh 7.5 / 9.3; Scranton 7.8 / 9.0; Huntington 7.8 / 9.6; Wheeling 8.1 / 9.8; Parkersburg 8.2 / 9.9; Youngstown 8.5 / 10.3; Augusta 8.9 / 8.4; Binghamton 9.0 / 10.2; Savannah 9.3 / 8.8; Erie 9.6 / 11.4; Cleveland 9.8 / 11.5; Dayton 10.5 / 12.3; Atlanta 10.8 / 10.9; Louisville 11.4 / 13.2; Toledo 11.5 / 13.2; Indianapolis 12.8 / 14.6; Lansing 13.6 / 15.4; Terre Haute 14.2 / 16.0; Memphis 16.0 / 17.2; St. Louis 16.1 / 17.9; Jackson MS 17.7; Little Rock 18.4; New Orleans 19.3; Tulsa 22.9; Oklahoma City 24.0; Wichita 24.2. Controls: Roanoke 4.5, Fayetteville 4.6, Charlotte 6.2. The remaining ~140 areas carry state/regional estimates, flagged `est` in the workbook.

Air access (norfolkairport.com, cross-checked against Wikipedia's ORF table): daily nonstops to Philadelphia (American Eagle), Baltimore (Southwest), Washington National and Dulles, Atlanta, Charlotte, Chicago O'Hare and Midway, Detroit, Minneapolis, Nashville, Newark, Dallas, Houston, Denver; seasonal only to Pittsburgh, Akron/Canton and Columbus (Breeze) and St. Louis (Southwest); two-weekly New Orleans (Breeze). No nonstop to Cleveland, Indianapolis, Louisville, Cincinnati, Memphis, Birmingham, Little Rock, Oklahoma City, Tulsa or Wichita. Richmond's route list is an interactive map and was not retrieved.

---

## 4. Volume

Source: Redfin's public county market tracker (the file `parse_redfin.py` and the 696-county screen were built from), Last-Modified 2026-06-02, twelve monthly periods ending 2026-05-31, property type "Multi-Family (2-4 Unit)", non-seasonally-adjusted, `homes_sold` summed per county. Cross-check: the parse reproduces the pipeline's own `map_data.json` recorded-sales figures for NC/VA exactly (NC 644, VA 579).

Feasible sales per quarter = sales ÷ 4 × the state's feasibility ratio from the county screen (share of the duplex price distribution under the ceiling and above the 0.83% break-even): AL 0.53, AR 0.57, GA 0.53, IA 0.60, IL 0.65, IN 0.63, KS 0.55, KY 0.45, LA 0.60, MI 0.60, MO 0.43, MS 0.57, NY 0.68, OH 0.62, OK 0.48, PA 0.56, SC 0.50, TN 0.52, TX 0.46, WV 0.56; pooled 0.53 where a state has no ratio. Expected verified leads per quarter = feasible ÷ (1 in N).

### 4.1 Home-region benchmark

NC/VA map categories A + B: 1,223 two-to-four-unit sales/yr → ~162 feasible/quarter → **~11.6 expected verified leads per quarter at 1 in 14**. Inside the 1.25 h radius (20 counties, Hampton Roads + Richmond/Petersburg + the Albemarle): 185 sales/yr → 1.75 leads/quarter. The other ~9.8/quarter are already Tier 2.

### 4.2 Metro breakdowns that drive the result

**Philadelphia CSA** (kept counties, Cape May out as resort, Bucks and Chester capped): Philadelphia County 336 sales, $305K 2–4-unit median; Delaware 199 / $311K; Montgomery 206 / $399K; Berks 146 / $283K; Bucks 56 / $490K; Chester 45 / $487K; Camden NJ 97 / $341K; Burlington 64 / $354K; Gloucester 45 / $329K; Atlantic 90 / $406K; Cumberland NJ 51 / $264K; Salem 32 / $243K; New Castle DE 63 / $317K; Kent DE 14 / $281K; Cecil MD 6 / $422K. Total 1,450; central 1 in 12.1, worst 21.5. At the PA ratio ≈ 200 feasible/quarter → 16 leads/quarter; because the CSA median is $339K the true ratio is lower than PA's average, so treat 12–16 as the range. Drive 5.9 h OSRM (≈ 5.0 h Google, identical to Charlotte). Philadelphia County's 336 looks low for a rowhouse city and is Redfin's classification; a floor.

**Pittsburgh CSA**: Allegheny 568 / $223K; Westmoreland 95 / $141K; Beaver 64 / $126K; Washington PA 58 / $110K; Butler 40 / $140K; Fayette 33 / $75K; Lawrence 28 / $96K; Mercer 26 / $88K; Jefferson OH 19 / $93K; Armstrong 15 / $71K; Indiana 13 / $114K; Hancock WV 7; Brooke WV 4. Total 970; central 1 in 10.6, worst 20.0; 135 feasible/quarter → 12.8 leads/quarter, ×0.80 = 10.2. 7.5 h OSRM; ORF–PIT is seasonal Breeze only.

**Cleveland–Akron–Canton**: Cuyahoga 1,682 / $157K; Summit 257 / $167K; Stark 174 / $161K; Lorain 106 / $139K; Erie OH 42; Portage 37; Ashtabula 27; Wayne 26; Tuscarawas 24; Lake 18; Medina 15; Huron 14; Geauga 6; Carroll 2. Total 2,430; central 1 in 12.2, worst 21.0; 378 feasible/quarter → 31 leads/quarter, ×0.62 = 19. 9.8 h OSRM; no ORF nonstop except seasonal Breeze to Akron/Canton. The single largest pool in the 189-area set, and squarely in the sub-$1,000-rent management-minimum zone file 30 describes.

**Scranton / NEPA**: Lackawanna 384 / $240K; Luzerne 449 / $235K; Wyoming 3; Schuylkill (Pottsville μSA) 89 / $167K. Scranton central 1 in 12.8, worst 24.8 (116 feasible/quarter → 9.1 leads, ×0.80 = 7.3); Pottsville 1 in 7.3 / 12.4 (12 feasible → 1.7).

**Upper Ohio Valley**: Kanawha 23 / $128K; Cabell 28 / $180K; Ohio County WV 12 / $145K; Marshall 9; Belmont OH 15 / $106K; Monongalia 46 / $298K; Marion 7; Harrison 14 / $174K; Raleigh (Beckley) 4; Mercer WV (Bluefield) 1; Cambria (Johnstown) 71 / $65K; Somerset PA 12 / $88K. Charleston–Huntington central 1 in 6.8, worst 11.4, 10 feasible/quarter → 1.5 leads; Johnstown 1 in 7.6 / 12.2, 11.5 feasible → 1.5; Wheeling 1 in 6.6 / 15.8, 5 feasible → 0.8; Fairmont–Clarksburg 1 in 6.6 / 13.3 → 0.5; Morgantown 1 in 12.7 / 61.7 (student rule, $298K) → 0.5; Beckley 1 in 6.5 / 10.7 → 0.13. Whole corridor ≈ 5 leads/quarter, all within one 7–8 h drive loop.

**Washington–Baltimore ex-Virginia**: Baltimore City 200 / $289K; Baltimore County 25 / $537K; Anne Arundel 17 / $265K; Harford 5; Carroll 7; Frederick 13 / $389K; Washington MD 42 / $250K; District of Columbia 199 / $837K; Berkeley WV 20 / $296K; Jefferson WV 4; Franklin PA 42 / $215K. Total 574; central 1 in 13.4, worst 33.1. The pooled feasibility ratio overstates this area badly (DC's median is $837K, the model already caps it); realistically Baltimore City, Washington County MD and Franklin County PA are the only searchable pockets → 3–4 leads/quarter, not the 5.8 the workbook shows. 3.9 h OSRM.

**Southern Tier NY**: Broome (Binghamton) 255 / $165K; Tioga 21; Chemung (Elmira) 81 / $88K; Steuben 45 / $129K. Binghamton central 1 in 11.2, worst 15.8 (47 feasible → 4.2 leads, ×0.80 = 3.4); Elmira–Corning 1 in 9.9 / 13.8 (21.5 feasible → 2.2, ×0.80 = 1.7). 9.0 h.

**Toledo** (Lucas 211 / $106K; Wood 18): 1 in 9.7 / 16.3, 36 feasible → 3.7, ×0.62 = 2.3. **Youngstown** (Mahoning 58, Trumbull 39): 1 in 9.7 / 15.2, 17.5 feasible → 1.8, ×0.80 = 1.4. **Indianapolis** (Marion 522 / $206K; Madison 51; Delaware IN 37; Hamilton 21 / $408K): 751 total, 1 in 9.6 / 16.5, 118 feasible → 12.3, ×0.62 = 7.6.

### 4.3 State ranking, post-penalty

Volume allocated to states by county (multi-state areas split), 1-in-N from the 2-band central; "wtd N" is volume-weighted.

| State | Areas | 2–4-unit sales/yr | Feasible/q | Wtd N | Best N | Leads/q central → after penalty | Tier mix |
|---|---|---|---|---|---|---|---|
| PA | 14 | 3,373 | 467 | 11.6 | 6.7 | 41.1 → **35.2** | A4 B9 C1 |
| OH | 11 | 3,278 | 506 | 11.8 | 6.6 | 43.1 → **27.2** | B6 C5 |
| LA | 9 | 1,317 | 198 | 11.3 | 6.9 | 17.7 → 11.0 (worst-case basis 4.2) | C9 |
| IN | 10 | 960 | 150 | 9.7 | 7.0 | 15.7 → 9.7 | C10 |
| IL | 14 | 884 | 136 | 10.8 | 7.8 | 12.8 → 8.0 | C14 |
| GA | 13 | 829 | 110 | 12.1 | 6.9 | 9.4 → 6.1 | B2 C11 |
| NY (upstate) | 3 | 436 | 75 | 10.8 | 9.9 | 6.9 → 5.5 | B2 C1 |
| MO | 7 | 731 | 86 | 10.4 | 6.8 | 8.3 → 5.1 | C7 |
| KS | 9 | 726 | 100 | 13.6 | 8.6 | 7.4 → 4.6 | C9 |
| NJ (Philadelphia CSA share) | 1 | 379 | 52 | 12.1 | 12.1 | 4.3 → 4.3 | A |
| MD + DC | 4 | 573 | 77 | 13.0 | 9.0 | 6.0 → 6.0 (realistically 3–4) | A |
| WV | 11 | 210 | 29 | **9.3** | **6.5** | 3.4 → 3.0 | A6 B5 |
| TN | 5 | 283 | 37 | 9.2 | 8.0 | 4.0 → 2.5 | C5 |
| AR | 11 | 255 | 36 | 10.0 | 6.3 | 3.6 → 2.3 | C11 |
| TX | 25 | 326 | 37 | 10.6 | 7.1 | 3.6 → 2.2 | C25 |
| MI | 4 | 256 | 38 | 12.4 | 10.2 | 3.1 → 1.9 | C4 |
| AL | 12 | 206 | 27 | 9.1 | 6.9 | 3.1 → 1.9 | C12 |
| OK | 14 | 255 | 31 | 11.3 | 7.3 | 2.8 → 1.8 | C14 |
| KY | 9 | 241 | 28 | 12.4 | 6.8 | 2.4 → 1.6 | B3 C6 |
| IA | 6 | 175 | 27 | 11.3 | 7.4 | 2.5 → 1.5 | C6 |
| MS | 9 | 134 | 19 | 8.4 | 6.6 | 2.3 → 1.4 | C9 |
| DE (Philadelphia CSA share) | 1 | 77 | 11 | 12.1 | 12.1 | 0.9 → 0.9 | A |
| NM | 6 | 61 | 8 | 7.4 | 6.4 | 1.1 → 0.7 | C6 |
| SC | 3 | 37 (Redfin gap) | 5 | 8.2 | 8.0 | 0.6 → 0.5 | A1 B2 |
| AK, CA, SD | 4 | — | — | — | — | < 1 | C |

Totals: all 189 areas 207 leads/quarter central, 145 after penalty; Tier A 26.1 (unchanged), Tier B 39.6 → 31.7, Tier C 141 → 88. Home region for comparison: 11.6.

### 4.4 Why the micro "leaders" are a mirage

The 15 areas still marked likely lead after re-weighting: Americus GA, Beckley WV, Blytheville AR, Charleston–Huntington WV, Clovis NM, El Dorado AR, Fairmont–Clarksburg WV, Grenada MS, Kennett MO, McComb MS, Meridian MS, Natchez MS, Oil City PA, Terre Haute IN, Wheeling WV. Their Redfin 2–4-unit sales run from 1 (Bluefield's WV half) to 77 (Charleston–Huntington) a year; the median is under 30. Thirteen of fifteen are Tier C fly-ins. All sit in sub-$1,000-rent stock where file 30's management minimums add 0.08–0.13 pts to the bar on their own. Only Charleston–Huntington and (as a Pittsburgh add-on) Wheeling and Fairmont carry both caliber and reachable volume; Terre Haute (1 in 7.0, 22 sales, 14 h) does not.

---

## 5. Two penalties the projection cannot see

### 5.1 Rental tax classification (assumption: training knowledge through mid-2026, not re-verified this session)

The projection derives the county tax rate from ACS owner-occupied taxes ÷ owner-occupied value (B25103 / B25077). NC and VA tax rentals and homesteads identically, so the baseline is unbiased; several candidate states do not:

| State | Mechanism | Rental vs owner burden | Δ rate (est.) | Bar shift | Hit-rate factor |
|---|---|---|---|---|---|
| SC | 6% assessment ratio for non-owner-occupied vs 4%, plus Act 388 school-operating exemption for owner-occupied only | ≈ 2–3× | +0.8 to +1.0 | +0.10 to +0.12 | ×0.55–0.60 |
| WV | Class III/IV (non-owner-occupied) levied at twice the Class II rate | 2× | +0.5 | +0.06 | ×0.77 |
| AL | Class II (rental) assessed at 20% vs Class III (homestead) 10% | 2× | +0.4 | +0.05 | ×0.80 |
| MS | Class II 15% vs Class I 10%, plus homestead credit | 1.5× | +0.35 | +0.04 | ×0.83 |
| IN | 2% cap on non-homestead residential vs 1% homestead | up to 2× | +0.7 | +0.08 | ×0.70 |
| TX | Loss of $100K+ school homestead exemption and appraisal cap | +0.5 to +0.7 on cheap stock | +0.7 | +0.08 | ×0.70 |
| LA | Loss of the $75K homestead exemption on parish levies | +0.3 to +0.4 on $150K stock | +0.35 | +0.04 | ×0.83 |
| OH, NY | Owner-occupied rollbacks (OH) and Basic STAR (NY) | +10–20% | +0.15 to +0.3 | +0.02 to +0.04 | ×0.90 |
| PA, NJ, DE, MD*, KY, TN, KS, MO, OK, AR, IL, MI, IA | Uniform, or homestead relief too small to matter | ≈ none | — | — | ×1.00 |

*Maryland's Homestead Credit caps assessment growth for owner-occupants who already own; a new buyer pays full value either way, so no bias for the purchase decision.

This further favors Pennsylvania over every Appalachian and Sun Belt "leader", West Virginia included, and it must be verified against each state's statute before it moves a decision.

### 5.2 Insurance (from the Insurance.com 2026 $300K-dwelling table embedded in `project_areas.py`)

PA $1,434 · NJ $1,449 · DE $1,461 · NY $1,844 · VA $1,939 · WV $1,961 · OH $2,109 · MD $2,242 · GA $2,301 · MS $2,602 · IL $2,802 · IN $2,869 · SC $2,870 · MI $3,071 · AR $3,195 · TN $3,198 · AL $3,716 · MO $3,783 · NC $3,799 · KY $4,471 · TX $4,582 · LA $5,185 · KS $5,289 · OK $5,378. The Mid-Atlantic/Appalachian arc is favorable against the home region; the Gulf and Plains are why New Orleans (worst 34), Oklahoma City (26), Wichita (27) and Tulsa (23) show worst-case figures so far from their centrals. The model's adverse case counts only penalties, so PA's insurance advantage is in the central but not in the worst case.

### 5.3 Landlord-tenant climate (assumption: training knowledge, unlinked)

Tenant-leaning within the Tier A/B set: New Jersey (statewide just-cause Anti-Eviction Act), New York (HSTPA 2019; Good Cause Eviction 2024, opt-in by upstate cities — Binghamton's status not verified), Maryland (2024 Renters' Rights and Stabilization Act; Baltimore City registration and lead law), DC (slow process, TOPA). Pennsylvania is moderate statewide with Philadelphia-specific rental licensing, lead certification and a mandatory eviction-diversion program. Ohio, West Virginia, Indiana, Kentucky, Tennessee, South Carolina, Georgia, Alabama, Mississippi, Arkansas, Texas, Oklahoma, Kansas and Missouri are landlord-friendly with fast processes. Virginia's own July 2026 change (14-day pay-or-quit) narrowed the gap between the home region and the Mid-Atlantic.

---

## 6. Synthesis

1. **Pennsylvania** clears the bar three ways: Philadelphia is Tier A with volume greater than the entire home region; the Pittsburgh–Johnstown–Wheeling–Morgantown loop is Tier B with 1 in 6.6–10.6 caliber and ~14 leads/quarter post-penalty; NEPA and the Southern Tier add another ~14. Lowest insurance in the table, no rental tax classification, moderate law, daily ORF–PHL service. Post-penalty 35 leads/quarter versus 11.6 at home.
2. **Ohio** clears it on Cleveland alone (19 post-penalty leads/quarter from one CSA) plus Toledo and Youngstown's 1-in-9.7 caliber; costs are a fly-in operating model, no nonstop, cheap stock in the management-minimum zone, and a modest owner-rollback tax bias. 27 leads/quarter post-penalty.
3. **West Virginia** is the caliber leader (state-weighted 1 in 9.3, best 6.5) with 210 sales a year statewide; its Class III/IV levy halves the advantage; worth searching only as the WV legs of a Pennsylvania loop.
4. **Indiana** is the only other fly-in state whose post-penalty flow (9.7) approaches the home region's, on Indianapolis' 1 in 9.6; the 2% non-homestead cap and the lack of an ORF nonstop take it to roughly parity, not advantage.
5. **Louisiana, Illinois, Georgia, Missouri, Kansas** show central flows of 7–18 but collapse on the worst case (insurance) or the fly-in factor or both.
6. **Maryland/DC/Delaware/New Jersey** are the only other Tier-A ground; price (DC, Baltimore County), the pooled-ratio overstatement, NJ's taxes and just-cause law, and MD's 2024–25 statutes leave 5–8 leads/quarter with the least favorable operating climate in the set.
7. **South Carolina** cannot be scored: Redfin has no rows for Richland, Lexington, Kershaw or Fairfield. Columbia (1 in 8.4, 7.6 h) and Florence (1 in 8.0, 6.2 h, Tier A) deserve a volume check from another source before being dismissed — and a rental tax burden ~2–3× the modeled one before being pursued.
8. **Everything else**, the fifteen micro leaders included, fails on volume × distance.

Expectation management: the campaign's own record is that zero NC/VA rows currently pencil at asking price after full verification (file 49a: 61 rows, the one full-gate pass under contract to someone else). The same gates will kill most out-of-state candidates. What Pennsylvania and Ohio change is the number of at-bats: ~62 post-penalty leads per quarter against 11.6.

---

## 7. Recommendations

1. If the geography widens, widen north along I-95 / I-76 / I-79, not south or west. Order of attack: Philadelphia CSA (Cape May out; Bucks and Chester under ZIP caps) → the Upper Ohio Valley loop (Pittsburgh, Johnstown, Wheeling, Morgantown–Fairmont, Charleston–Huntington) → Scranton/Pottsville and the Southern Tier.
2. Ohio only after the `pm_fee_schedule` intake from file 30 exists and a fly-in cadence is priced; Cleveland is the prize, Toledo and Youngstown the caliber plays, the rest of the state is not worth the trip.
3. Retire the micro leaders as search geographies; keep them as alert-only ZIPs in the weekly sweep if at all.
4. Fix the assessment before re-running the leaders test: replace the flat −2 with a Gate-5 bar shift (+0.05 Tier B, +0.10 Tier C); score `drive_ec` alongside `drive_wb`; add a per-state rental-classification tax multiplier; carry Redfin's coverage gaps as explicit unknowns rather than zeros.
5. Verify before deciding: (a) the tax-classification table in §5.1 against each state's statute; (b) Philadelphia's and Baltimore's feasibility ratios at county level by running those CSAs through `screen_replica.py` rather than my state-level approximation; (c) South Carolina volume from a non-Redfin source.

---

## 8. Assumptions, ambiguities and gaps

- 1 in 14 vs the rebuilt 1 in 11.7 (§1.2): relative rankings unaffected; absolute flows may be ~1.2× higher.
- Feasibility ratios are state-level; Philadelphia and Washington–Baltimore are overstated, cheap markets (Johnstown, Toledo, Elmira) understated.
- OSRM vs Google: 1.1–1.25× slower; tiers calibrated accordingly. 140 of 189 areas carry estimated hours.
- Redfin coverage: no rows for 16 kept counties (Columbia SC ×4, Columbus GA ×4, Hattiesburg MS ×3, Corpus Christi TX ×2, Salisbury MD ×2, Huntingdon PA); Philadelphia County's 336 is a classification floor. All volumes are floors, not counts.
- The projection assumes non-money gates pass at the NC/VA rate; Cleveland, Toledo, Youngstown and Scranton hold deeper distressed stock than NC/VA, which the 1.8%+ survival discount only partly captures.
- Tax classification and landlord-law claims are training knowledge (mid-2026), unlinked and not re-fetched.
- Bluefield's Virginia half (Tazewell County) is excluded by Najum's own override in `match_areas14.py` and is honored here.

---

## 9. Plumbing

- Local archive (repo split-zip, reassembled and extracted): the eight projection files, `lead25.py`, `lead25_surv.py`, `leaders_w2.py`, `estimators_all.py`, `worst_w2.py`, `survival_driver.py`, `decompose_shift.py`, `project_areas.py`, `parse_redfin.py`, `build_baseline.py`, `funnel_union.py`, `weekly_sweep.py`, `round9_final.py`, `constants.json`, `model/map_data.json`, README, campaign files 00, 07, 10, 11, 14, 30 and the round sweep CSVs — read directly.
- Redfin county market tracker — `curl` from the container (241 MB, served; Last-Modified 2026-06-02; periods to 2026-05-31). Cross-check: NC/VA totals reproduce the pipeline's `map_data.json` exactly.
- OSRM public router — 96 route calls by `urllib`, all served. Cross-check: the campaign's Google-derived `drive_wb` constants.
- norfolkairport.com/where-we-fly — `curl` served on the fourth URL (first: TCP reset; second and third: 404). Cross-check: Wikipedia's ORF airlines-and-destinations table by `curl`, agrees.
- flyrichmond.com/airline-information — served, carriers only; route list is an interactive map, not retrieved.
- Bright Data `ajumobinicholasY` search_engine ×2 and `djnicholasaY` ×2 → "session expired" (connector-level failures). `djnicholasq`, `bjumobinicholasY` and Composio not exercised: the targets were plain pages reachable by `curl` (route 1). No Apify leg needed.
- No Reddit target; no experiential question; no user-generated sources used.
- Recency: projection files one day old; Redfin four months old; OSRM and ORF live at time of fetch; ACS 2020-24 underlying.

## 10. Sources

- Redfin Data Center: https://www.redfin.com/news/data-center/ — county file: https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/county_market_tracker.tsv000.gz
- OSRM: http://project-osrm.org/ — endpoint pattern `https://router.project-osrm.org/route/v1/driving/{lon},{lat};{lon},{lat}?overview=false`
- Norfolk International Airport nonstops: https://www.norfolkairport.com/where-we-fly/ — cross-check https://en.wikipedia.org/wiki/Norfolk_International_Airport
- Richmond International Airport: https://flyrichmond.com/airline-information/
- Management-fee figures as cited inside campaign file 30 (not re-fetched): https://www.baselane.com/resources/how-much-do-property-managers-charge · https://www.turbotenant.com/property-management/fees-north-carolina/ · https://www.turbotenant.com/property-management/fees-virginia/
- Insurance table as embedded in `_pipeline/area_projection/project_areas.py` (attributed there to Insurance.com 2026, $300K dwelling).
- Campaign files as named above, all under `2026-2027 Duplex Search Campaign/`.
