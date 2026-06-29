# Strict Gap Resolver Report

## Scope
This resolver searched existing evidence files only, plus readable email subjects/bodies and attachment names. It did not modify original evidence and did not change extraction logic. Organizer manifests/logs were used as context but are not listed as candidate source documents.

## Search Inputs
- `strict_timeline_gaps.csv`
- `00_INBOX - ??????? - Eingang/Accounting`
- `00_INBOX - ??????? - Eingang/Accounting_Organized`
- `00_INBOX - ??????? - Eingang/Enrico`
- Existing manifests and unprocessed reports as context only

## Summary
- Total gaps: 69
- Candidate rows: 432
- Gaps with HIGH-confidence candidates: 64
- OCR blocked gaps: 0
- Password blocked gaps: 0
- Gaps with no candidate: 0
- Manual review needed gaps: 5

## Top Files Likely To Close Most Gaps
- 00_INBOX - Входящи - Eingang/Accounting/8. Überweisungsnachweise bzw. Barzahlungsquittungen/# 2024/10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf: 18 matching gap candidates
- 00_INBOX - Входящи - Eingang/Accounting/audit2024/10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf: 17 matching gap candidates
- 00_INBOX - Входящи - Eingang/Accounting/ihrelohnauswertungenapril2025/Lohnauswertungen.pdf: 16 matching gap candidates
- 00_INBOX - Входящи - Eingang/Accounting/ihrelohnauswertungen/Lohnauswertungen.pdf: 15 matching gap candidates
- 00_INBOX - Входящи - Eingang/Accounting_Organized/06_Bank_Payments/10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf: 15 matching gap candidates
- 00_INBOX - Входящи - Eingang/Accounting_Organized/06_Bank_Payments/10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024__copy2.pdf: 15 matching gap candidates
- 00_INBOX - Входящи - Eingang/Accounting_Organized/06_Bank_Payments/10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024__copy3.pdf: 14 matching gap candidates
- 00_INBOX - Входящи - Eingang/Accounting_Organized/14_Duplicates/10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf: 14 matching gap candidates
- 00_INBOX - Входящи - Eingang/Accounting_Organized/02_Payroll/Lohnauswertungen_Juli_2025__copy2.pdf: 9 matching gap candidates
- 00_INBOX - Входящи - Eingang/Accounting_Organized/02_Payroll/Lohnauswertungen_Juli_2025__copy4.pdf: 9 matching gap candidates

## Gap Status By Month And Category
| Month | Category | Status | Best Candidate | Confidence | Next Action |
| --- | --- | --- | --- | --- | --- |
| 2024-01 | payroll | CANDIDATE_FOUND | Lohnauswertungen.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-01 | health insurance | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-01 | operating cost | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-01 | Enrico | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-02 | payroll | CANDIDATE_FOUND | Lohnauswertungen.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-02 | health insurance | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-02 | operating cost | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-02 | Enrico | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-03 | payroll | CANDIDATE_FOUND | Lohnauswertungen.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-03 | health insurance | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-03 | operating cost | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-03 | tax | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-04 | payroll | CANDIDATE_FOUND | Lohnauswertungen_Juli_2025__copy2.pdf | HIGH | USE_EXISTING |
| 2024-04 | health insurance | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-04 | operating cost | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-04 | Enrico | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-05 | payroll | CANDIDATE_FOUND | Lohnauswertungen.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-05 | health insurance | CANDIDATE_FOUND | 10001_05-2024_DivAuswertungen_DivMitarbeiter_EZ1.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-05 | operating cost | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-05 | Enrico | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-06 | payroll | CANDIDATE_FOUND | Lohnauswertungen_Juli_2025__copy2.pdf | HIGH | USE_EXISTING |
| 2024-06 | health insurance | CANDIDATE_FOUND | 10001_06-2024_DivAuswertungen_DivMitarbeiter_HZ1.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-06 | operating cost | MANUAL_REVIEW_NEEDED | 10001_06-2024_DivAuswertungen_DivMitarbeiter_HZ1.pdf | MEDIUM | MOVE_TO_CATEGORY |
| 2024-06 | Enrico | MANUAL_REVIEW_NEEDED | 10001_06-2024_DivAuswertungen_DivMitarbeiter_HZ1.pdf | MEDIUM | MOVE_TO_CATEGORY |
| 2024-07 | payroll | CANDIDATE_FOUND | Lohnauswertungen_Juli_2024.pdf | HIGH | USE_EXISTING |
| 2024-07 | health insurance | CANDIDATE_FOUND | Entgeltbescheinigungen 07-2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-07 | operating cost | MANUAL_REVIEW_NEEDED | Entgeltbescheinigungen 07-2024.pdf | MEDIUM | MOVE_TO_CATEGORY |
| 2024-07 | Enrico | CANDIDATE_FOUND | 07.2024.pdf | HIGH | USE_EXISTING |
| 2024-08 | payroll | CANDIDATE_FOUND | Lohnauswertungen_Juli_2025__copy2.pdf | HIGH | USE_EXISTING |
| 2024-08 | health insurance | CANDIDATE_FOUND | Entgeltbescheinigungen 08-2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-08 | operating cost | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2023.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-08 | tax | CANDIDATE_FOUND | Entgeltbescheinigungen 08-2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-08 | Enrico | CANDIDATE_FOUND | Gutschrift 34-2024 Zahariev Martin 04.10.2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-09 | payroll | CANDIDATE_FOUND | Lohnauswertungen_Juli_2025__copy2.pdf | HIGH | USE_EXISTING |
| 2024-09 | health insurance | CANDIDATE_FOUND | 10001_09-2024_DivAuswertungen_DivMitarbeiter_QZ1.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-09 | operating cost | MANUAL_REVIEW_NEEDED | 10001_09-2024_DivAuswertungen_DivMitarbeiter_QZ1.pdf | MEDIUM | MOVE_TO_CATEGORY |
| 2024-10 | payroll | CANDIDATE_FOUND | Lohnauswertungen_Juli_2025__copy2.pdf | HIGH | USE_EXISTING |
| 2024-10 | health insurance | CANDIDATE_FOUND | Entgeltbescheinigungen 10-2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-10 | operating cost | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2023.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-11 | payroll | CANDIDATE_FOUND | Lohnauswertungen_Juli_2025__copy2.pdf | HIGH | USE_EXISTING |
| 2024-11 | health insurance | CANDIDATE_FOUND | Entgeltbescheinigungen 11-2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-11 | operating cost | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2023.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-12 | payroll | CANDIDATE_FOUND | Lohnauswertungen_Juli_2025__copy2.pdf | HIGH | USE_EXISTING |
| 2024-12 | health insurance | CANDIDATE_FOUND | Entgeltbescheinigungen 12-2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2024-12 | operating cost | MANUAL_REVIEW_NEEDED | Entgeltbescheinigungen 12-2024.pdf | MEDIUM | MOVE_TO_CATEGORY |
| 2025-01 | payroll | CANDIDATE_FOUND | Lohnauswertungen_Juli_2025__copy2.pdf | HIGH | USE_EXISTING |
| 2025-01 | health insurance | CANDIDATE_FOUND | Entgeltbescheinigungen 12-2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-01 | operating cost | CANDIDATE_FOUND | Entgeltbescheinigungen 04-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-02 | payroll | CANDIDATE_FOUND | Lohnauswertungen.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-02 | health insurance | CANDIDATE_FOUND | Entgeltbescheinigungen 02-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-02 | operating cost | CANDIDATE_FOUND | Entgeltbescheinigungen 04-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-03 | payroll | CANDIDATE_FOUND | Lohnauswertungen.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-03 | health insurance | CANDIDATE_FOUND | 10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-03 | operating cost | CANDIDATE_FOUND | Entgeltbescheinigungen 04-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-03 | tax | CANDIDATE_FOUND | Tabelle nach § 175 InsO mit Grund des Bestreitens.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-04 | payroll | CANDIDATE_FOUND | Entgeltbescheinigungen 04-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-04 | health insurance | CANDIDATE_FOUND | Entgeltbescheinigungen 04-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-04 | operating cost | CANDIDATE_FOUND | Entgeltbescheinigungen 04-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-04 | tax | CANDIDATE_FOUND | Entgeltbescheinigungen 04-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-04 | Enrico | CANDIDATE_FOUND | gutschrift April 2025 zahariev.pdf | HIGH | USE_EXISTING |
| 2025-05 | payroll | CANDIDATE_FOUND | Entgeltbescheinigungen 05-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-05 | health insurance | CANDIDATE_FOUND | Entgeltbescheinigungen 05-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-05 | operating cost | CANDIDATE_FOUND | Entgeltbescheinigungen 04-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-05 | tax | CANDIDATE_FOUND | Entgeltbescheinigungen 05-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-06 | payroll | CANDIDATE_FOUND | Entgeltbescheinigungen 06-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-06 | health insurance | CANDIDATE_FOUND | Entgeltbescheinigungen 06-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-06 | operating cost | CANDIDATE_FOUND | Entgeltbescheinigungen 06-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-06 | tax | CANDIDATE_FOUND | Entgeltbescheinigungen 06-2025.pdf | HIGH | MOVE_TO_CATEGORY |
| 2025-06 | Enrico | CANDIDATE_FOUND | Zahlungsavis Zahariev Juni 2025.pdf | HIGH | USE_EXISTING |

## Method Notes
- HIGH confidence requires both month and category/type matches in a readable source file or email/attachment metadata, plus a strong category-specific filename/path/document type.
- OCR and password blocked files are listed as candidates when filename/path/category matches but text could not be read.
- Files in `Unknown_To_Review` are included and marked for manual review.
- Files in duplicate folders are included but downgraded to manual review.
- Candidate status does not mean the document should be summed automatically; it means the file may close a strict evidence gap after review or extraction improvement.
