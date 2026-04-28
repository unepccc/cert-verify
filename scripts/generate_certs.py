"""
UNEP-CCC Certificate Verification System v1.1
CSV → JSON generator

Reads certificates.csv (exported directly from SharePoint) from the
repository root and writes one JSON file per row into certificates/.

SharePoint export columns used:
  CertificateID, First Name, Last Name, Email, WebinarTitle,
  Webinar Date, DateIssued, Status, VerificationURL,
  Verification Notes (internal)

Columns intentionally ignored (never written to JSON):
  Email, VerificationURL, Verification Notes (internal)

Date formatting (done by this script — no Excel pre-processing needed):
  "Webinar Date"  : "11/5/2025"         → "5 November 2025"
  "DateIssued"    : "4/14/2026 2:27 PM" → "14 April 2026, 14:27:00 (UTC+02)"

Rules enforced:
  - Required fields must not be blank
  - Status must be exactly "Valid" or "Revoked"
  - Dates must be parseable — row is skipped with a clear error if not
"""

import csv
import json
import os
import sys
from datetime import datetime

# ── Configuration ────────────────────────────────────────────────────────────

CSV_FILE         = "certificates.csv"
OUTPUT_DIR       = "certificates"
ALLOWED_STATUSES = {"Valid", "Revoked"}
TIMEZONE_LABEL   = "UTC+02"   # Displayed in dateIssued; adjust if needed

# SharePoint column names (exact, case-sensitive)
COL_ID      = "CertificateID"
COL_FIRST   = "First Name"
COL_LAST    = "Last Name"
COL_TITLE   = "WebinarTitle"
COL_DATE    = "Webinar Date"   # e.g. "11/5/2025"  (M/D/YYYY from SharePoint)
COL_ISSUED  = "DateIssued"     # e.g. "4/14/2026 2:27 PM"
COL_STATUS  = "Status"

REQUIRED_COLS = [COL_ID, COL_FIRST, COL_LAST, COL_TITLE,
                 COL_DATE, COL_ISSUED, COL_STATUS]

# ── Date formatting ───────────────────────────────────────────────────────────

WEBINAR_DATE_FORMATS = ["%m/%d/%Y", "%m/%d/%Y %I:%M %p"]
ISSUED_DATE_FORMATS  = ["%m/%d/%Y %I:%M %p", "%m/%d/%Y"]


def format_webinar_date(raw: str) -> str:
    """
    "11/5/2025"  →  "5 November 2025"
    """
    raw = raw.strip()
    for fmt in WEBINAR_DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.strftime("%-d %B %Y")
        except ValueError:
            continue
    raise ValueError(f"Cannot parse webinar date: '{raw}'")


def format_date_issued(raw: str) -> str:
    """
    "4/14/2026 2:27 PM"  →  "14 April 2026, 14:27:00 (UTC+02)"
    SharePoint does not export seconds so we pad with :00.
    """
    raw = raw.strip()
    for fmt in ISSUED_DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            day  = dt.strftime("%-d")
            mon  = dt.strftime("%B")
            year = dt.strftime("%Y")
            time = dt.strftime("%H:%M:%S")
            return f"{day} {mon} {year}, {time} ({TIMEZONE_LABEL})"
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date issued: '{raw}'")

# ── Helpers ───────────────────────────────────────────────────────────────────

def safe_str(value: str) -> str:
    return value.strip()


def validate_row(row: dict) -> list:
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
        "webinarDate":   format_webinar_date(row[COL_DATE]),
        "dateIssued":    format_date_issued(row[COL_ISSUED]),
        "status":        safe_str(row[COL_STATUS]),
    }

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(CSV_FILE):
        print(f"ERROR: '{CSV_FILE}' not found in repository root.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    written    = 0
    skipped    = 0
    has_errors = False

    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        missing_headers = [c for c in REQUIRED_COLS if c not in reader.fieldnames]
        if missing_headers:
            print("ERROR: CSV is missing required columns:")
            for h in missing_headers:
                print(f"  - {h}")
            print(f"\nColumns found: {reader.fieldnames}")
            sys.exit(1)

        for line_num, row in enumerate(reader, start=2):
            cert_id = row.get(COL_ID, "").strip()

            if not any(v.strip() for v in row.values()):
                continue

            errors = validate_row(row)
            if errors:
                print(f"SKIP  row {line_num} (ID: '{cert_id}'):")
                for e in errors:
                    print(e)
                skipped    += 1
                has_errors  = True
                continue

            try:
                payload = row_to_json(row)
            except ValueError as e:
                print(f"SKIP  row {line_num} (ID: '{cert_id}'): {e}")
                skipped    += 1
                has_errors  = True
                continue

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

    print("Done.")


if __name__ == "__main__":
    main()
