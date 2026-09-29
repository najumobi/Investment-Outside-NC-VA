# 2026-09-29: memo 65 fixes

The code, prompt and repair-script changes live in `../2026-09-28-regions/_pipeline/` (edited in place: `weekly_sweep.py`, `sweep_remote.py`, `parsers.py`, the five `weekly_task_prompt_*.md`, new `fix_defects_0929.py`) and the note appended to the pipeline README is at the end of `../2026-09-28-regions/README_section_appended.md`.

This folder holds the data repair: `_pipeline/_backup_seen_index_before_0929.csv` is the live seen index as downloaded on 2026-09-29 01:46 UTC, `_pipeline/seen_index.csv` is the same index re-keyed by `fix_defects_0929.py` with the 2026-09-29 `parsers.key()` (3,674 -> 3,578 rows, 96 cross-portal twin pairs merged, detail_pending 790 -> 765). Both were written to the Dropbox `_pipeline` folder the same night.

Full appraisal and defect list: `65 Inaugural sweep appraisal, four regional routines (2026-09-28).md` at the repository root.
