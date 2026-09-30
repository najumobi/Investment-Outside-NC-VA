# 2026-09-30: advisory round 20, 306-308 Troy Ave NE Roanoke (files 68/68a/68b)

Memo `68 Advisory assimilation and unknown-unknowns pass, round 20, 306-308 Troy Ave NE Roanoke (2026-09-30).md`, the long-form claims ledger `68a` and the record set `68b` are at the repository root and were written to the Dropbox campaign root from the cloud session.

This folder holds the five campaign files the round patches, byte-exact (BOM and CRLF preserved), as produced by `_pipeline/assimilate_0930troy.py` against the live files downloaded from Dropbox on 2026-09-30 (file 14 as of 2026-09-29 11:02 UTC):

- `14 Live status and ranking of the 42 tracked candidates (2026-09-11).csv`: row i=28 (306 & 308 Troy Ave NE) status, event, score, coc, dscr, novice and note; no other row touched (`_pipeline/_backup_14_before_0930troy.csv` is the file as downloaded).
- `67a Asks register ... (2026-09-29).csv`: seven rows appended for the property (the six 73a asks plus a records request for permit ZVBL21-0310).
- `32b Jurisdiction rules ledger ... (2026-09-15).csv`: the Roanoke row extended in eight columns.
- `_pipeline/constants.json`: `advisory_73_rules_adopted`, `roanoke_instruments`, `roanoke_duplex_market`, `sweep_rent_basis_finding` (pipeline DEFECT 4, not applied), `inter_rater_log`, `rrha_hcv_status_2026`, and additions under `owner_side_municipal_fees.Roanoke`, `tax_assessed_combined_rate.Roanoke`, `gate3_two_family_rule.applied_to`, `rate_of_the_week`.
- `_pipeline/README - pipeline handoff (2026-09-11).md` and `_advisory/README.md`: the round-20 sections appended.

The Dropbox connector cannot write carriage-return line endings, so these five were NOT overwritten in Dropbox from the cloud. `python _pipeline/assimilate_0930troy.py` run on the Windows side (the script is in the Dropbox `_pipeline` folder) backs up and patches the live files in place; it is re-runnable and skips what is already present. `_evidence/306&308 Troy Ave NE Roanoke/records_2026-09-30/` holds the pulled records the script reads (owner and staff names masked in this repository copy; the Dropbox copy keeps the raw layer values).
