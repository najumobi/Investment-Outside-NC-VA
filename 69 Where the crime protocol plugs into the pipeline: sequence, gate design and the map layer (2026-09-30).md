# Where the crime protocol plugs into the pipeline: sequence, gate design and the map layer (2026-09-30)

Written 2026-09-30 (cloud session) against `_pipeline/weekly_task_prompt_TEMPLATE.md`, `weekly_sweep.py` (the `ingest` and `underwrite` stages), memo 65 (the inaugural regional sweeps), memo 66 (the novice column), file 14 as of 2026-09-29 (136 rows, 122 active, 71 ZIPs), and the CrimeGrade work in `pipeline_changes/2026-09-29-crimegrade/` (the address reader, the Philadelphia and Cleveland block-group validation, and the 206-screenshot, nine-tab sample read for 43 addresses on 2026-09-30). Najum's questions: where in the sequence does the crime assessment belong; are the weekly sweeps the wrong place for it; and was feeding the protocol only the GREEN-for-novice rows the right way to plug it in.

## 0. Answer first

Crime belongs before the property work, as Najum reasoned, and earlier than he proposed: inside the weekly sweep, computed by the script from a map layer that is built once per ZIP by hand and refreshed once a year. The reason is the cost structure. Every other gate in the pipeline costs something per property (a detail-page slot, a photo read, hours of frame-by-frame review). A block-level crime read costs about four minutes per ZIP page, once, and nothing per property after that, because the sweep already geocodes every listing to its Census block and the map layer can be read per block group in advance. Under the rule that governs screening order (do the test with the lowest cost per rejection first), a test with zero marginal cost and a rejection rate of 20 to 70 percent goes ahead of everything that costs a slot or an hour. The sweep is therefore exactly where the crime read happens; it already does, crudely, through the ZIP letter and the −3/−2/−1 penalty in `underwrite`. What leaves the weekly loop is the human effort, which moves from per property to per ZIP.

Feeding the protocol the 14 GREEN and GREEN-verify rows was a sound pilot and the wrong production order. The novice grade is a condition gate that is applied after the detail fetch and, for 117 of 136 rows, says YELLOW because one listing photo is all the evidence there is; putting it first discards 86 percent of the board on evidence scarcity before the location has been looked at, and it keeps GREEN rows in F blocks alive while YELLOW rows in B blocks die. The right joint use is crime first (location, permanent, free per property), condition second (building, evidence-dependent, changes with every read).

The load-bearing decision is not where the gate sits but how strict it is. On the 43 addresses read from the sample, "no F on Robbery" passes 34; "no F on Robbery, Burglary or Vandalism" passes 12; "nothing worse than D on any of six tabs" passes 4. Cleveland's east side and West Philadelphia pass none of these on any tab. The threshold decides whether the PA-OH-WV-NY expansion has survivors, and it should differ by region: strict where the funnel is wide (285 Ohio rows in the detail backlog) and lenient where it is thin (8 NC/VA shortlist rows a week).

## 1. The sequence as it runs, with what each stage costs and rejects

| Stage (template step) | Who does it | Cost per candidate | Rejection observed on 2026-09-28 | Where crime enters today |
|---|---|---|---|---|
| List fetch and parse (2–3) | script, remote | none | — | — |
| Money and shape gates at `ingest` (3): geocode, tract Gate 1, rent-to-price under 0.9%, hard ceiling, unit count, land | script | none | 87% of NC/VA listings, 76% phila, 61% pitt, 61% ohio | — |
| Detail fetch (4) | script, capped at 50 per region per week | the scarce resource: 790 rows waited in the backlog after the first night | — | — |
| Photo grade and Gate 3 (5–6) | the routine's Claude session | one photo read | 51% of the 150 regional detail rows (43 RED, 34 Gate-3) | — |
| `underwrite` (7): Gate 5, CoC, score, fold into file 14 | script | none | NEAR-MISS and negative cash flow | ZIP letter: −3 F, −2 D-, −1 D, −0.5 D+; vacancy 8% for F; "Constants needed" fetches the Overall letter by regular expression (step 8) |
| Najum's review of UNREVIEWED rows; advisory deep reviews; assimilation | Najum, claude.ai sessions | hours per property (20 to 90 frames, permits, county cards, memos 31 to 64) | the grade moves on about one row in seven (memo 66 §4) | ZIP letter only, as a −n in `why` |
| Inspection, bids, offer | Najum, inspector | days and money | — | — |

Two facts about this table decide the placement. First, the only stage whose cost is a hard cap is the detail fetch: 50 pages per region per week against shortlists of 287, 318 and 335. Any free gate applied before it buys detail slots; the same gate applied after it buys nothing. Second, the crime inputs used now are the retired Overall ZIP letter, so retiring Overall, Violent and Property without a replacement silently leaves `crime_pen`, the 8 percent vacancy rule and step 8 running on a measure the campaign has abandoned, and file 14's `crime` and `why` columns carrying it.

## 2. The ordering rule and its two caveats

Mitten (1960) proved the rule for a series of pass/fail tests: order them by cost of the test divided by its probability of rejecting the item, lowest first, and total expected cost is minimised. The pipeline's gates are a series in that sense (a property must pass all of them). Costs and rejection rates from the table give this order: the money gates (free, 61 to 87 percent), the block-level crime read (free once the layer exists, 20 to 70 percent depending on threshold), the photo grade (one slot plus one read, 51 percent), then the human stages. Crime sits second, ahead of the photo grade, because it costs nothing per property and rejects a comparable share. Najum's reasoning was right; the rule only adds that the ordering is decided by marginal cost per property, and that the crime read's marginal cost is zero because its cost is fixed per ZIP.

Caveat one: an early test that is noisy rejects good items that no later stage can recover. The validation measured that noise: a CrimeGrade colour is worth about one recorded year of robberies, and one F block group in four (Cleveland) to one in three (Philadelphia) sits below its city's median rate. So the knockout should fire only on the robust extreme (Robbery F, read from the block group and its across-the-street neighbour), while the rest of the reading works as a score term and as flags, never as a knockout on a single tab.

Caveat two: the cost of a false rejection depends on the supply of alternatives. Where the funnel is wide the loss is nothing (the next row is as good); where it is thin it is a real candidate. That is why the threshold should be set per region rather than once.

## 3. What the numbers say about strictness

File 14, retired ZIP letters, active rows: 85 of 122 are D or worse; by state, Ohio 15 of 25 rows F and 6 D-; Virginia 14 of 29 F; North Carolina 11 of 34 F and 13 D-; New York none worse than D; Pennsylvania none worse than D.

The 43 addresses read from the nine-tab sample (the 15 photo-list rows and 28 other file-14 rows on the same pages):

| Rule | Pass, 43 addresses | Pass, the 15 photo-list rows |
|---|---|---|
| Robbery not F (position under 0.923) | 34 | 10 |
| Robbery better than D (under 0.77) | 20 | 6 |
| No F on Robbery, Burglary or Vandalism | 12 | 5 |
| Murder not F and Drug not F | 28 | 8 |
| Nothing worse than D on Robbery, Assault, Burglary, Vandalism, Drug, Murder | 4 | 2 |

Two readings of that table matter. The GREEN list is not a better-located list: 6 of its 15 clear "Robbery better than D" against 20 of 43 overall, the same fraction; condition and location are close to independent, so filtering on one tells you nothing about the other. And the block level rescues what the ZIP letter would have thrown away: 44120, 44104 and 44109 are ZIP-letter F or D-, but the validation found that half of Cleveland's block groups are not F, and the pages for 13904 and 14901 hold block groups from A+ to F. A ZIP-level knockout would have removed whole ZIPs in which half the blocks pass; the block-level gate keeps the ZIPs and drops the blocks.

## 4. The placement, concretely

1. **The map layer.** For each ZIP in the four sweep lists (400 ZIPs; 56 have some map today, 22 have the six tabs), six screenshots of the ZIP-page map: Robbery, Assault, Burglary, Vandalism as gradients, Murder and Drug as flags. Named `<zip>_<crime>.png`, kept in `_pipeline/maps/` on Dropbox (not in the repository; CrimeGrade's terms allow the hand copy, not the automated fetch the current step 8 performs, which retiring Overall removes). At the sample's pace (206 shots in two hours) a ZIP takes about four minutes.
2. **The block-group table.** `label_screenshots.py` and `grade_by_view.py` already label and align a batch; the validation's reader already reads every block group under a map. One script turns a batch into `model/crime_bg.json`: block-group GEOID → position on each of the six tabs, plus the page and view it was read from. A ZIP page at the default zoom holds 40 to 90 block groups and overlaps its neighbours, so the table grows faster than the ZIP list.
3. **The join at `ingest`.** The Census geocoder already returns the block for every listing (its first twelve digits are the block group; `geo_cache.json` should keep them, it keeps the tract now). Join `crime_bg.json`, write six positions and letters into `scored.csv`, and apply two rules: a knockout, and a sort key for the detail queue (memo 65 §4 and §8 item 1 made the ordering of the 50 slots the sweep's first defect; crime position belongs in that key beside the rent-to-price band). A listing whose block group is not in the table gets `crime: maps needed <zip>` and is folded below rows that have a reading, exactly as "Constants needed" works today; the weekly task then lists the ZIPs to shoot, which is the whole of Najum's recurring crime work.
4. **The knockout, by region.** Proposed and Najum's call: in the three regional sweeps (wide funnels), OUT when the Robbery position is 0.923 or more (F) and the across-the-street block group is also F; in NC/VA (thin funnel), OUT only when Robbery is F and Burglary or Vandalism is F too. The two flags (Murder F, Drug F) never knock out; they ride into file 14 for the review stage's address-level checks (incident points within 150 m, shootings within 250 m, calls at the address).
5. **`underwrite`.** Replace `crime_pen` with a term on the Robbery position (for example −3 × (position − 0.6) / 0.4, floored at 0, which reproduces the old −3 at F and −1 near D), and the 8 percent vacancy rule with Robbery F. File 14's `crime` column becomes the six readings in one cell (`R .94 F / A .98 F / B .93 F / V .80 D; M F, D A+`) or six columns, with `why` naming the penalty as before.
6. **Refresh.** Once a year, or when CrimeGrade's data window moves; nothing weekly.

## 5. How the condition gate and the crime gate combine

The novice grade should stay where it is (after the detail fetch, on the photo the detail page serves) and be read only for rows that survived the crime knockout. Nothing about the grade itself changes. What changes is what a reader sees on the board: a YELLOW row in a B block outranks a GREEN-verify row in an F block on the score once the position term replaces the letter term, which is the ordering a first-time out-of-state owner wants; file 08's YELLOW is "inspect and bid, bids at or under 10 percent", a cost that is known before closing, while an F block is a cost that is paid for the life of the hold. The 14 GREEN rows remain the right first candidates for interior reads and the address-level crime checks, but as an output of the two gates, not as the input to one of them.

## 6. Unknown unknowns that bear on the placement

1. **The crime layer changes the ZIP lists, not only the rows.** Once the block-group table exists, a ZIP whose block groups are all F on Robbery can leave the sweep list (saving its list pages and detail slots), and a ZIP the ZIP letter condemned can stay because half its blocks pass. Memo 65 §2 already wants 29 zero-row ZIPs swapped; the crime table is the second reason to edit the lists.
2. **The detail queue is the lever.** Fifty slots a region a week against backlogs of 237, 268 and 285 rows: a free gate applied before those slots is worth more than any change to the score. Crime at `ingest` spends the slots on rows that can survive; crime at review time spends them first and asks afterwards.
3. **Side of the street is automatable.** The reader already reports the across-the-street block group and its distance; the `--check-side` OpenStreetMap house point resolves it. Apply it at `ingest` to any row within 15 m of a boundary with a different letter, so no knockout fires on a boundary case.
4. **Map coverage is not ZIP coverage.** The ZIP-page map at its default zoom leaves the edges of large ZIPs off the image (Varsity Dr fell off the 28304 page); a listing off every map gets "maps needed" and a panned view is shot for it. `grade_by_view.py` handles several views per ZIP.
5. **Possible double counting with Gate 1.** The tract model and block-level crime both track neighbourhood income. Before the position term goes into the score, measure the correlation between tract tier and Robbery position on the rows that carry both; if it is high, the crime term should be smaller than the old letter penalty, not equal to it.
6. **Cleveland and Philadelphia saturate.** Every Cleveland and Philadelphia row read F on nearly all nine tabs, and the validation found half of Cleveland's block groups F. CrimeGrade cannot rank candidates inside those cities; the recorded-incident feature services (Cleveland Division of Police, OpenDataPhilly) can, and that ranking is a review-stage task on the survivors, not a sweep task.
7. **Same block group, same reading.** Three Fayetteville rows, two Rocky Mount rows, two Troy Ave rows and three Diven Ave rows read identically on all nine tabs because they share a block group. The map cannot separate siblings; only address-level data can.
8. **The retired letters are still in the board.** 136 `crime` cells, the `why` arithmetic on every scored row, the vacancy assumption on F rows and step 8 of four task prompts all use the Overall letter. Retiring it is a pipeline change with a backup and a re-score, not a column edit.
9. **The advisory loop should receive the vector, not re-derive it.** Memo 67 found the deep reviews re-deriving facts the board already held; the six readings and the two flags should be in the packet each review starts from.
10. **Time budget.** The 24 active-row ZIPs without any map (NC and PA mostly) are about an hour and a half of screenshots; the full 400-ZIP layer is about a day, and it need not be built at once: shoot the ZIPs the sweep names each week and the layer converges on the ZIPs that produce candidates.

## 7. This week

1. Shoot the six tabs for the 24 active-row ZIPs without a map (list in §6 item 10; `15022, 15132, 15136, 15210, 15902, 16101, 18510, 19141, 19143, 21502, 23601, 27101, 27320, 27520, 27603, 27801, 27864, 27893, 28021, 28214, 28303, 28311, 28352, 28390`), then the remaining tabs for the 34 ZIPs that have Robbery only.
2. Build `crime_bg.json` from every map on hand (the cloud session can do this from the batch as soon as it is uploaded).
3. Decide the two thresholds in §4 item 4 and the score term in item 5; then the `ingest` join, the "maps needed" list and the `underwrite` change go in together with a backup of file 14 and a one-time re-score of the 122 active rows.
4. Keep the 14 GREEN rows as the first review set, now ordered by their Robbery position rather than by their grade.
