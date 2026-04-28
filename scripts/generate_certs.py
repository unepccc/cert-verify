"""
UNEP-CCC Certificate Verification System v1.1
CSV → JSON generator

Reads certificates.csv from the repository root and writes one JSON file
per row into the certificates/ folder.

Rules enforced:
  - Required fields must not be blank
  - Status must be exactly "Valid" or "Revoked"
  - Email column is never written to JSON
  - All string values are JSON-safe (quotes escaped)
  - dateIssued format is normalised to match the spec:
      "14 April 2026, 14:27:40 (UTC+02)"
"""

import csv
import json
import os
import re
import sys

# ── Configuration ────────────────────────────────────────────────────────────

CSV_FILE        = "certificates.csv"
OUTPUT_DIR      = "certificates"
ALLOWED_STATUSES = {"Valid", "Revoked"}

# CSV column names — these match the actual Excel sheet headers exactly.
# The sheet uses "First Name" and "Last Name" (with spaces).
# The formatted date columns are used, NOT the raw serial number columns.
COL_ID          = "CertificateID"
COL_FIRST       = "First Name"
COL_LAST        = "Last Name"
COL_TITLE       = "WebinarTitle"
COL_DATE        = "WebinarDateFormatted"   # e.g. "5 November 2025"
COL_ISSUED      = "DateIssuedFormatted"    # e.g. "14 April 2026, 14:27:40 (UTC+02)"
COL_STATUS      = "Status"
# Email, WebinarDate (raw serial), DateIssued (raw serial), JSON_FileName
# are all intentionally ignored — never written to JSON.

REQUIRED_COLS   = [COL_ID, COL_FIRST, COL_LAST, COL_TITLE,
                   COL_DATE, COL_ISSUED, COL_STATUS]

# ── Helpers ──────────────────────────────────────────────────────────────────

def normalise_date_issued(raw: str) -> str:
    """
    Normalise DateIssued to:  "14 April 2026, 14:27:40 (UTC+02)"
    Handles missing spaces that the current Excel formula sometimes produces.
    """
    # Strip surrounding whitespace
    s = raw.strip()
    # Ensure space after comma between date and time
    s = re.sub(r',\s*', ', ', s)
    # Ensure space before opening parenthesis
    s = re.sub(r'\s*\(', ' (', s)
    return s


def safe_str(value: str) -> str:
    """Return a JSON-safe string (strip leading/trailing whitespace)."""
    return value.strip()


def validate_row(row: dict, line_num: int) -> list[str]:
    """Return a list of error strings for this row (empty = OK)."""
    errors = []
    for col in REQUIRED_COLS:
        if col not in row:
            errors.append(f"  Missing column '{col}'")
        elif not row[col].strip():
            errors.append(f"  Column '{col}' is blank")
    if COL_STATUS in row and row[COL_STATUS].strip() not in ALLOWED_STATUSES:
        errors.append(
            f"  Status '{row[COL_STATUS].strip()}' is invalid "
            f"(must be 'Valid' or 'Revoked')"
        )
    return errors


def row_to_json(row: dict) -> dict:
    return {
        "certificateId": safe_str(row[COL_ID]),
        "firstName":     safe_str(row[COL_FIRST]),
        "lastName":      safe_str(row[COL_LAST]),
        "webinarTitle":  safe_str(row[COL_TITLE]),
        "webinarDate":   safe_str(row[COL_DATE]),
        "dateIssued":    normalise_date_issued(row[COL_ISSUED]),
        "status":        safe_str(row[COL_STATUS]),
    }

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(CSV_FILE):
        print(f"ERROR: '{CSV_FILE}' not found in repository root.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    written  = 0
    skipped  = 0
    has_errors = False

    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Check that all required columns are present in the header
        missing_headers = [c for c in REQUIRED_COLS if c not in reader.fieldnames]
        if missing_headers:
            print("ERROR: CSV is missing required columns:")
            for h in missing_headers:
                print(f"  - {h}")
            print(f"\nColumns found: {reader.fieldnames}")
            print("\nExpected column names (check capitalisation and spaces):")
            for c in REQUIRED_COLS:
                print(f"  {c}")
            sys.exit(1)

        for line_num, row in enumerate(reader, start=2):  # start=2: row 1 is header
            cert_id = row.get(COL_ID, "").strip()

            # Skip completely empty rows silently
            if not any(v.strip() for v in row.values()):
                continue

            errors = validate_row(row, line_num)
            if errors:
                print(f"SKIP  row {line_num} (ID: '{cert_id}'):")
                for e in errors:
                    print(e)
                skipped += 1
                has_errors = True
                continue

            payload  = row_to_json(row)
            out_path = os.path.join(OUTPUT_DIR, f"{cert_id}.json")

            with open(out_path, "w", encoding="utf-8") as out:
                json.dump(payload, out, ensure_ascii=False, indent=2)

            print(f"OK    {out_path}  [{payload['status']}]")
            written += 1

    print(f"\n── Summary ──────────────────────────")
    print(f"  Written : {written}")
    print(f"  Skipped : {skipped}")

    if has_errors:
        print("\nWARNING: Some rows were skipped. Review errors above.")
        # Exit 0 — partial success is still a success.
        # Change to sys.exit(1) if you want the Action to fail on any skip.

    print("Done.")

if __name__ == "__main__":
    main()
