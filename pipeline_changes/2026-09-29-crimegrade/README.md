# 2026-09-29: CrimeGrade grades at a street address

The campaign has so far used CrimeGrade's ZIP-level letter (file 09 and the `crime` column of file 14). This folder adds a way to read a CrimeGrade grade at the address itself, from CrimeGrade's own map, and records the first 25 Ohio addresses read with it, for Overall Crime and for Robbery. File 14 is untouched.

## Files

- `_pipeline/crimegrade/grade_addresses.py` — entry point: a CSV of addresses and map images in, a CSV of grades out.
- `_pipeline/crimegrade/georef.py` — lines a map image up with the ground by matching its white streets to Census TIGER street centrelines.
- `_pipeline/crimegrade/colour_read.py` — reads the fill colour of the address's census block group and turns it into a grade.
- `_pipeline/crimegrade/ramp.json` — the legend's colour ramp, sampled pixel by pixel from a ZIP-page screenshot.
- `_pipeline/crimegrade/requirements.txt` — numpy and Pillow.
- `addresses_ohio_2026-09-29.csv` — the 25 Ohio addresses graded on 2026-09-29 and the map image each was read from.
- `crimegrade_overall_ohio_2026-09-29.csv` — their Overall Crime results, as written by the committed scripts.
- `addresses_ohio_robbery_2026-09-29.csv` — the same addresses with the Robbery screenshot each was read from; Dayton appears twice, read from two screenshots taken at different window sizes, as a check.
- `crimegrade_robbery_ohio_2026-09-29.csv` — their Robbery results.
- `addresses_vawv_robbery_2026-09-29.csv` — the 33 Virginia and West Virginia rows of file 14 as of 2026-09-29, with the address sent to the geocoder, the Robbery screenshot each was read from, and the row's current `crime` letter.
- `crimegrade_robbery_vawv_2026-09-29.csv` — their Robbery results. File 14 lists 556 Bellwood Rd, Newport News, under 23607, but the Census geocoder and the row's own Redfin link put it in 23601, so it was read from a 23601 screenshot.
- `addresses_green_robbery_2026-09-29.csv` — the 15 addresses on the 2026-09-29 photo list, with the address sent to the geocoder and the Robbery screenshot each was read from. Twelve screenshots are new; 306 & 308 Troy Ave NE, 1934 Oakland St and 1021 Penmar Ave SE reuse the Virginia maps. 4902 Kershaw St, Philadelphia, is not in file 14.
- `crimegrade_robbery_green_2026-09-29.csv` — their Robbery results. File 14 lists 814 Varsity Dr, Fayetteville, under 28304, but the Census geocoder and the row's Redfin link put it in 28301, north of the 28304 map, so it was read from a 28301 screenshot.
- `.gitignore` — keeps the map images (`maps/`) and the scripts' cache out of the repository.

The map images are not committed and the scripts never download from CrimeGrade. The images are CrimeGrade's, and its terms prohibit automated scraping without a license, so each map is saved by hand.

## How to run

1. Python 3 with numpy and Pillow (`pip install -r _pipeline/crimegrade/requirements.txt`), and internet access to `geocoding.geo.census.gov` and `tigerweb.geo.census.gov`; `--check-side` also uses `nominatim.openstreetmap.org`.
2. For each ZIP, open `https://crimegrade.org/safest-places-in-<ZIP>/`, right-click the map and save the image into `maps/`, for example `maps/44104.png`. A screenshot of that map, or of the interactive map, also works as long as it shows the streets around the address. The legend, the map buttons, the "Click the map to explore" band, a browser address bar and page margins are ignored automatically. For a single crime, open the ZIP page with that crime in the address, for example `https://crimegrade.org/safest-places-in-44104/?crime=robbery`, and screenshot the map; it uses the same A+ to F legend, so the scripts read it unchanged.
3. List the addresses in a CSV with columns `id,address,image`, the image path relative to the CSV. `addresses_ohio_2026-09-29.csv` is an example.
4. Run `python3 _pipeline/crimegrade/grade_addresses.py addresses.csv results.csv --check-side`.

The first run on a map takes one to two minutes, mostly the street download and the zoom search. Streets, block groups, geocodes and map alignments are cached in `_pipeline/crimegrade/cache/`.

## Output columns

- `grade` — the reading: the block group's median legend position, split into thirteen equal bands.
- `position` — where that colour sits on the legend, 0 at the A+ end and 1 at the F end. `position_iqr` is its spread inside the block group; `at_address_position` is the median within a few pixels of the address.
- `label_anchored_grade` — the alternative reading described under Caveats.
- `edge_distance_m`, `neighbours_within_60m` — how close the address is to another block group, and that group's grade.
- `side_check` — the OpenStreetMap house check, when it ran.
- `note` — flags: a different grade across the street, a position on a grade line, the two readings disagreeing, or a weak street match.

## Method

1. **Geocode.** The Census geocoder returns the coordinates and the 2020 census block; the block's first twelve digits are its block group.
2. **Georeference.** CrimeGrade draws its maps in Web Mercator, so an image is fixed by one zoom and one offset. For each zoom from 12.3 to 14.8, TIGER street centrelines are drawn around the address and slid across the image's white-street mask; the zoom and offset with the highest normalised cross-correlation win. A coarse pass runs at half resolution in steps of 0.04 zoom, then a full-resolution pass refines in steps of 0.005. The saved ZIP-page maps came out between zoom 12.85 and 14.1.
3. **Read.** CrimeGrade fills each census block group with one colour: its colour edges follow block-group lines, and the spread inside a group is small. Every pixel inside the address's block-group polygon, drawn 2 px inside its edge, is placed on the legend ramp. Pixels more than 6 colour units from the ramp are dropped, which removes streets, anti-aliased street edges, labels, the watermark and the darkened overlay band. The median position is the reading.
4. **Grade.** CrimeGrade's thirteen grades are equal percentile bands, A+ above the 92.31st percentile down to F below the 7.72nd, so the ramp is split into thirteen equal bands.
5. **Side of the street.** Where the street in front of the house divides two block groups with different grades, `--check-side` looks the house up in OpenStreetMap and reads the block group that contains the house point.

## Validation, 2026-09-29

- Street matching reproduced a label-based alignment of the Canton 44710 map to within 1.6 px, and put five Akron 44320 neighbourhood labels within 1 px of their OpenStreetMap positions.
- Block-group outlines drawn on the Canton, Cleveland 44120, 44106 and 44102 and Toledo 43605 maps follow the streets and the colour edges.
- Screenshots and saved maps give the same grades. Screenshots of the interactive map for Cleveland 44104, Dayton 45405 and Akron 44320, and of the Canton 44710 ZIP-page map, gave F, F, D-, F and D for Sophia Ave, Manor Ave, Pointview Ave, Work Dr and Ingram Ave SW, as the saved maps did, with legend positions within 0.002.
- The five houses on a dividing street (Garfield Heights, W 90th St, W Sylvania Ave and both Starr Ave addresses) each have an OpenStreetMap house point in the block group the Census geocoder assigned.
- Robbery: the 19 Robbery screenshots aligned with street-match scores between 0.51 and 0.77. The Dayton map, screenshotted twice at different window sizes, read D at 0.799 both times. Block-group outlines on the Martins Ferry, Toledo 43605 and 43612 and Canton Robbery maps follow the colour edges, and the six Robbery side-of-street checks each confirm the geocoder's side.
- Robbery, Virginia and West Virginia: the 21 screenshots aligned with scores between 0.46 and 0.79. Block-group outlines on the Roanoke 24012, Parkersburg 26101, Suffolk 23434, Petersburg 23805 and Blackstone 23824 maps follow the colour edges. Four side-of-street checks confirm the geocoder's side; 515 Albemarle Ave SE has no OpenStreetMap house point, and the block group across its street is also in the C family.
- Robbery, photo list: the 12 new screenshots aligned with scores between 0.56 and 0.80. Re-read from new screenshots, 3446 E 125th St, 312 N 7th St, 9816 Manor Ave and 3601 Memphis Ave gave the same grades and legend positions as the first Robbery screenshots. On the Johnstown 15906 map, the TIGER centreline of Naylor Rd lies on the map's street. 299 Robinson St, Binghamton, is on a street dividing an A+ block group from a D- one; its OpenStreetMap house point is in the A+ group the Census geocoder assigned.

- Robbery, block-group validation (2026-09-30): `validation/` reads every block group under the Philadelphia and Cleveland Robbery screenshots and compares the colour with robberies the police recorded in 2024-25. Spearman 0.47 (Philadelphia, 341 block groups) and 0.66 (Cleveland, 577), against a year-to-year noise floor of about 0.7; about one F block group in four has a recorded rate below its city's median. Details and the other categories' block-group statistics are in `validation/README.md`.

## Nine crime types from tab-by-tab screenshots, 2026-09-30

`types_sample_manifest_2026-09-30.csv` lists 206 screenshots of the ZIP-page map taken tab by tab (Assault, Robbery, Burglary, Vandalism, Theft, Vehicle Theft, Drug-Related Crime, Arson, Murder) for 22 ZIP pages: the 15 photo-list ZIPs plus 13760, 13790, 13901, 13903, 13905, 14830 and 14892. `_pipeline/crimegrade/label_screenshots.py` grouped them by the tab label, the ZIP in the header line and the map view; two shots caught the tab bar before its label rendered and are typed by elimination (Drug-Related Crime for 14830, Assault for 14901). `_pipeline/crimegrade/grade_by_view.py` fitted each of the 27 map views once (street-match scores 0.43 to 0.66) and read every tab for every address on the map: `crimegrade_types_sample_readings_2026-09-30.csv` holds the 781 readings, `crimegrade_types_sample_2026-09-30.csv` the 43 addresses (15 photo-list, 28 other file-14 rows in those ZIPs) by type. The Robbery readings equal the 2026-09-29 readings to three decimals for all 15 photo-list addresses, and an address seen on two views reads the same on both (171 pairs, spread 0.000). No file-14 address lies on the 13760 or 14892 pages. Images are in `maps/types_sample/` (not committed).

## Six-tab batch of 2026-09-30 (5:10 AM) and the block-group table

`types_batch510_manifest_2026-09-30.csv` lists 158 screenshots: 26 ZIP pages with the six tabs of the protocol (Robbery, Assault, Burglary, Vandalism, Drug-Related Crime, Murder). 32 views were fitted (street-match scores 0.25 to 0.64; the three rural views under 0.4, Tamaqua 18252, Dickson City 18519 and Spring Lake 28390, were checked with `_pipeline/crimegrade/overlay_view.py` and follow the colour edges) and read for 264 readings on 38 addresses (`crimegrade_types_batch510_readings_2026-09-30.csv`, `crimegrade_types_batch510_2026-09-30.csv`). Two things were set aside: the 44125 Drug tab was shot with the "More" dropdown open over the map and off the page zoom, and the 43612 six-tab set was shot with the map rotated about ten degrees, which the north-up georeferencer cannot fit (its later Assault and Robbery shots are fine); both need re-shooting north-up at the page zoom.

`crime_bg_2026-09-30.csv` and `.json.gz` are the block-group table memo 69 asks for: `_pipeline/crimegrade/build_crime_bg.py` read every 2020 block group under every fitted view of the three batches (3923 block groups with at least one tab, 3907 with all six), and a block group seen on two views reads identically on every tab (7476 pairs, median spread 0.000, largest 0.000). An address is looked up by the first twelve digits of the block the Census geocoder returns. Images are in `maps/types_batch510/`, `maps/types_batch1001/` and `maps/types_batch23601/` (not committed).

## Six-tab batch of 2026-09-30 (10:01 AM) and the 23601 set

`types_batch1001_manifest_2026-09-30.csv` lists 300 screenshots: 48 ZIP pages with the six tabs (the 16 active-row ZIPs that had no map, the 15 Virginia and West Virginia ZIPs that had Robbery only, the 43612 and 44125 re-shoots, and 15 more sweep ZIPs in Philadelphia, Wilkes-Barre, Danville, Winston-Salem, Eden and Reidsville). 48 views were fitted and read for 518 readings on 64 addresses (`crimegrade_types_batch1001_readings_2026-09-30.csv`, `crimegrade_types_batch1001_2026-09-30.csv`); every address seen on two pages agrees (96 pairs). Set aside: three 18640 shots of the violent-crime page taken while the map was still a dimmed "Load Interactive Map" preview (the proper 18640 six tabs are in the batch), and a duplicate 19134 Robbery shot at another zoom. Reidsville 27320 fits at zoom 11.985, below the search floor the scripts used until then; `grade_by_view.py` now searches from 11.5. `types_batch23601_manifest_2026-09-30.csv` lists the six 23601 tabs: the view fits, but 556 Bellwood Rd lies 35 px north of the page map, so the ZIP needs a re-shoot with the map panned up; it is not in the table. After these batches 94 ZIPs carry all six tabs, and 70 of the 71 ZIPs with an active file-14 row are complete (23601 is the one left).

## Caveats

- **Plus and minus are inferred.** The legend prints only A+, B, C, D and F. Anchoring each printed letter where the legend prints it, instead of using equal bands, changes four of the 25 Overall results: Garfield Heights and W Sylvania Ave become D, and both Starr Ave addresses become D-. It changes three Robbery results: Ingram Ave SW becomes D-, Garfield Heights D and Martins Ferry B. No letter family changes. Martins Ferry's Overall grade sits on the C-/D+ line.
- **Different scales.** CrimeGrade ranks each geographic level separately, so an address's block-group grade and its ZIP's letter are not on the same scale.
- **Robbery rests on few incidents.** Robbery is rare, about 1.6 a year per 1,000 residents in 44104, so a block group of about 1,450 people records only a few robberies a year and its Robbery grade leans on CrimeGrade's model more than the Overall grade does.
- **Modelled data.** CrimeGrade fills police-reporting gaps with a model and lags official data by 6 to 12 months. A block group averages about 1,450 residents, so a grade describes the surrounding blocks, not the house.
