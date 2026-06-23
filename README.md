# UNEP-CCC Certificate Verification System

**Version 1.1** · Public certificate verification for webinar attendance certificates issued by the [UNEP Copenhagen Climate Centre](https://unepccc.org/).

🔗 **Live system:** [unepccc.github.io/cert-verify](https://unepccc.github.io/cert-verify/)
📊 **Statistics:** [unepccc.github.io/cert-verify/stats.html](https://unepccc.github.io/cert-verify/stats.html)

---

## Overview

This repository hosts a static, publicly accessible certificate verification service. When UNEP-CCC issues a Certificate of Attendance for a webinar, a corresponding JSON record is published here automatically. Anyone can verify the authenticity of a certificate by entering the Certificate ID or scanning the QR code printed on the document.

The system is deliberately static — there is no backend server, no database, and no live connection to UN internal systems. This ensures long-term reliability, auditability, and minimal maintenance.

---

## How It Works

```
Attendee registered in SharePoint
      ↓
Power Automate triggers automatically
      ↓
Certificate ID generated · QR code created · Word template populated
      ↓
PDF generated and emailed to attendee
      ↓
Power Automate pushes updated certificates.csv to GitHub
      ↓
GitHub Action runs automatically (~30 seconds)
      ↓
JSON file published · stats.json updated
      ↓
Certificate live on public verification page
```

The entire process from SharePoint entry to live certificate verification is fully automatic — no manual steps required.

---

## Repository Structure

```
cert-verify/
│
├── index.html                  # Public verification page (GitHub Pages)
├── stats.html                  # Public statistics page
├── certificates.csv            # Source data — updated automatically by Power Automate
├── stats.json                  # Auto-generated statistics — updated by GitHub Action
│
├── certificates/               # Auto-generated — one JSON file per certificate
│   └── UNEPCCC-<TYPE>-YYYY-NNNNNN.json
│
├── assets/
│   └── unepccc-logo.png        # UNEP-CCC logo (transparent background)
│
├── scripts/
│   └── generate_certs.py       # CSV → JSON + stats conversion script
│
└── .github/
    └── workflows/
        └── generate-certs.yml  # GitHub Action — runs on every CSV update
```

---

## Certificate ID Format

```
UNEPCCC-<TYPE>-YYYY-NNNNNN
```

| Part | Description |
|------|-------------|
| `UNEPCCC` | Issuing organisation |
| `<TYPE>` | Activity type code (see below) |
| `YYYY` | Year of issuance |
| `NNNNNN` | Six-digit random number |

**Activity type codes:**

| Code | Activity Type |
|------|---------------|
| `WEB` | Webinar |
| `WSP` | Workshop |
| `TRN` | Training course |
| `CNF` | Conference |

The activity type is taken from the `Activity Type` column in the data. If that column is blank, it is derived automatically from the type code in the Certificate ID.

---

## JSON Data Model

Each certificate is stored as a single JSON file named `<CertificateID>.json`:

```json
{
  "certificateId": "UNEPCCC-WSP-2026-445566",
  "firstName": "Maria",
  "lastName": "Santos",
  "activityType": "Workshop",
  "activityTitle": "Designing NDCs: A Practical Workshop for Policymakers",
  "activityDate": "10 June 2026",
  "dateIssued": "12 June 2026, 10:30:00 (UTC+02)",
  "status": "Valid"
}
```

**Status values:**

| Status | Meaning |
|--------|---------|
| `Valid` | Certificate is authentic and current |
| `Revoked` | Certificate has been revoked by UNEP-CCC |

> Revoked certificates retain their JSON file — they are never deleted. The `status` field is updated to `"Revoked"` and the file is republished.

---

## Verification States

The public page shows exactly one of three states:

| State | Condition |
|-------|-----------|
| ✅ **Valid** | JSON file exists and `status` is `"Valid"` |
| ⚠️ **Revoked** | JSON file exists and `status` is `"Revoked"` |
| ❌ **Not Found** | No JSON file exists for this Certificate ID |

---

## Verification Page Features

- **Four languages** — English, French, Spanish, Chinese (中文)
- **Auto-verify on load** — direct links via `?cert=UNEPCCC-WEB-YYYY-NNNNNN` verify instantly
- **Verified-on timestamp** — shows exact date and time of verification with animated indicator
- **Print / Save Certificate** — generates a print-ready certificate with QR code and verification timestamp, matching the original PDF layout
- **Share button** — native OS share sheet on mobile, clipboard copy on desktop

---

## Statistics Page

A public statistics page is available at [/stats.html](https://unepccc.github.io/cert-verify/stats.html) showing:

- Total certificates issued, valid, and revoked
- Total number of activities
- Certificates by activity type (bar chart)
- Certificates issued by year (bar chart)
- Breakdown per activity with status badges

Statistics are regenerated automatically by the GitHub Action on every CSV update — no manual maintenance required.

---

## Automated Pipeline

Certificates are published automatically via Power Automate:

1. A new item is created in the SharePoint certificates list
2. Power Automate generates the Certificate ID, QR code, and PDF
3. The PDF is emailed to the attendee with a direct verification link
4. Power Automate appends the new row to `certificates.csv` via the GitHub API
5. The GitHub Action detects the change and generates the JSON file and updated statistics

**No manual CSV export or file upload is required.**

---

## Manual Update (Fallback)

If the automated pipeline is unavailable, certificates can be published manually:

1. Export the certificate list from SharePoint as `certificates.csv`
2. Remove the `Email` and any internal columns before uploading
3. Upload/replace `certificates.csv` in this repository root
4. The GitHub Action runs automatically and regenerates all files

**The CSV must contain these columns** (exact names, case-sensitive):

| Column | Example |
|--------|---------|
| `CertificateID` | `UNEPCCC-WSP-2026-445566` |
| `First Name` | `Maria` |
| `Last Name` | `Santos` |
| `Activity Type` *(optional)* | `Workshop` |
| `Activity Title` | `Designing NDCs: A Practical Workshop...` |
| `Activity Date` | `6/10/2026` |
| `DateIssued` | `6/12/2026 10:30 AM` |
| `Status` | `Valid` or `Revoked` |

> For backward compatibility, the legacy column names `WebinarTitle` and `Webinar Date` are still accepted, and a missing `Activity Type` is derived from the Certificate ID type code.

---

## Revoking a Certificate

1. In SharePoint, change the certificate's `Status` to `Revoked`
2. The automated pipeline will update the JSON file automatically, or
3. Export and upload `certificates.csv` manually as a fallback
4. The verification page will immediately show the Revoked state

> Do **not** delete JSON files to revoke a certificate. Always use the `Revoked` status.

---

## System Design Principles

- **No backend** — fully static, hosted on GitHub Pages
- **No APIs** — no live connection to UN internal systems
- **Automated** — Power Automate pushes directly to GitHub on every certificate issuance
- **Auditable** — full change history in Git
- **Resilient** — works indefinitely with no infrastructure to maintain
- **Privacy** — email addresses and internal notes are never published

---

## Versioning

| Version | Description |
|---------|-------------|
| v1.0 | Static verification, no revocation support |
| v1.1 | Revocation-aware, automated pipeline, print/share, statistics |
| v1.2 | Multi-activity support (webinars, workshops, training, conferences) (current) |

Minor versions = behavioural changes · Major versions = architectural changes

---

## Contact

For certificate enquiries: **aristeidis.tsakiris@un.org**  
UNEP Copenhagen Climate Centre · Marmorvej 51 · 2100 Copenhagen Ø · Denmark
