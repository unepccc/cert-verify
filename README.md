# UNEP-CCC Certificate Verification

Public verification page for Certificates of Attendance issued by the [UNEP Copenhagen Climate Centre](https://unepccc.org/) — webinars, workshops, training courses and conferences.

🔗 **Verify a certificate:** [unepccc.github.io/cert-verify](https://unepccc.github.io/cert-verify/)
📊 **Statistics:** [unepccc.github.io/cert-verify/stats.html](https://unepccc.github.io/cert-verify/stats.html)

## How verification works

Every certificate has a Certificate ID, printed on the document and encoded in its QR code, for example `UNEPCCC-WEB-2026-K7M3Q9TXA2`.

Each certificate's record is stored in `records/` in locked (encrypted) form. A record can be opened only with its Certificate ID: the verification page uses the ID to find and unlock that one record in your browser. Without the ID, the files reveal nothing — not even which certificate they belong to.

The page shows one of three results:

| Result | Meaning |
|---|---|
| ✅ Valid | The certificate was issued by UNEP-CCC and is current |
| ⚠️ Revoked | The certificate was issued but has since been revoked |
| ❌ Not Found | No certificate exists with this ID |

## Maintenance

`records/` and `stats.json` are published automatically from a private data repository. Do not edit them by hand.

For certificate enquiries: **aristeidis.tsakiris@un.org**
UNEP Copenhagen Climate Centre · Marmorvej 51 · 2100 Copenhagen Ø · Denmark
