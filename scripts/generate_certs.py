"""
UNEP-CCC Certificate Verification System v1.2
CSV → JSON generator (multi-activity)

Reads certificates.csv (exported / pushed from SharePoint) from the
repository root and writes one JSON file per row into certificates/.
Also writes stats.json with aggregate statistics.

Supports multiple activity types (webinars, workshops, training, etc.).

CSV columns used:
  CertificateID, First Name, Last Name, Activity Type, Activity Title,
  Activity Date, DateIssued, Status
Columns intentionally ignored (never written to JSON):
  Email, VerificationURL, Verification Notes (internal)

Activity type:
  - Taken from the "Activity Type" column if present (e.g. "Workshop").
  - If that column is blank/missing, it is derived from the Certificate ID
    middle code (WEB → Webinar, WSP → Workshop, TRN → Training course,
    CNF → Conference). Unknown codes default to "Activity".

Date formatting (done by this script):
  "Activity Date" : "11/5/2025"         → "5 November 2025"
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

# Certificate ID middle code → activity type display name
TYPE_CODE_MAP = {
    "WEB": "Webinar",
    "WSP": "Workshop",
    "TRN": "Training course",
    "CNF": "Conference",
}
DEFAULT_TYPE = "Activity"   # used when code is unknown and no column given

# Column names. The script accepts new names first, then falls back to the
# old (v1.1) names so the transition does not break anything.
COL_ID        = "CertificateID"
COL_FIRST     = "First Name"
COL_LAST      = "Last Name"
COL_TYPE      = "Activity Type"                       # new (optional)
COL_TITLE     = ["Activity Title", "WebinarTitle"]    # new, then old
COL_DATE      = ["Activity Date", "Webinar Date"]     # new, then old
COL_DATE_DISP = "Activity Date Display"               # new (optional) — free text
COL_ISSUED    = "DateIssued"
COL_STATUS    = "Status"

REQUIRED_SIMPLE = [COL_ID, COL_FIRST, COL_LAST, COL_ISSUED, COL_STATUS]

# ── Date formatting ───────────────────────────────────────────────────────────

ACTIVITY_DATE_FORMATS = ["%m/%d/%Y", "%m/%d/%Y %I:%M %p"]
ISSUED_DATE_FORMATS   = ["%m/%d/%Y %I:%M %p", "%m/%d/%Y"]


def format_activity_date(raw: str) -> str:
    """ "11/5/2025"  →  "5 November 2025" """
    raw = raw.strip()
    for fmt in ACTIVITY_DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%-d %B %Y")
        except ValueError:
            continue
    raise ValueError(f"Cannot parse activity date: '{raw}'")


def format_date_issued(raw: str) -> str:
    """ "4/14/2026 2:27 PM"  →  "14 April 2026, 14:27:00 (UTC+02)" """
    raw = raw.strip()
    for fmt in ISSUED_DATE_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
            return (f"{dt.strftime('%-d')} {dt.strftime('%B')} "
                    f"{dt.strftime('%Y')}, {dt.strftime('%H:%M:%S')} "
                    f"({TIMEZONE_LABEL})")
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date issued: '{raw}'")

# ── Helpers ───────────────────────────────────────────────────────────────────

def safe_str(value: str) -> str:
    return (value or "").strip()


def pick_column(row: dict, names) -> str:
    """Return the first non-empty value among the given column name(s)."""
    if isinstance(names, str):
        names = [names]
    for n in names:
        if n in row and row[n] and row[n].strip():
            return row[n].strip()
    return ""


def derive_activity_type(row: dict, cert_id: str) -> str:
    """
    Use the Activity Type column if present, otherwise derive from the
    Certificate ID middle code.
    """
    explicit = safe_str(row.get(COL_TYPE, ""))
    if explicit:
        return explicit
    # Derive from ID: UNEPCCC-<CODE>-YYYY-NNNNNN
    parts = cert_id.split("-")
    if len(parts) >= 2:
        code = parts[1].upper()
        return TYPE_CODE_MAP.get(code, DEFAULT_TYPE)
    return DEFAULT_TYPE


def validate_row(row: dict, title: str, date_raw: str) -> list:
    errors = []
    for col in REQUIRED_SIMPLE:
        if col not in row:
            errors.append(f"  Missing column '{col}'")
        elif not row[col].strip():
            errors.append(f"  Column '{col}' is blank")
    if not title:
        errors.append("  Activity Title is blank (checked 'Activity Title' and 'WebinarTitle')")
    # A date is required: either the single Activity Date OR the free-text display field.
    date_display = safe_str(row.get(COL_DATE_DISP, ""))
    if not date_raw and not date_display:
        errors.append("  Activity Date is blank (provide 'Activity Date' or 'Activity Date Display')")
    if COL_STATUS in row and row[COL_STATUS].strip() not in ALLOWED_STATUSES:
        errors.append(
            f"  Status '{row[COL_STATUS].strip()}' is invalid "
            f"(must be 'Valid' or 'Revoked')"
        )
    return errors


def row_to_json(row: dict, cert_id: str, title: str, date_raw: str) -> dict:
    # Use the free-text display date if provided (e.g. "2nd–4th June 2026"),
    # otherwise format the single Activity Date as normal (e.g. "2 June 2026").
    date_display = safe_str(row.get(COL_DATE_DISP, ""))
    activity_date = date_display if date_display else format_activity_date(date_raw)

    return {
        "certificateId": cert_id,
        "firstName":     safe_str(row[COL_FIRST]),
        "lastName":      safe_str(row[COL_LAST]),
        "activityType":  derive_activity_type(row, cert_id),
        "activityTitle": title,
        "activityDate":  activity_date,
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

    stats_activities = {}   # title → {type, date, total, valid, revoked}
    stats_by_year    = {}   # year → count
    stats_by_type    = {}   # activityType → count
    total_valid      = 0
    total_revoked    = 0

    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        missing = [c for c in REQUIRED_SIMPLE if c not in reader.fieldnames]
        if missing:
            print("ERROR: CSV is missing required columns:")
            for h in missing:
                print(f"  - {h}")
            print(f"\nColumns found: {reader.fieldnames}")
            sys.exit(1)

        for line_num, row in enumerate(reader, start=2):
            cert_id = row.get(COL_ID, "").strip()

            if not any((v or "").strip() for v in row.values()):
                continue

            title    = pick_column(row, COL_TITLE)
            date_raw = pick_column(row, COL_DATE)

            errors = validate_row(row, title, date_raw)
            if errors:
                print(f"SKIP  row {line_num} (ID: '{cert_id}'):")
                for e in errors:
                    print(e)
                skipped += 1
                has_errors = True
                continue

            try:
                payload = row_to_json(row, cert_id, title, date_raw)
            except ValueError as e:
                print(f"SKIP  row {line_num} (ID: '{cert_id}'): {e}")
                skipped += 1
                has_errors = True
                continue

            out_path = os.path.join(OUTPUT_DIR, f"{cert_id}.json")
            with open(out_path, "w", encoding="utf-8") as out:
                json.dump(payload, out, ensure_ascii=False, indent=2)

            print(f"OK    {out_path}  [{payload['activityType']} · {payload['status']}]")
            written += 1

            # ── Accumulate stats ──────────────────────────────────────────
            status   = payload["status"]
            a_title  = payload["activityTitle"]
            a_type   = payload["activityType"]
            a_date   = payload["activityDate"]

            try:
                year = payload["dateIssued"].split(" ")[2].replace(",", "")
            except IndexError:
                year = "Unknown"

            key = f"{a_type}||{a_title}"
            if key not in stats_activities:
                stats_activities[key] = {
                    "title": a_title, "type": a_type, "activityDate": a_date,
                    "total": 0, "valid": 0, "revoked": 0
                }
            stats_activities[key]["total"]   += 1
            stats_activities[key]["valid"]   += 1 if status == "Valid"   else 0
            stats_activities[key]["revoked"] += 1 if status == "Revoked" else 0

            stats_by_year[year] = stats_by_year.get(year, 0) + 1
            stats_by_type[a_type] = stats_by_type.get(a_type, 0) + 1

            if status == "Valid":   total_valid   += 1
            if status == "Revoked": total_revoked += 1

    # ── Write stats.json ──────────────────────────────────────────────────────
    from datetime import timezone
    import datetime as dt

    stats_payload = {
        "generatedAt":       dt.datetime.now(timezone.utc).strftime("%-d %B %Y, %H:%M:%S (UTC)"),
        "totalCertificates": written,
        "totalValid":        total_valid,
        "totalRevoked":      total_revoked,
        "totalActivities":   len(stats_activities),
        "byYear":            dict(sorted(stats_by_year.items())),
        "byType":            dict(sorted(stats_by_type.items())),
        "activities":        [
            {
                "title":        data["title"],
                "type":         data["type"],
                "activityDate": data["activityDate"],
                "total":        data["total"],
                "valid":        data["valid"],
                "revoked":      data["revoked"],
            }
            for data in sorted(
                stats_activities.values(),
                key=lambda x: x["activityDate"],
                reverse=True
            )
        ]
    }

    with open("stats.json", "w", encoding="utf-8") as sf:
        json.dump(stats_payload, sf, ensure_ascii=False, indent=2)
    print("\nOK    stats.json")

    print(f"\n── Summary ──────────────────────────")
    print(f"  Written : {written}")
    print(f"  Skipped : {skipped}")

    if has_errors:
        print("\nWARNING: Some rows were skipped. Review errors above.")

    print("Done.")


if __name__ == "__main__":
    main()
