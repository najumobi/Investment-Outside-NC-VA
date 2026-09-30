# Crime on the board and in the sweep: block-level cells in file 14, the re-score, and the pipeline change (2026-09-30)

Written 2026-09-30 (cloud session) after Najum's go-ahead to put the block-level crime readings on the board, correct the two ZIPs, and make whatever Dropbox changes the protocol of memo 69 needs, without moving the folder the routines run from. Everything below was written to Dropbox with a backup beside it and mirrored to the repository; `70a Crime cells, why notes and re-scores, 206 rows before and after (2026-09-30).csv` holds every changed cell of file 14.

## 1. What changed in file 14

File 14 (206 rows, 188 active) was rewritten once, byte for byte except the intended cells; the copy from before the change is `_pipeline/_backup_14_before_0930crime.csv`.

- **Two addresses corrected.** 814 Varsity Dr now reads 28301 and 556 Bellwood Rd 23601, which is where the Census geocoder and each row's own listing put them.
- **The `crime` column.** For the 191 rows whose block group has been read (173 of the 188 active rows), the cell is the six-tab reading in one grammar: `R .89 D- / A .93 F / B .89 D- / V .96 F; M D-, D D (9/30)`, that is Robbery, Assault, Burglary and Vandalism as legend position (0 = A+, 1 = F) and letter, Murder and Drug as letters, and the date of the read. For the 15 rows with no reading the cell says why: `zip C- retired 9/30; block maps needed` for a ZIP with no map yet, or `off the 15666 page map to the north (pan and re-shoot)` where the map exists but the house lies outside it.
- **The `why` column.** The old term `crime D -1` became `crime R .78 D -1.4` (position, letter, penalty); rows with a reading better than C+ carry `crime R .27 B+ 0`; every row that had a ZIP letter carries `zip letter D retired 9/30` at the end so nothing was lost.
- **The `score` column.** 157 rows moved. The new penalty is 3 x (Robbery position - 0.6) / 0.4, floored at zero: nothing at C+ and better, about 1 at D+, 2 at D-, 2.6 in the middle of F. Each score was recomputed as old score + old letter penalty - new penalty, so the swap is exact for the penalty and touches nothing else. Two things were not recomputed and should be when a row is next underwritten: the 8 percent vacancy rule (it used the ZIP letter F, it now uses Robbery F) and the knockout in section 2, which was not applied to rows already on the board. The largest moves were rows in F-letter ZIPs whose block reads better (Conover Rd -2.9 to -0.9) and rows in C-letter ZIPs whose block reads D- or F (Slack St 53.2 to 50.7).

## 2. What changed in the sweep

`_pipeline/weekly_sweep.py` was patched by `pipeline_changes/2026-09-30-crime/_pipeline/patch_weekly_sweep_0930.py` (backup `_pipeline/_backup_weekly_sweep_before_0930crime.py`; the patched file compiles and its helpers were tested against the table before it was written).

- The crime input is `_pipeline/model/crime_bg.json`: 4,432 block groups (4,399 with all six tabs), each with its legend position per tab, built from every screenshot batch so far by `_pipeline/crimegrade/build_crime_bg.py`. A listing is looked up by the first twelve digits of the block the Census geocoder returns; `ingest` now keeps that block beside the tract (`model/geo_cache_bg.json`), and an address geocoded before today gets one call to the one-line geocoder, cached.
- `ingest` reads the block for every row that could reach the detail queue (new, relisted, price-cut or detail-pending, no other knockout, under the practical ceiling), writes `block_group`, `crime_R` and `crime_cell` into `scored.csv`, knocks out a row whose Robbery is F and whose Burglary or Vandalism is also F (the second tab stands in for memo 69's across-the-street check until the table carries adjacency), sorts the remaining Robbery-F rows behind the rest of the detail queue, and prints `## Crime maps needed` with the ZIPs on the shortlist that no map covers.
- `underwrite` scores the Robbery position with the penalty above, applies the 8 percent vacancy at Robbery F, gives a Robbery-F-plus-Burglary-or-Vandalism-F row the verdict `OUT (crime)` (not folded), writes the six-tab cell into file 14's `crime` column when it folds or re-scores a row, keeps the old letter in `results.csv` as `crime_zip` for reference, and lists `<ZIP>: crime maps needed` under "Constants needed" instead of asking for a CrimeGrade letter. The automated letter fetch is gone.
- The five task prompts (`weekly_task_prompt_TEMPLATE.md`, `_ncva`, `_phila`, `_pitt`, `_ohio`; backups beside them) say in step 8(a) that a "crime maps needed" line is a request for Najum's screenshots, not a workbench fetch, and no longer mention `constants.json` `crime_zip`. Najum pastes the prompts into the routines as before.

## 3. Where the pieces live

| | Dropbox (the routines' folder) | Repository |
|---|---|---|
| Reader, labeller, batch reader, table builder, overlay check, packager | `_pipeline/crimegrade/` | `pipeline_changes/2026-09-29-crimegrade/_pipeline/crimegrade/` |
| Block-group table the sweep reads | `_pipeline/model/crime_bg.json` | `pipeline_changes/2026-09-29-crimegrade/model/crime_bg.json`; the full per-view table with provenance is `crime_bg_2026-09-30.csv` / `.json.gz` beside it |
| Screenshot batches read so far (manifests, readings, matrices) | not on Dropbox; the images are in Najum's zips | `pipeline_changes/2026-09-29-crimegrade/types_*` and `crimegrade_types_*` |
| The patched sweep and the patch | `_pipeline/weekly_sweep.py` | `pipeline_changes/2026-09-30-crime/_pipeline/` |
| Memos 69 and 70, the 70a change log | campaign root | repository root |

## 4. What the local session should do next

1. Before the Thursday routine, run `weekly_sweep.py underwrite --date=2026-09-30 --region=pitt --dry` against the 9/30 pitt run folder: it exercises the new code end to end on real inputs (the cloud session could compile and unit-test it, not run it, because the script's paths are the PC's). Expect `crime R ...` terms in `why`, `crime_cell` and `block_group` in `results.csv`, and a "crime maps needed" line for 15066, 15120, 15203, 15204, 26062, 26301 and 44446.
2. When a batch of screenshots arrives, the cloud session labels, fits and reads it and pushes the new `model/crime_bg.json` to Dropbox; nothing in the routines changes.
3. Optionally `underwrite --rescore` on the 9/30 pitt rows, which also applies the vacancy rule and the knockout to them; the by-hand re-score in section 1 only swapped the penalty term.

## 5. Still open

- 23601 (556 Bellwood Rd) needs the six tabs shot with the map dragged up; the ZIPs of this morning's Pittsburgh entrants without a map are 15066, 15120, 15203, 15204, 26062, 26301 and 44446; 15666, 28390, 26101 and 13760 each have one row that lies just off the page map (the cell in file 14 says which way to pan).
- The knockout uses two tabs in place of the across-the-street check; a future table build can add each block group's neighbours so the rule reads as memo 69 wrote it.
- The score of a row already on the board reflects the new penalty only; the vacancy rule and the knockout apply when the row is next underwritten.
