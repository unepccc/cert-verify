# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

A fully static certificate verification service for UNEP Copenhagen Climate Centre (UNEP-CCC) webinar attendance certificates. It runs on GitHub Pages with no backend, no database, and no live connection to UN systems. The entire pipeline is:

```
SharePoint → Power Automate → certificates.csv (GitHub) → GitHub Action → JSON files + stats.json → GitHub Pages
```

## Running the Certificate Generator

The only script in this repo converts `certificates.csv` into per-certificate JSON files and `stats.json`:

```bash
python scripts/generate_certs.py
```

Run this from the repository root. It requires no dependencies beyond the Python standard library (Python 3.12+). Output goes to `certificates/<CertificateID>.json` and `stats.json`.

To test with a modified CSV without touching the real one:

```bash
cp certificates.csv certificates_test.csv
# edit certificates_test.csv
CSV_FILE=certificates_test.csv python -c "
import scripts.generate_certs as g; g.CSV_FILE='certificates_test.csv'; g.main()
"
```

Or simply edit the `CSV_FILE` constant at the top of `scripts/generate_certs.py` temporarily.

## Architecture

### Data flow

1. **`certificates.csv`** — the authoritative source. Power Automate appends rows automatically. Columns: `CertificateID`, `First Name`, `Last Name`, `WebinarTitle`, `Webinar Date`, `DateIssued`, `Status`, `VerificationURL`, `Verification Notes (internal)`.
2. **`scripts/generate_certs.py`** — reads the CSV, validates each row, formats dates, and writes `certificates/<ID>.json` + `stats.json`. Columns `Email`, `VerificationURL`, and `Verification Notes (internal)` are explicitly dropped and never written to JSON.
3. **`certificates/<ID>.json`** — one file per certificate, fetched directly by `index.html` via `fetch()` against the GitHub Pages URL.
4. **`stats.json`** — aggregated statistics consumed by `stats.html`.
5. **`index.html` / `stats.html`** — self-contained single-file pages. All CSS and JS are inline. No build step, no bundler, no npm.

### Verification logic (index.html)

The page performs a `fetch()` to `certificates/<ID>.json`. Three outcomes:
- **HTTP 200, `status: "Valid"`** → Valid state
- **HTTP 200, `status: "Revoked"`** → Revoked state
- **HTTP 404** → Not Found state

Certificate ID format: `UNEPCCC-WEB-YYYY-NNNNNN`

### Date formatting (generate_certs.py)

SharePoint exports dates in US format. The script converts them:
- `Webinar Date`: `"11/5/2025"` → `"5 November 2025"` (%-d format, no leading zero)
- `DateIssued`: `"4/14/2026 2:27 PM"` → `"14 April 2026, 14:27:00 (UTC+02)"` (seconds padded to `:00` since SharePoint omits them)

`TIMEZONE_LABEL` at the top of the script controls the timezone string displayed in `dateIssued`. It is a display label only — no timezone conversion is performed.

## GitHub Action

`.github/workflows/generate-certs.yml` regenerates the JSON on `main` from three triggers:

- **push** to `main` touching `certificates.csv` — the fast path; regenerates immediately.
- **schedule** (hourly, at `:23`) — a safety net that regenerates even when the push trigger was skipped or missed. It only commits when a certificate file actually changed, so idle runs are no-ops.
- **workflow_dispatch** — manual trigger from the GitHub Actions UI.

It runs `generate_certs.py`, then commits `certificates/` and `stats.json` back to `main` as `cert-bot`. The bot's commit message includes `[skip ci]` to prevent a re-trigger loop.

> **Do not put `[skip ci]` (or `[ci skip]` / `[no ci]`) in any commit that edits `certificates.csv`.** GitHub honors that token on the pushed commit and skips the push trigger, so the JSON is not generated on push. The hourly schedule will still catch it within the hour, but the instant path is lost.

## Key Conventions

- **Never delete JSON files to revoke a certificate.** Set `Status` to `Revoked` in the CSV — the JSON file is updated in place and the page shows the Revoked state.
- **Column names in `certificates.csv` are case-sensitive.** The script uses exact string matching against SharePoint's export headers.
- The `certificates/` directory and `stats.json` are **generated files** — do not edit them manually. Regenerate by running the script or triggering the Action.
- **Never put `[skip ci]` in a commit that edits `certificates.csv`.** It suppresses the push trigger that generates the JSON (the hourly schedule is only a fallback). `[skip ci]` is reserved for the bot's own regenerate commit.
- `index.html` and `stats.html` are **self-contained** (inline CSS + JS). Keep them that way — there is intentionally no build pipeline.
- The four UI languages in `index.html` (EN, FR, ES, 中文) are stored as a `translations` object in the inline JS. All UI strings must be added to all four language keys.
