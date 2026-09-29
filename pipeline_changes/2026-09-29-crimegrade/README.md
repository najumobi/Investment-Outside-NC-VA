# 2026-09-29: CrimeGrade Overall Crime grade at a street address

The campaign has so far used CrimeGrade's ZIP-level letter (file 09 and the `crime` column of file 14). This folder adds a way to read the Overall Crime grade at the address itself, from CrimeGrade's own map, and records the first 25 Ohio addresses read with it. File 14 is untouched.

## Files

- `_pipeline/crimegrade/grade_addresses.py` — entry point: a CSV of addresses and map images in, a CSV of grades out.
- `_pipeline/crimegrade/georef.py` — lines a map image up with the ground by matching its white streets to Census TIGER street centrelines.
- `_pipeline/crimegrade/colour_read.py` — reads the fill colour of the address's census block group and turns it into a grade.
- `_pipeline/crimegrade/ramp.json` — the legend's colour ramp, sampled pixel by pixel from a ZIP-page screenshot.
- `_pipeline/crimegrade/requirements.txt` — numpy and Pillow.
- `addresses_ohio_2026-09-29.csv` — the 25 Ohio addresses graded on 2026-09-29 and the map image each was read from.
- `crimegrade_overall_ohio_2026-09-29.csv` — their results, as written by the committed scripts.
- `.gitignore` — keeps the map images (`maps/`) and the scripts' cache out of the repository.

The map images are not committed and the scripts never download from CrimeGrade. The images are CrimeGrade's, and its terms prohibit automated scraping without a license, so each map is saved by hand.

## How to run

1. Python 3 with numpy and Pillow (`pip install -r _pipeline/crimegrade/requirements.txt`), and internet access to `geocoding.geo.census.gov` and `tigerweb.geo.census.gov`; `--check-side` also uses `nominatim.openstreetmap.org`.
2. For each ZIP, open `https://crimegrade.org/safest-places-in-<ZIP>/`, right-click the map and save the image into `maps/`, for example `maps/44104.png`. A screenshot of that map, or of the interactive map, also works as long as it shows the streets around the address; the legend, the buttons and the "Click the map to explore" band are ignored automatically.
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

## Caveats

- **Plus and minus are inferred.** The legend prints only A+, B, C, D and F. Anchoring each printed letter where the legend prints it, instead of using equal bands, changes four of the 25 Ohio results, each within the D family: Garfield Heights and W Sylvania Ave become D, and both Starr Ave addresses become D-. Martins Ferry sits on the C-/D+ line.
- **Different scales.** CrimeGrade ranks each geographic level separately, so an address's block-group grade and its ZIP's letter are not on the same scale.
- **Modelled data.** CrimeGrade fills police-reporting gaps with a model and lags official data by 6 to 12 months. A block group averages about 1,450 residents, so a grade describes the surrounding blocks, not the house.
