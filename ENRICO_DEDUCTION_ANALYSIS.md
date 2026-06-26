# Enrico Deduction Analysis

## Purpose

Analyze documents from Enrico Weissflog / Sachsenpower and create monthly deduction tables for financial review.

## Period Analyzed

February 2024 through June 2025.

## Total Deductions by Category

- Abschlag Coincident: 
- Abschlag Mitnahme: 
- Abschlag Quittungslose Sendung: 
- Sendungsverlust: 
- Scannermiete: 
- Scanner-related invoices: 
- Other deductions: 

## Monthly Summary Table

| month | gross_credit_gutschrift_total | abschlag_coincident_total | abschlag_mitnahme_total | abschlag_quittungslose_sendung_total | sendungsverlust_total | scannermiete_total | other_deductions_total | total_deductions | net_amount_if_available | number_of_source_documents | missing_source_documents | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-02 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-03 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-04 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-05 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-06 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-07 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-08 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-09 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-10 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-11 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-12 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2025-01 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2025-02 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2025-03 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2025-04 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2025-05 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |
| 2025-06 |  |  |  |  |  |  |  |  |  | 0 | YES | No Gutschrift/Abrechnung source document detected for this month. |

## Missing Months

- 2024-02
- 2024-03
- 2024-04
- 2024-05
- 2024-06
- 2024-07
- 2024-08
- 2024-09
- 2024-10
- 2024-11
- 2024-12
- 2025-01
- 2025-02
- 2025-03
- 2025-04
- 2025-05
- 2025-06

## Important Observations

- The analyzer does not invent numbers. Empty values mean no reliable value was extracted.
- PDF text extraction depends on an available PDF text backend such as `pypdf`, `PyPDF2`, or `pdftotext`.
- RAR extraction depends on the optional `rarfile` package and a compatible local RAR backend.
- Duplicate detection uses document number, document date, amount, and file hash.
- Duplicate documents detected: 0

## List of Source Documents

- No Enrico/Sachsenpower source documents detected

## Limitations

- OCR is not implemented.
- Scanned PDFs without embedded text cannot be analyzed until OCR is added.
- The script extracts conservative text patterns only; complex tables may require manual review.
- Missing source documents are marked when no Gutschrift or Abrechnung was detected for the month.

## Next Documents Needed

- Missing Gutschrift or Abrechnung documents for all months marked as missing.
- Any Sachsenpower/Enrico ZIP, RAR, EML, PDF, TXT, or CSV files not yet placed in `_INBOX` or `03_Documents - Документи - Dokumente`.
- Original PDFs with embedded text or OCR-ready scanned copies for months where values are empty.
