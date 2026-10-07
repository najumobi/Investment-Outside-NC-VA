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

## 2026-10-06, second pass: the five rows still at one image after the morning fold

Najum asked (10/6, afternoon) for the same hunt on 1992 Starr Ave Toledo, 1996 Starr Ave Toledo, 315 E Essex Ave Lansdowne, 319 E Essex Ave Lansdowne and 426 Washington Ave Huntington.

| Row | New photos | From | Vintage |
|---|---|---|---|
| 1992 Starr Ave | 4 county photos and 1 Street View frame | the Lucas County Auditor's parcel photos (the document API behind the Photos tab of icare.co.lucas.oh.us); the Street View frame Realtor.com embeds | 1997, 2006, 2011, and a county "Front" photo stamped 2/7/2024; the Street View frame is undated |
| 1996 Starr Ave | 3 county photos and 1 Street View frame | the same two sources | 1997, 2006, 2011; Street View undated |
| 315 E Essex Ave | 0 new listing photographs; 1 Google Street View frame, a DIFFERENT capture from the listing cover (the cover has a sign post at the steps, the frame has none), so the folder now holds two distinct exterior views | Realtor.com's embedded frame; the Delaware County card and sketch | undated |
| 319 E Essex Ave | 0 new photographs; the Street View frame saved is centred on 315's doorway pair and shows 319's doorway only at its right edge, so 319 stays at one unique view (the cover, which matches Google's capture) | the same | undated |
| 426 Washington Ave | 0; the Zillow for-sale-by-owner listing's only image is Google's Street View frame, the capture Najum had already screenshotted, saved here at Google's full 1536 x 1152 | Zillow's raw page | undated |

Also saved: the county footprint sketches for all four MLS rows, the Lucas County photo metadata, and (in the notes) the Delaware County residential cards, which record two living units for each Essex house, a reading the morning pass could not get because the county's https certificate has expired and the site answers over http only.

What the county photos change: 1992 Starr is a ONE-STORY building of 1,280 sq ft behind a two-story-looking false front (the 2011 side view and the county card agree), so "4 bedrooms, 2 baths" means tiny units or a basement unit; 1996 Starr was the Pastime Bar in 1997 and 2006 and "apartments and office" by 2011, so its commercial class is its history, not an error.

Plumbing for this pass: the three direct Bright Data connectors all answered "session expired", so every Bright Data call went through Composio with the accounts rotated across all four; Bright Data refuses county sites as "Government" and Zillow's search URLs under its robots policy (Zillow's homedetails pages and zillowstatic's address suggestions are allowed); the county sites were read from the cloud container; SerpApi did the search-engine work because the workbench's own web_search helper is disabled by Composio's "enhanced controls"; Homes.com and a Facebook group post failed on both the Bright Data and Apify legs; the Wayback CDX index (through Bright Data) had no capture of any of the five Zillow pages or of the Redfin page tried; Dropbox fetched the Street View frames from Google's signed links and took the county images as uploads from the Composio sandbox.

The same subfolders and notes were written into the Dropbox `_evidence` tree on 2026-10-06; nothing older was touched.

Correction (10/6, evening, after Najum asked which rows still sit at one unique view): the two Essex rows above were first written as "the same Google capture as the cover". Laid side by side at matching scale, 315's two covers carry a red-and-white sign on a post at the front steps and the Street View frame does not, so Google's frame is a second capture of 315 and that folder has two distinct exterior views (both of the front; no interiors). 319's frame is Google's view of the same block centred on 315's pair of doors; 319's own doorway, with the chairs, grill and dish of its cover, sits at the frame's right edge, so 319 keeps one unique view. The two hunt notes were rewritten the same evening, in the repo and in Dropbox. On 10/7, at Najum's request, 319's Street View folder and the smaller copy of its cover were deleted from Dropbox, and the folder was removed from this mirror; 319's one image is now `319_essex_redfin_cover_2026-10-06/essex319_cover_larger_from_broker_feed.jpg`.

The weekly fold could adopt the Lucas County route as a script: a Tyler iasWorld public-access site exposes its parcel photos through `api/documents/Parcel%20Photo/<jurisdiction>/<base64 of the assessor number>?token=<the token printed in idoc2/photoview.aspx>` once an address search has opened the parcel's datalet; each document's image is `api/document/<id>/standard?token=...`. Delaware County's iasWorld site keeps no photo documents, only the sketch (a session-bound Telerik image on the Sketch tab).

## 2026-10-06, third pass: 613 S 52nd St Philadelphia

Najum asked (10/6, evening) for the same hunt on 613 S 52nd St, the one Philadelphia row still at a single image (the Zillow cover at 1024 x 681).

| Source | New images | Vintage |
|---|---|---|
| Realtor.com's copy of the Bright MLS listing PAPH2603378 | 34, the whole gallery, at 2048 x 1362 | May 2026 |
| Redfin's photo CDN, listing PAPH2224964 | 23 distinct (26 files; 3 byte-identical repeats dropped) | April 2023 |
| Redfin's photo CDN, listing 1000750585 | 1 (320 x 240) | September 2006 |
| Zillow's "Floor 2" rental record | 5 | about January 2026 |
| OfferMarket's wholesale posting | 2 photos and a parcel map | 2023 |
| Google Street View, the frame Zillow and Realtor embed | one capture at 1536 x 1152 and 950 x 428 | undated, after the 2025 repaint |

What the photos change: the folder had the cover alone; now every room of both units, the rear, the yard and the side lot are on file, and the 2023 set shows the same kitchens and baths before the 2025 purchase, so the 2026 listing's refresh is paint, first-floor laminate and fixtures (an inference from the comparison, labeled so in the note). Drop ceilings hide the first-floor ceilings and the second-floor front rooms' ceilings, which the note flags for inspection.

What the pages change: the listing reads off the market on 10/6 (Realtor.com status off_market with its Bright MLS raw block last updated 8/14, EveryHome "No Longer Available", Zillow's main record back to the 2025 sale with one photo, Redfin "Off Market" and never carrying the listing). No site exposes the date. Under the standing rule the row is OUT until the agent confirms; this pass does not edit the tracker.

Plumbing for this pass: the direct Bright Data connectors were still expired, so every page read went through Composio's BRIGHTDATA_WEB_UNLOCKER (raw format, rotated across the four accounts), which answered for Zillow (the main record and both unit records), Realtor.com, Redfin, EveryHome, OfferMarket, LoopNet (a login wall), lifeinthephillyburbs (a redirect), the eXp IDX page (404) and three Wayback CDX queries (all empty); Homes.com and Facebook refused the Bright Data and the Apify legs as before. The photo bytes came straight from the public CDNs (ap.rdcpix.com, ssl.cdn-redfin.com, photos.zillowstatic.com, cms.offermarket.us, maps.googleapis.com) to the cloud container, where contact sheets confirmed every frame is this house; the container's egress resets on web.archive.org, hence the unlocker for the CDX. The six subfolders were created with the Dropbox connector, the 68 images saved into them with Composio's DROPBOX_SAVE_URL from the same public URLs, and the note and the two JSON files written with the connector; nothing older was touched.

Method notes for the weekly fold: Realtor.com's raw page lists every listing photo with its rdcpix id, and the `od-w2048_h1536.jpg` suffix serves a 2048 px rendering, larger than Zillow's 1536 px; Redfin's CDN still serves a removed listing's gallery by MLS number years later (PAPH2224964 from 2023, 1000750585 from 2006). The eXp IDX CDN pattern (`listingphotos<office>/<MLS>-<n>.jpg`) is a trap: it answers 200 with a "Photo Coming Soon" placeholder for every index, so a 200 there proves nothing.
