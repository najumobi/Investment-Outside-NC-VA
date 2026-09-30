# Block-group validation of CrimeGrade's Robbery colours (2026-09-30)

Question: do the block-group colours on CrimeGrade's Robbery maps track robberies the police actually recorded?

## Method

- Every block group lying inside a Robbery screenshot was read the same way the address pipeline reads one (median legend position of the pixels inside the polygon, drawn 2 px inside its edge, UI and legend excluded). Block groups with fewer than 150 residents (2020 Census) were dropped.
- Philadelphia: the two Robbery screenshots (19139, 19131), 341 block groups. Recorded robberies from OpenDataPhilly `incidents_part1_part2` (Carto SQL API), 2024-01-01 to 2025-12-31, `text_general_code LIKE 'Robbery%'`, point-in-polygon into 2020 block groups (`rob_19139.json`, `rob_19131.json`).
- Cleveland: nine Robbery screenshots (44102, 44103, 44104, 44105, 44106, 44108, 44109, 44110, 44120), 577 block groups. Recorded offences from the Cleveland Division of Police `Crime_Incidents` feature service (2016 to 2025-11-11), which carries `CENSUS_BG_GEOID` on every row; 2024 plus 2025 to Nov 11 (1.86 years) in `cle_counts_2024_25.json`, full calendar years 2023 and 2024 in `cle_counts_by_year.json`.
- Block-group polygons and 2020 populations from TIGERweb (`Tracts_Blocks/MapServer/11`); `bg_cuyahoga.geojson.gz` holds all 1,185 Cuyahoga block groups, `bg_19139.geojson` and `bg_19131.geojson` the ones under the two Philadelphia maps.
- `validate_blockgroups.py` reproduces `results_bg.csv` (one row per city and block group: mean legend position over the maps that show it, spread between maps, letter, recorded count, rate per 1,000) and `summary.json`. The year-to-year figures in `reliability.json` came from the same counts split by calendar year.

## Results

| | Philadelphia | Cleveland |
|---|---|---|
| Block groups read (pop >= 150) | 341 | 577 |
| Recorded robberies, 2024-25 | 1,486 | 2,513 |
| Spearman, colour position vs recorded rate | 0.47 | 0.66 |
| Same, vs a 700 m population-weighted smoothed rate | 0.49 | 0.68 |
| Block groups shown on two or more maps | 99 | 382 |
| Median difference in position between maps | 0.000 | 0.000 |
| Block groups coloured F | 114 (33%) | 284 (49%) |
| F block groups with a rate below the city median | 32% | 23% |
| F block groups with no recorded robbery in two years | 17% | 13% |
| Block groups in the top fifth of recorded rates coloured F | 65% | 86% |
| ... coloured D- or F | 93% | 97% |
| Spearman within the F band only | 0.22 | 0.36 |
| Year-to-year Spearman of recorded block-group counts (noise floor) | 0.67 (2024 vs 2025) | 0.71 (2023 vs 2024) |
| Colour vs a single year of recorded rate | 0.46 (2024), 0.39 (2025) | 0.60 (2023), 0.62 (2024) |

Median recorded rate per 1,000 by colour band, Cleveland: D+ 0.0, D 0.0, D- 1.5, F 3.6 (interquartile 1.5 to 6.5). Philadelphia: D+ 0.8, D 1.4, D- 1.8, F 2.8 (0.9 to 4.5).

Cleveland block-group statistics for the other categories (505 city block groups with 150 or more residents, 2024 to Nov 2025, annualised):

| Category (CDP label) | Per block group per year | Block groups with none in 1.86 yrs | Share held by the top 10% of block groups | Year-to-year Spearman (2023 vs 2024) |
|---|---|---|---|---|
| Homicide | 0.21 | 71% | 51% | 0.43 |
| Robbery | 2.8 | 24% | 38% | 0.71 |
| Felonious assault | 4.7 | 18% | 31% | 0.78 |
| Assault (all) | 32.9 | 13% | 27% | 0.91 |
| Burglary | 6.3 | 20% | 29% | 0.79 |
| Theft | 17.5 | 15% | 35% | 0.87 |
| Motor vehicle theft | 7.6 | 18% | 29% | 0.78 |
| Arson | 0.37 | 60% | 45% | 0.18 |
| Vandalism | 16.6 | 16% | 32% | 0.86 |
| Drug abuse violations | 1.5 | 27% | 41% | 0.42 |
| Weapons | 4.1 | 19% | 35% | 0.75 |
| Rape | 0.9 | 39% | 41% | 0.32 |

Spearman correlations between per-1,000 rates across those block groups: robbery with felonious assault 0.81, assault 0.80, burglary 0.77, theft 0.76, vehicle theft 0.75, vandalism 0.78; homicide with everything 0.13 to 0.38; arson 0.26 to 0.49; drug violations 0.33 to 0.62.

## Reading

- The colours carry real information: the top fifth of block groups by recorded robbery rate is almost always coloured D- or F, and the median recorded rate rises band by band.
- They are noisy at the bottom of the scale. About one F block group in four has a recorded rate below its city's median, and one in six or seven had no recorded robbery in two years. In Cleveland half of all block groups are F, so the letter alone separates little; the continuous position keeps some order inside F (0.36).
- The noise floor is the data itself: a year of recorded robberies predicts the next year's block-group ranking at about 0.7, and a two-year count of a few robberies per block group is a small sample. CrimeGrade's colour predicts a single recorded year at 0.6 in Cleveland, close to that ceiling, and at 0.4 to 0.46 in Philadelphia.
- Robbery, assault, burglary, theft, vehicle theft and vandalism rank block groups almost identically (0.75 to 0.89); at this scale they are one signal. Homicide, arson, drug violations and rape are sparse, concentrated in a few block groups, and do not repeat year to year (0.18 to 0.43), so their block colours are flags for a handful of places, not a gradient.
