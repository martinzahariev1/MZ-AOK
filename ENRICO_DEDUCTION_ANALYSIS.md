# Enrico Deduction Analysis

## Purpose

Analyze documents from Enrico Weissflog / Sachsenpower and create monthly deduction tables for financial review.

## Period Analyzed

February 2024 through June 2025.

## Total Deductions by Category

- Abschlag Coincident: -6245.92
- Abschlag Mitnahme: -180.25
- Abschlag Quittungslose Sendung: -123.00
- Sendungsverlust: 658.31
- Scannermiete: 80.00
- Scanner-related invoices: 
- Other deductions: 

## Monthly Summary Table

| month | gross_credit_total | gross_credit_gutschrift_total | abschlag_coincident_total | abschlag_mitnahme_total | abschlag_quittungslose_sendung_total | sendungsverlust_total | scannermiete_total | other_deductions_total | total_deductions | total_deductions_negative | refunds_total_positive | net_effect | net_amount_if_available | number_of_source_documents | missing_source_documents | source_document_numbers | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-02 |  |  |  |  |  |  |  |  |  |  |  |  |  | 1 | YES |  | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-03 | 186243.20 | 186243.20 | -6245.92 | -180.25 | -123.00 |  |  |  | -6549.17 | -6549.17 |  | 179694.03 |  | 1 | NO | 7-2024 |  |
| 2024-04 |  |  |  |  |  |  |  |  |  |  |  |  |  | 0 | YES |  | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-05 |  |  |  |  |  |  |  |  |  |  |  |  |  | 0 | YES |  | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-06 |  |  |  |  |  |  |  |  |  |  |  |  |  | 0 | YES |  | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-07 |  |  |  |  |  |  |  |  |  |  |  |  |  | 0 | YES |  | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-08 |  |  |  |  |  |  |  |  |  |  | 916.00 | 916.00 |  | 1 | YES | 34-2024 | No Gutschrift/Abrechnung source document detected for this month. |
| 2024-09 | 176234.29 | 176234.29 |  |  |  |  |  |  |  |  |  | 176234.29 |  | 2 | NO | 31-2024 |  |
| 2024-10 | 197442.02 | 197442.02 |  |  |  |  |  |  |  |  |  | 197442.02 |  | 2 | NO | 38-2024 |  |
| 2024-11 | 232318.76 | 232318.76 |  |  |  | 147.65 | 16.00 |  | 163.65 |  | 100.00 | 232582.41 |  | 7 | NO | 01999; 02000; 02001; 02002; 42-2024; 51-2025 |  |
| 2024-12 | 188941.38 | 188941.38 |  |  |  | 12.50 |  |  | 12.50 |  | 95.95 | 189049.83 |  | 6 | NO | 02014; 02015; 02023; 44-2024; 55-2025 |  |
| 2025-01 | 189578.90 | 189578.90 |  |  |  | 51.89 | 16.00 |  | 67.89 |  |  | 189646.79 |  | 6 | NO | 02035; 02036; 02037; 02038; 48-2025 |  |
| 2025-02 | 170271.25 | 170271.25 |  |  |  | 73.29 | 16.00 |  | 89.29 |  | 75.91 | 170436.45 |  | 7 | NO | 02054; 02055; 02056; 02057; 52-2025; 60-2025 |  |
| 2025-03 | 202395.66 | 202395.66 |  |  |  | 223.05 | 16.00 |  | 239.05 |  | 50.00 | 202684.71 |  | 7 | NO | 02068; 02069; 02070; 02766; 57-2025; 71-2025 |  |
| 2025-04 |  |  |  |  |  | 2.50 | 16.00 |  | 18.50 |  |  | 18.50 |  | 3 | YES | 02764; 02765; 02767 | No Gutschrift/Abrechnung source document detected for this month. |
| 2025-05 | 120491.84 | 120491.84 |  |  |  |  |  |  |  |  |  | 120491.84 |  | 2 | NO | 66-2025 |  |
| 2025-06 |  |  |  |  |  |  |  |  |  |  |  |  |  | 0 | YES |  | No Gutschrift/Abrechnung source document detected for this month. |

## Missing Months

- 2024-02
- 2024-04
- 2024-05
- 2024-06
- 2024-07
- 2024-08
- 2025-04
- 2025-06

## Important Observations

- The analyzer does not invent numbers. Empty values mean no reliable value was extracted.
- PDF text extraction depends on an available PDF text backend such as `pypdf`, `PyPDF2`, or `pdftotext`.
- RAR extraction depends on the optional `rarfile` package and a compatible local RAR backend.
- Duplicate detection uses document number, document date, amount, and file hash.
- Duplicate documents detected: 1

## List of Source Documents

- 00_INBOX - Входящи - Eingang/Enrico/07.2024.pdf
- 00_INBOX - Входящи - Eingang/Enrico/Auffälligkeiten vorige Woche.eml
- 00_INBOX - Входящи - Eingang/Enrico/Gutschrift 34-2024 Zahariev Martin 04.10.2024.pdf
- 00_INBOX - Входящи - Eingang/Enrico/Martin Zahariev Gutschrift 51 17.02.2025.pdf
- 00_INBOX - Входящи - Eingang/Enrico/Martin Zahariev Gutschrift 55 08.03.2025.pdf
- 00_INBOX - Входящи - Eingang/Enrico/Martin Zahariev Transporte 2058 08.03.2025 Scannermiete.pdf
- 00_INBOX - Входящи - Eingang/Enrico/abrechnungmai2025.zip::Leistungsnachweis Zahariev Mai 25 Sachsenpower GmbH & Co. KG.pdf
- 00_INBOX - Входящи - Eingang/Enrico/abrechnungmai2025.zip::gutschrift 66 Mai 2025 zahariev.pdf
- 00_INBOX - Входящи - Eingang/Enrico/abrechnungseptember.zip::Gutschrift 31-2024 Zahariev Martin 30.09.2024.pdf
- 00_INBOX - Входящи - Eingang/Enrico/abrechnungseptember.zip::Leistungsnachweis September 2024.pdf
- 00_INBOX - Входящи - Eingang/Enrico/fwgutschriftrechnungen.zip::Rechnung 2764 Zahariev Hermes Kleidung.pdf
- 00_INBOX - Входящи - Eingang/Enrico/fwgutschriftrechnungen.zip::Rechnung 2765 Zahariev Hermes Scannermiete.pdf
- 00_INBOX - Входящи - Eingang/Enrico/fwgutschriftrechnungen.zip::Rechnung 2766 Zahariev Hermes Sendungsverlust.pdf
- 00_INBOX - Входящи - Eingang/Enrico/fwgutschriftrechnungen.zip::Rechnung 2767 Zahariev Hermes Bearbeitungsgebuhr.pdf
- 00_INBOX - Входящи - Eingang/Enrico/fwgutschriftrechnungen.zip::gutschrift 05.04. 2025 zahariev.pdf
- 00_INBOX - Входящи - Eingang/Enrico/gutschrift 71 2025 zahariev Sendungsverlust.pdf
- 00_INBOX - Входящи - Eingang/Enrico/gutschriftundrechnungen.zip::Gutschrift 42-2024 Zahariev Martin 30.11.2024.pdf
- 00_INBOX - Входящи - Eingang/Enrico/gutschriftundrechnungen.zip::Rechnung 2014 vom 05.12.2024 Sendungsverlust Zahariev.pdf
- 00_INBOX - Входящи - Eingang/Enrico/gutschriftundrechnungen.zip::Rechnung 2015 07.12.2024 Martin Zahariev.pdf
- 00_INBOX - Входящи - Eingang/Enrico/gutschriftundrechnungen.zip::Rechnung 2023 vom 07.12.2024  Zahariev HERMES Bekleidung.pdf
- 00_INBOX - Входящи - Eingang/Enrico/original_msg.eml
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendengutschrift382024zaharievmartin31_10_.zip::Gutschrift 38-2024 Zahariev Martin 31.10.2024.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendengutschrift382024zaharievmartin31_10_.zip::Leistungsnachweis Oktober 2024.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendengutschrift422024zaharievmartin30_11_.zip::Leistungsnachweis November 2024.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendengutschrift442024zaharievmartin31_12_.zip::Gutschrift 44-2024 Zahariev Martin 31.12.2024.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendengutschrift442024zaharievmartin31_12_.zip::Leistungsnachweis Dezember Zahariev 2024.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendengutschriftmrz2025zahariev_pdf.zip::Leistungsnachweis Subunternehmer Sachsenpower GmbH & Co. KG.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendengutschriftmrz2025zahariev_pdf.zip::gutschrift märz 2025 zahariev.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenleistungsnachweismartinzaharievfebruar.zip::Leistungsnachweis Martin Zahariev Februar 2025.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenleistungsnachweismartinzaharievfebruar.zip::Martin Zahariev Gutschrift 52 28.02.2025.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievgutschrift4831_01_2025_.zip::Leistungsnachweis Martin Zahariev Januar 2025.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievgutschrift4831_01_2025_.zip::Martin Zahariev Gutschrift 48 31.01.2025.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievtransporte203608_01_202.zip::Martin Zahariev Transporte 2035 08.01.2025 Hermes Bekleidung.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievtransporte203608_01_202.zip::Martin Zahariev Transporte 2036 08.01.2025 Scannermiete.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievtransporte203608_01_202.zip::Martin Zahariev Transporte 2037 08.01.2025 Sendungsverluste.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievtransporte203608_01_202.zip::Martin Zahariev Transporte 2038 08.01.2025 Bearbeitungsgebühr.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievtransporte205407_02_202.zip::Martin Zahariev Transporte 2054 07.02.2025 Scannermiete.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievtransporte205407_02_202.zip::Martin Zahariev Transporte 2055 07.02.2025 Sendungsverluste.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievtransporte205407_02_202.zip::Martin Zahariev Transporte 2056 07.02.2025 Bearbeitungsgebühr.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievtransporte205407_02_202.zip::Martin Zahariev Transporte 2057 07.02.2025 Hermes Bekleidung.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievtransporte207008_03_202.zip::Martin Zahariev Transporte 2069 08.03.2025 Sendungsverluste.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenmartinzaharievtransporte207008_03_202.zip::Martin Zahariev Transporte 2070 08.03.2025 Sendungsverluste.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenrechnung1999vom06_11_2024sendungsverl.zip::Rechnung 1999 vom 06.11.2024 Sendungsverlust Zahariev.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenrechnung1999vom06_11_2024sendungsverl.zip::Rechnung 2000 vom 06.11.2024  Zahariev Bearbeitung.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenrechnung1999vom06_11_2024sendungsverl.zip::Rechnung 2001 vom 06.11.2024  Zahariev Hermes Bekleidung.pdf
- 00_INBOX - Входящи - Eingang/Enrico/peremailsendenrechnung1999vom06_11_2024sendungsverl.zip::Rechnung 2002 vom 06.11.2024 Scannermiete Zahariev.pdf
- 00_INBOX - Входящи - Eingang/Enrico/rechnungenaus062025.zip::Rechnung 2810 Zahariev TF Touren.pdf
- 00_INBOX - Входящи - Eingang/Enrico/rechnungenaus062025.zip::Rechnung 2811 Zahariev scannermiete.pdf
- 00_INBOX - Входящи - Eingang/Enrico/rechnungenaus062025.zip::Rechnung 2812 Zahariev Hermes Sendungsverlust.pdf
- 00_INBOX - Входящи - Eingang/Enrico/rechnungenaus062025.zip::Rechnung 2813 zahariev bearbeitungsgeb_hr.pdf
- 00_INBOX - Входящи - Eingang/Enrico/rechnungenaus062025.zip::Rechnung 2814 zahariev bekleidung.pdf
- 00_INBOX - Входящи - Eingang/Enrico/rechnungenaus062025.zip::Zahlungsavis Zahariev Juni 2025.pdf
- 00_INBOX - Входящи - Eingang/Enrico/rechnungenfrjuli25.zip::Rechnung 2836 zahariev sendungsverlust.pdf
- 00_INBOX - Входящи - Eingang/Enrico/rechnungenfrjuli25.zip::Rechnung 2837 zahariev bearbeitungsgebühr.pdf
- _INBOX/kundigung Dokument.pdf

## Limitations

- OCR is not implemented.
- Scanned PDFs without embedded text cannot be analyzed until OCR is added.
- The script extracts conservative text patterns only; complex tables may require manual review.
- Missing source documents are marked when no Gutschrift or Abrechnung was detected for the month.

## Next Documents Needed

- Missing Gutschrift or Abrechnung documents for all months marked as missing.
- Any Sachsenpower/Enrico ZIP, RAR, EML, PDF, TXT, or CSV files not yet placed in `_INBOX` or `03_Documents - Документи - Dokumente`.
- Original PDFs with embedded text or OCR-ready scanned copies for months where values are empty.
