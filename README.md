# UNEP-CCC Certificate Verification System

**Version 1.1** · Public certificate verification for webinar attendance certificates issued by the [UNEP Copenhagen Climate Centre](https://unepccc.org/).

🔗 **Live system:** [unepccc.github.io/cert-verify](https://unepccc.github.io/cert-verify/)

---

## Overview

This repository hosts a static, publicly accessible certificate verification service. When UNEP-CCC issues a Certificate of Attendance for a webinar, a corresponding JSON record is published here. Anyone can verify the authenticity of a certificate by entering the Certificate ID or scanning the QR code printed on the document.

The system is deliberately static — there is no backend server, no database, and no live connection to UN internal systems. This ensures long-term reliability, auditability, and minimal maintenance.

---

## How It Works

```
Webinar completed
      ↓
Power Automate generates & emails PDF certificates to attendees
      ↓
SharePoint list exported as certificates.csv
      ↓
CSV uploaded to this repository
      ↓
GitHub Action converts CSV → individual JSON files (certificates/)
      ↓
Public verification page reads JSON files on demand
```

---

## Repository Structure

```
cert-verify/
│
├── index.html                  # Public verification page (GitHub Pages)
├── certificates.csv            # Source data exported from SharePoint
│
├── certificates/               # Auto-generated — one JSON file per certificate
│   └── UNEPCCC-WEB-YYYY-NNNNNN.json
│
├── assets/
│   └── unepccc-logo.png        # UNEP-CCC logo (transparent background)
│
├── scripts/
│   └── generate_certs.py       # CSV → JSON conversion script
│
└── .github/
    └── workflows/
        └── generate-certs.yml  # GitHub Action — runs on every CSV upload
```

---

## Certificate ID Format

```
UNEPCCC-WEB-YYYY-NNNNNN
```

| Part | Description |
|------|-------------|
| `UNEPCCC` | Issuing organisation |
| `WEB` | Certificate type (webinar) |
| `YYYY` | Year of issuance |
| `NNNNNN` | Sequential certificate number |

---

## JSON Data Model

Each certificate is stored as a single JSON file named `<CertificateID>.json`:

```json
{
  "certificateId": "UNEPCCC-WEB-2026-092206",
  "firstName": "Aristeidis",
  "lastName": "Tsakiris",
  "webinarTitle": "Maritime Decarbonization: A Critical Component of the Global Climate Action Agenda",
  "webinarDate": "24 April 2025",
  "dateIssued": "17 April 2026, 16:12:00 (UTC+02)",
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

## Supported Languages

The verification page is available in English, French, Spanish, and Chinese (中文).

---

## Updating the Certificate Register

After each webinar:

1. Export the certificate list from SharePoint as `certificates.csv`
2. Remove the `Email` and any internal columns before uploading
3. Upload/replace `certificates.csv` in this repository root
4. The GitHub Action runs automatically and regenerates all JSON files

**The CSV must contain these columns** (exact names, case-sensitive):

| Column | Example |
|--------|---------|
| `CertificateID` | `UNEPCCC-WEB-2026-092206` |
| `First Name` | `Aristeidis` |
| `Last Name` | `Tsakiris` |
| `WebinarTitle` | `Maritime Decarbonization...` |
| `Webinar Date` | `4/24/2025` |
| `DateIssued` | `4/17/2026 4:12 PM` |
| `Status` | `Valid` or `Revoked` |

---

## Revoking a Certificate

1. In SharePoint, change the certificate's `Status` to `Revoked`
2. Export and upload `certificates.csv` as normal
3. The GitHub Action will update the JSON file with `"status": "Revoked"`
4. The verification page will immediately show the Revoked state

> Do **not** delete JSON files to revoke a certificate. Always use the `Revoked` status.

---

## System Design Principles

- **No backend** — fully static, hosted on GitHub Pages
- **No APIs** — no live connection to UN internal systems
- **Auditable** — full change history in Git
- **Resilient** — works indefinitely with no infrastructure to maintain
- **Privacy** — email addresses and internal notes are never published

---

## Versioning

| Version | Description |
|---------|-------------|
| v1.0 | Static verification, no revocation support |
| v1.1 | Revocation-aware (current) |

Minor versions = behavioural changes · Major versions = architectural changes

---

## Contact

For certificate enquiries: **aristeidis.tsakiris@un.org**  
UNEP Copenhagen Climate Centre · Marmorvej 51 · 2100 Copenhagen Ø · Denmark
