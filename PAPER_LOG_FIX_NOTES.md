# Paper-trading log fixes

## What was wrong / clarified

- The supplied `bot_paper_log.csv` contained only the CSV header (253 bytes): it had no trade rows. There are no historical bot trades in that file to reconstruct, so no records have been invented.
- The Python bot's canonical log is `docs/paper_log.csv`; the mobile app downloads that endpoint and saves it locally as `bot_paper_log.csv`.
- A header-only CSV is a valid result when the Python paper ledger has not opened any positions yet. The app's previous message incorrectly implied that a trade had to close before the log could appear.

## Changes made

- Reworked `paper.py` persistence so CSV and JSON writes use temporary files and atomic replacement.
- CSV export now always includes both OPEN and CLOSED positions, sorted by trade ID, and preserves the complete schema.
- Fixed trade ID allocation so the first new trade is ID 1 and IDs remain unique after restart/migration.
- Added validation for finite entry/SL/TP values and correct BUY/SELL price ordering; invalid paper trades are rejected rather than logged as impossible trades.
- Preserved conservative same-candle handling: if a completed candle touches both SL and TP, SL is recorded first.
- Kept MFE/MAE values across updates and included them in the ledger.
- Updated the mobile app's log-not-found message to explain that a successful scan publishes the CSV even when it currently has no trades.
- Standardized the downloaded/shared bot log filename to `bot_paper_log.csv`.
- Added regression tests for header-only logs, open/closed trade export, and invalid trade rejection.

## Validation

Run from the project root:

```bash
python -m unittest discover -s tests -v
python -m py_compile *.py
```

The included tests pass. Flutter tooling was not available in this environment, so an Android APK build was not run.

## Important limitation

The empty historical bot log cannot be backfilled from the current source code. The corrected logger will record positions generated after deploying this version. It does not fabricate past entries, exits, TP/SL hits, or P&L.
