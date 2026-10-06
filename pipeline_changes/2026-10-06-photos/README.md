# 2026-10-06: photo hunt for the eight single-photo rows

Najum asked (2026-10-06) for a hunt for more usable photos than the one each of these eight rows holds in `_evidence`: 1104 Lake St Elmira, 1300 Latrobe St Parkersburg, 18518 Newell Rd Shaker Heights, 310 Linden St Vandergrift, 704 Baker St Cumberland, 806 Lynn St Parkersburg, 822 Lamont St McKees Rocks, 422 E Division St New Castle. His own 10/5 attempts had already probed the current listings' galleries.

## What was found

| Row | New photos | From | Vintage |
|---|---|---|---|
| 18518 Newell Rd | 83 | YES-MLS 4147344 (2019 sale), MLS Now 4438854 and 4485267 (2023), MLS Now 5076409 (2024 sale), Wayback copy of the 2023 Zillow page | 2019, 2023, 2024 |
| 310 Linden St | 24 | West Penn 1668844 (2024 sale) and the two photo sets on Zillow's record for 310 1/2 Linden St | 2024 and about 2018-2021 |
| 422 E Division St | 13 | West Penn 1005628 (2014 listing) and 1207400 (2016 listing) | 2014, 2016 |
| 1104 Lake St | 1 | UNYREIS EC258522 (2020 sale), one exterior | 2020 |
| 704 Baker St, 806 Lynn St, 1300 Latrobe St, 822 Lamont St | 0 | no earlier listing exists on any portal's history, and the county portals that might hold a photo refuse scripted access | |

Every folder here is named exactly as its Dropbox `_evidence` folder. The same eleven subfolders and eight notes were written into the Dropbox `_evidence` tree on 2026-10-06 (the photos by Dropbox's save-from-URL from the CDNs, the notes as `README_hunt_2026-10-06.txt` beside each existing README.txt); nothing from 10/5 was touched. The photos are the originals as served by the CDNs (file names keep the MLS number and frame index); byte-identical duplicates were dropped.

## How (and where the method generalises)

1. Portal sale histories name the earlier MLS numbers (Redfin's "Sale & Tax History" is the most complete; Coldwell Banker, Homes.com and Movoto cross-check).
2. Redfin's photo CDN keeps earlier listings' galleries under those numbers: `https://ssl.cdn-redfin.com/photo/<server>/bigphoto/<last three digits>/<MLS>_<n>[_<v>].jpg`, server 162 for West Penn, 159 for MLS Now and YES-MLS, 190 for UNYREIS, 235 for Bright. Frame indexes were probed 0 to 40 with versions blank and _0 to _9; the CDN is reachable from the cloud container directly.
3. Zillow's raw page JSON carries extra sets the markdown view hides (`lastSoldListing.photos`, the record's own `photos`), fetched through the Bright Data web unlocker (Composio transport) and downloaded from photos.zillowstatic.com.
4. The Wayback Machine's CDX index (through Bright Data; the container cannot reach archive.org) found one useful capture, the 2023 Zillow page of 18518 Newell.
5. County portals: Wood County's parcel layer answered (no photos); Allegheny, Westmoreland and Wood's CAMA sites reject scripted postbacks; Lawrence County's ActDataScout and Chemung County's Beacon are robots-closed to the proxies. The notes give the manual path for each.

The weekly fold could adopt step 1 and 2 as a script: for each new single-photo row, read the Redfin history, probe the CDN for each earlier MLS number, and write the frames and a note into the row's folder.
