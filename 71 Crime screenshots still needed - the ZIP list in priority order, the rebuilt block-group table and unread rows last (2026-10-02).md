# Crime screenshots still needed: the ZIP list in priority order, the rebuilt block-group table and unread rows last (2026-10-02)

Written 2026-10-02 (cloud session) in answer to Najum's "List all the zip codes you need screenshots for." The list itself is `71a Crime screenshots still needed, ZIP by ZIP in priority order (2026-10-02).csv`: one row per ZIP, with the addresses that make it urgent, how many of its current listings are still unread, and the CrimeGrade page to open. Everything below was also written to Dropbox, with a backup beside each replaced file.

## 1. Answer first

Of the 400 ZIPs in the four sweep lists, 92 have been shot with all six tabs and 308 have not. Only 58 of the 308 hold a row that is waiting on a reading today, and they are the ones to shoot first. One more ZIP needs a re-shoot rather than a first shot: the house at 208 Scarborough St, Spring Lake, lies about 2 km south of the 28390 page map, so that page needs to be panned south and shot again.

## 2. How the list is ordered

The priority follows what each screenshot unlocks.

1. **Board (12 ZIPs and the 28390 re-shoot).** Each holds an active file-14 row with no block-level reading, so its crime column says "maps needed" and its score carries no crime term. They are 15066, 26301, 15120 and 44446 in the Pittsburgh region and 45503, 44123, 44305, 44306, 44146, 45324, 44203 and 43812 in Ohio.
2. **Detail queue (34 ZIPs).** Each holds a listing that passes the money gates and is waiting for its detail page. Under the patch in section 5, such a row now waits behind every row that has a reading, so a screenshot taken before that region's next run moves it up the queue.
3. **Passed the money gates before (12 ZIPs).** Each holds a listing that passes the money gates but has already been through the detail stage. It comes back only on a price cut or a relisting.
4. **Other sweep ZIPs with unread listings (158).** These are ordered in the file by how many of their current listings are unread. Atlantic City 08401 (33), Philadelphia 19148 (29) and 19145 (21) lead.
5. **Sweep ZIPs with no listings today (30).**
6. **Covered already (62).** Every current listing in these ZIPs already reads through a neighbouring ZIP's page. They can wait until a listing lands in a part of the ZIP no page covers. Most are in Philadelphia, where ZIP pages overlap heavily.

At memo 69's pace of about four minutes a ZIP, the first three groups take about four hours and all six about twenty.

## 3. The block-group table, rebuilt

`build_crime_bg.py` had used limits set for the block-group validation. It kept only block groups with at least 300 pixels on the legend ramp and at least 60 percent of their bounding box on the map. Those limits left dense blocks unread even where the address reader could read them, and they left out every large block group that is only partly on a map. The reader now takes a block group with 40 or more ramp pixels. Below 300 pixels it must read as one colour (an interquartile range of 0.08 or less), so that a sliver tinted by a neighbour is not taken. A block group partly off the map is read from the part that shows, since CrimeGrade fills each block group with one colour. Block groups under 150 residents are still skipped.

The rebuilt table covers the same six batches. It holds 5,623 block groups, of which 5,589 have all six tabs; the old table held 4,432. None of the 4,432 earlier block groups changed letter on any tab. 23 Burglary positions and one Murder position moved by less than 0.02, because a view that had been under the old limit now adds its reading to the mean. Every Robbery reading already on the board, 195 rows in all, matches the table.

## 4. The board

Eight file-14 rows that had no reading now have one. Each row's crime cell, score and why note were changed the same way as in the 9/30 pass (memo 70 section 1): the crime penalty was swapped and nothing else changed. Four of them are read through another ZIP's page:

- 3536-3538 Orchard St, Weirton, is read through the 43952 page. Robbery is B, and the score stays 13.1.
- 3427 Clearfield St, Pittsburgh, is read through the 15136 page. Robbery is D+, and the score goes from 5.3 to 4.1.
- 1818 Mary St, Pittsburgh, is read through the 15210 page. Robbery is D-, and the score goes from -5.4 to -7.1.
- 556 Bellwood Rd, Newport News, is read through the 23607 page. Robbery is F, but Burglary is C and Vandalism D-, so the NC/VA knockout does not apply. The score goes from 3.8 to 4.3, because the retired ZIP letter's -3 gives way to -2.5.

The other four are read under the new limits:

- 14 Rear Railroad St, Plymouth, is read through the 18651 page. Robbery is C, and the score stays -5.2.
- 408-410 Pump Hill Pl, Mount Pleasant, is read from a block group that extends onto the 15666 map. Robbery is C, and the score goes from 2.1 to 2.0.
- 6198 State Route 17c, Endicott, is read the same way from the 13760 map. Robbery is A, and the score stays -9.3.
- 603 33rd St, Parkersburg, which is off market, is read the same way from the 26101 map. Robbery is D-, and the score goes from -4.3 to -6.6.

None of the eight meets the knockout. The board is now sorted the way the patched sweep sorts it (section 5).

## 5. Unread rows last

Memo 69 section 4.3 says a listing whose block group no map covers "is folded below rows that have a reading". The two 9/30 patches wrote the "maps needed" cell but still sorted such a row by its score alone. Because an unread row carries no crime term, it outranked rows that had a reading; 979 Lagonda Ave, folded by the 10/1 Ohio run at 0.1, is the example. `patch_weekly_sweep_1002.py` adds `crime_rank()` and uses it in three places:

- In the detail queue, within each rent-to-price band group, rows read better than Robbery F come first, then Robbery-F rows, then unread rows.
- In the verdict list, within each verdict, unread rows come after rows that have a reading.
- In file 14, within the active rows, unread rows come after rows that have a reading.

Scores, verdicts and knockouts are unchanged. The run report's "Crime maps needed" line now also says how many shortlist rows are waiting behind the read ones.

## 6. Files

| What | Dropbox | Repository |
|---|---|---|
| Block-group table the sweep reads | `_pipeline/model/crime_bg.json` (backup `_backup_crime_bg_before_1002.json`) | `pipeline_changes/2026-09-29-crimegrade/model/crime_bg.json` |
| Full table, one row per block group | | `pipeline_changes/2026-09-29-crimegrade/crime_bg_2026-10-02.csv` and `.json.gz` |
| Table builder | `_pipeline/crimegrade/build_crime_bg.py` | `pipeline_changes/2026-09-29-crimegrade/_pipeline/crimegrade/build_crime_bg.py` |
| Sweep with unread rows last | `_pipeline/weekly_sweep.py` (backup `_backup_weekly_sweep_before_1002crime.py`) | `pipeline_changes/2026-10-02-crime/_pipeline/` |
| File 14 | live file (backup `_pipeline/_backup_14_before_1002crime.csv`) | `pipeline_changes/2026-10-02-crime/board_changes_1002.json` (the eight rows, before and after) |
| Status of every board, queue and money-passing row | | `pipeline_changes/2026-10-02-crime/row_status_2026-10-02.csv` |

`grade_by_view.py` no longer sends Najum's email address in its request header to OpenStreetMap's geocoder.

## 7. The 8:20 AM batch of 2026-10-02

Najum's first batch against the list covered 49 ZIP pages from the fourth group: 15 in NC/VA, 19 in the Pittsburgh region and 15 in the Philadelphia region. After it, 138 of the 400 sweep ZIPs are complete. The board is unchanged, because its 14 unread rows are all in group-1 ZIPs, which this batch did not cover.

Twelve detail-queue rows became readable through neighbouring pages: two in Hazleton, two in Ambridge, two in Braddock, two in Verona and four on Pittsburgh's North Side. None of them meets the knockout. Seven other money-passing listings became readable too.

71a is regenerated:

- Group 1 is unchanged.
- A new group 1b lists the three pages this batch left incomplete: 19111 needs Robbery, Vandalism, Murder and Drug; 24401 needs Vandalism; 27215 needs Drug.
- Group 2 falls to 29 ZIPs, group 3 to 11 and group 4 to 103.
- 74 ZIPs are now covered through other pages.

The batch was taken in a wider window, and six of its shots have no street layer. How both were handled is in `pipeline_changes/2026-09-29-crimegrade/README.md`.

## 8. The 12:46 and 12:48 PM batches of 2026-10-02

The two afternoon batches covered 103 more ZIP pages from the fourth group, finished 19111, 24401 and 27215, and completed 27704 between them. After them, 229 of the 400 sweep ZIPs are complete and the table holds 10,635 block groups.

One board row gained a reading: 896 Huber St, Akron, reads through the neighbouring Akron pages. Its Robbery is C (.61), it does not meet the knockout, and its score moves from -5.3 to -5.4 on the penalty swap. The board was sorted again with the sweep's key, which moves the row up from among the unread rows. Seven detail-queue rows became readable (four in Warren, two in Canton, one in Painesville), and none of them meets the knockout.

71a is regenerated:

- Group 1 has 11 ZIPs, since 44306 left it.
- Group 1b lists nine pages that came in short of tabs.
- Group 2 has 26 ZIPs, group 3 has 10 and group 4 has 16.
- 30 ZIPs have no listings, and 69 are covered through other pages.

None of the group 1, 2 or 3 ZIPs has been shot yet; they are the ones the board and the weekly runs depend on.

## 9. The 9:20 PM batch of 2026-10-04

Najum shot the list in order, starting with the board, and every active row of file 14 now has a block-level reading. The 13 board rows this batch read were updated in the same way as the earlier ones (`pipeline_changes/2026-10-02-crime/board_changes_1004.json`), and the board was sorted again with the sweep's key. Two of them now meet memo 69's knockout, which brings the board's count to 35 of 207 active rows:

- 208 Scarborough St, Spring Lake, now on the re-shot map, is F on every tab.
- 1242-1244 Laird St, Akron, is Robbery F with F across the street.

1600 Mcclure St, Homestead, is Robbery F, but the block across the street is better, so it does not meet the knockout. Most of the batch's pages lack only Drug-Related Crime, because Overall Crime was shot in its place. Drug is a flag with no part in the knockout or the score, so those rows read normally, and their cells carry Murder but not Drug.

In the detail queue, 201 of 204 rows are now readable, and 25 of them will leave the queue at their region's next run. The other three lie just south of their page maps: two in Springfield (45503), 0.6 and 0.7 km off, and one in Akron (44319), 1.7 km off.

71a and 71b are rewritten in a new order:

1. The two pan re-shoots.
2. The four group-3 ZIPs left.
3. The 16 group-4 ZIPs.
4. Six pages missing a tab other than Drug.
5. The Drug tab for 40 pages.
6. The 101 ZIPs that can wait.

After this batch 233 of the 400 sweep ZIPs are complete, and the table holds 11,969 block groups.
