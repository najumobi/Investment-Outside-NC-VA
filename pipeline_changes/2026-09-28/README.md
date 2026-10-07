# Pipeline changes applied 2026-09-28 (weekly-sweep defect fixes)

Files here mirror what was written to the campaign folder on Dropbox (`…\2026-2027 Duplex Search Campaign\`) from the cloud session on 2026-09-28, byte for byte, so the repo carries a record of the change. The authoritative copies are the Dropbox ones; the local Claude Code session works from those.

- `_pipeline/parsers.py` — `key()` folds portal spelling variants (Mount/Mt, North/N, Parkway/Pkwy, …) before matching.
- `_pipeline/weekly_sweep.py` — `underwrite` re-scores same-date UNREVIEWED rows on a rerun, writes the `i` column despite the BOM header, numbers new rows w<n+1>, and counts `folded_into_14` across passes.
- `_pipeline/fix_defects_0928.py` — one-shot data repair (seen-index re-key and merge, duplicate file-14 row, tally); re-runnable, `--dry` previews.
- `_pipeline/_backup_*_before_0928.*` — the pre-change copies of the two scripts and three data files (the repo's split-zip snapshot of 2026-09-27 holds the same bytes).
- `14 Live status …csv`, `_pipeline/seen_index.csv`, `_sweeps/weekly_tally.csv` — the repaired data files as uploaded.
- `README_section_appended_to_pipeline_handoff.md` — the section appended to `_pipeline\README - pipeline handoff (2026-09-11).md`.

Details of what was wrong and how it was verified are in that README section.
