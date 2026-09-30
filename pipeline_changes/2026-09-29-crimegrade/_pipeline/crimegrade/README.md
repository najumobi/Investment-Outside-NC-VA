# crimegrade: block-level crime from CrimeGrade screenshots

Reads CrimeGrade's ZIP-page maps at the census block group and feeds the weekly sweep (memo 69). Nothing here fetches from CrimeGrade; the screenshots are taken by hand (six tabs per ZIP page: Robbery, Assault, Burglary, Vandalism, Drug-Related Crime, Murder; map north-up at the page zoom, dropdown closed, whole page in frame).

Reading a batch of screenshots (a folder with the images in `x/`):
1. `label_screenshots.py cluster <folder>` groups them by crime tab, ZIP and map view and writes two montages; label the clusters in a small JSON and run `label_screenshots.py apply <folder> labels.json` to get `manifest.json`.
2. `grade_by_view.py <folder>` fits each map view once (`georef.py`, TIGER street matching) and reads every tab for every address of file 14 on the map (`FILE14=<path>` points at the live copy); `overlay_view.py <folder> <view>` draws block-group outlines on a view to check a weak fit by eye.
3. `build_crime_bg.py <table.json> <folder> [...]` reads every block group under every fitted view into the table; the compact `model/crime_bg.json` the sweep reads is `{GEOID: {R, A, B, V, D, M, ...positions}}`.
4. `package_batch.py <folder> <tag> <date>` writes the manifest, readings and address-by-crime matrix for the record.

`grade_addresses.py` is the single-address reader the work started with (`addresses.csv` with `id,address,image` in, grades out). `colour_read.py` and `ramp.json` turn a block group's fill colour into a legend position (0 = A+, 1 = F).
