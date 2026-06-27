# Validation Report

## Scope

Validation sampled up to 20 existing rows per major category from current CSV outputs. It used only `Accounting_Organized`, existing report CSV/XLSX outputs, recovered text files, and processing logs/reports. No analyzer code or extracted tables were modified by the validation engine.

## Overall Accuracy

- Sampled rows: 100
- Overall extraction accuracy: 32.0%
- Incorrect rows: 28
- Partial rows: 40

## Accuracy By Category

| Category | Correct | Partial | Wrong | Accuracy |
| --- | --- | --- | --- | --- |
| Payroll | 11 | 7 | 2 | 55.0% |
| Health Insurance | 10 | 5 | 5 | 50.0% |
| Tax | 3 | 10 | 7 | 15.0% |
| Operating Cost | 3 | 14 | 3 | 15.0% |
| Enrico | 5 | 4 | 11 | 25.0% |

## Wrong Extractions

| Category | Source file | Extracted value | Actual/source evidence | Probable parser mistake |
| --- | --- | --- | --- | --- |
| Payroll | 00_INBOX - Входящи - Eingang/Accounting_Organized/03_Employee_Payslips/Entgeltbescheinigungen 06-2025.pdf | {"month": "2000-01", "total_netto": "18.07"} | source filename month hint: 06-2025 | Month parser selected a nearby date or unrelated filename token. |
| Payroll | 00_INBOX - Входящи - Eingang/Accounting_Organized/09_Enrico_Forwarded/Docutain Dokument.pdf | {"month": "2024-07", "total_netto": "2.06"} | sampled values are supported by source text/path | Month parser selected a nearby date or unrelated filename token. |
| Health Insurance | 00_INBOX - Входящи - Eingang/Accounting_Organized/02_Payroll/10001_06-2024_DivAuswertungen_DivMitarbeiter_HZ1.pdf | {"month": "2024-12", "insurance_name": "AOK Plus", "amount_due": "1118.00", "amount_paid": "1806.00"} | amount_due: not found; amount_paid: not found | Month parser selected a nearby date or unrelated filename token. |
| Health Insurance | 00_INBOX - Входящи - Eingang/Accounting_Organized/02_Payroll/10001_08-2024_Brutto_NettoProbe_00074_NZ1.pdf | {"month": "2024-01", "insurance_name": "TK", "amount_paid": "1664.52"} | amount_paid: not found | Month parser selected a nearby date or unrelated filename token. |
| Health Insurance | 00_INBOX - Входящи - Eingang/Accounting_Organized/02_Payroll/10001_09-2024_Brutto_NettoProbe_00051_QZ1.pdf | {"month": "2024-01", "insurance_name": "TK"} | sampled values are supported by source text/path | Month parser selected a nearby date or unrelated filename token. |
| Health Insurance | 00_INBOX - Входящи - Eingang/Accounting_Organized/03_Employee_Payslips/Entgeltbescheinigungen 04-2025.pdf | {"month": "2003-01", "insurance_name": "AOK Plus", "amount_due": "28.04", "amount_paid": "4518.02", "due_date": "28.04.2025"} | source filename month hint: 04-2025; amount_paid: not found | Month parser selected a nearby date or unrelated filename token. |
| Health Insurance | 00_INBOX - Входящи - Eingang/Accounting_Organized/09_Enrico_Forwarded/Martin Zahariev Transporte 2055 07.02.2025 Sendungsverluste.pdf | {"month": "2055-07", "insurance_name": "TK", "amount_due": "12.11"} | sampled values are supported by source text/path | Month parser selected a nearby date or unrelated filename token. |
| Tax | 00_INBOX - Входящи - Eingang/Accounting_Organized/02_Payroll/10001_03-2024_DivAuswertungen_DivMitarbeiter_8Z1.pdf | {"month": "2024-11", "tax_type": "Lohnsteuer", "amount_due": "2413.55", "amount_paid": "11.04"} | amount_due: not found | Month parser selected a nearby date or unrelated filename token. |
| Tax | 00_INBOX - Входящи - Eingang/Accounting_Organized/02_Payroll/10001_04-2024_DivAuswertungen_DivMitarbeiter_BZ1.pdf | {"month": "2024-08", "tax_type": "Lohnsteuer", "amount_due": "366.67", "amount_paid": "1548.00"} | amount_paid: not found | Month parser selected a nearby date or unrelated filename token. |
| Tax | 00_INBOX - Входящи - Eingang/Accounting_Organized/02_Payroll/10001_09-2024_Brutto_NettoProbe_00051_QZ1.pdf | {"month": "2024-01", "tax_type": "Lohnsteuer"} | sampled values are supported by source text/path | Month parser selected a nearby date or unrelated filename token. |
| Tax | 00_INBOX - Входящи - Eingang/Accounting_Organized/03_Employee_Payslips/Entgeltbescheinigungen 06-2025.pdf | {"month": "2000-01", "creditor": "Finanzamt", "tax_type": "Lohnsteuer", "amount_due": "26.06", "amount_paid": "2474.01", "due_date": "26.06.2025"} | source filename month hint: 06-2025; amount_paid: not found | Month parser selected a nearby date or unrelated filename token. |
| Tax | 00_INBOX - Входящи - Eingang/Accounting_Organized/05_Taxes/Accountings 02-2025.pdf | {"month": "2025-10", "creditor": "Finanzamt", "tax_type": "Umsatzsteuer", "amount_due": "13.36", "amount_paid": "0.00", "unpaid_balance": "10.04"} | source filename month hint: 02-2025 | Month parser selected a nearby date or unrelated filename token. |
| Tax | 00_INBOX - Входящи - Eingang/Accounting_Organized/05_Taxes/Accountings 05-2024.pdf | {"month": "2024-11", "creditor": "Finanzamt", "tax_type": "Umsatzsteuer", "amount_due": "12.52", "amount_paid": "0.00", "unpaid_balance": "11.07"} | source filename month hint: 05-2024 | Month parser selected a nearby date or unrelated filename token. |
| Tax | 00_INBOX - Входящи - Eingang/Accounting_Organized/06_Bank_Payments/10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2024.pdf | {"month": "2002-01", "creditor": "Finanzamt", "tax_type": "other public liability", "amount_due": "4.01", "amount_paid": "3.01", "unpaid_balance": "68848.69"} | unpaid_balance: not found | Month parser selected a nearby date or unrelated filename token. |
| Operating Cost | 00_INBOX - Входящи - Eingang/Accounting_Organized/03_Employee_Payslips/Entgeltbescheinigungen 06-2025.pdf | {"month": "2000-01", "category": "insurance", "amount_due": "4799.13", "amount_paid": "2474.01"} | source filename month hint: 06-2025; amount_due: not found; amount_paid: not found | Month parser selected a nearby date or unrelated filename token. |
| Operating Cost | 00_INBOX - Входящи - Eingang/Accounting_Organized/06_Bank_Payments/10. Nachweis von Lohnzahlungen - Bankkontoumsätze 2023.pdf | {"month": "2002-01", "category": "fuel", "amount_due": "49.94", "unpaid_balance": "-213.26"} | sampled values are supported by source text/path | Month parser selected a nearby date or unrelated filename token. |
| Operating Cost | 00_INBOX - Входящи - Eingang/Accounting_Organized/03_Employee_Payslips/8. Lohnabrechnungen aller Mitarbeiter.zip | {"month": "2023-10", "category": "accounting fees"} | sampled values are supported by source text/path | Month parser selected a nearby date or unrelated filename token. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/04_Health_Insurance/04-2021 #9109.pdf | {"month": "2021-04", "document_number": "1637805507", "document_type": "Gutschrift", "amount": "12.04"} | source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/04_Health_Insurance/06-2021 #9109.pdf | {"month": "2021-06", "document_type": "Gutschrift", "amount": "11.06"} | source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/04_Health_Insurance/07-2021 #9109.pdf | {"month": "2021-07", "document_type": "Gutschrift", "amount": "14.07"} | source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/04_Health_Insurance/12-2021 #9109.pdf | {"month": "2021-12", "document_type": "Gutschrift", "amount": "27.12"} | source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/06_Bank_Payments/Zahlungsavis Zahariev Juni 2025.pdf | {"month": "2025-07", "document_number": "2810", "document_type": "Rechnung", "amount": "30.06"} | source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/08_Operating_Costs/Rechnung 2765 Zahariev Hermes Scannermiete.pdf | {"month": "2025-04", "document_number": "02765", "document_type": "Rechnung", "amount": "637.84"} | source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/08_Operating_Costs/Rechnung 2778 Zahariev Hermes Scannermiete.pdf | {"month": "2025-05", "document_number": "02778", "document_type": "Rechnung", "amount": "599.76"} | source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/08_Operating_Costs/Rechnung 2789 Zahariev TF Touren.pdf | {"month": "2025-06", "document_number": "02789", "document_type": "Rechnung", "amount": "8282.40"} | amount: not found; source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/08_Operating_Costs/Rechnung 2799 Bearbeitungsgebühr 10.06.2025 Zahariev.pdf | {"month": "2025-06", "document_number": "02799", "document_type": "Rechnung", "amount": "53.55"} | source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/08_Operating_Costs/Rechnung 2811 Zahariev scannermiete.pdf | {"month": "2025-07", "document_number": "02811", "document_type": "Rechnung", "amount": "333.20"} | source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |
| Enrico | 00_INBOX - Входящи - Eingang/Accounting_Organized/08_Operating_Costs/Unternehmerabrechnung - VP 120-2400035649.pdf | {"month": "2024-01", "document_number": "120-2400035649", "document_type": "GUTSCHRIFT", "document_date": "26.03.2024", "amount": "608.64"} | source is not in Enrico_Forwarded category | Enrico detector is too broad and accepts non-Enrico health-insurance/accounting documents. |

## Parser Improvements Ranked By Impact

| Recommended fix | Affected sampled rows |
| --- | --- |
| Add field-specific validation patterns and source text snippets for this document type. | 40 |
| Prefer Leistungszeitraum/document period labels and filename month patterns over first date token. | 17 |
| Restrict category detection to folder hints plus stronger Enrico/Sachsenpower terms. | 11 |

## Method

- `CORRECT`: sampled key fields were directly supported by source text/path.
- `PARTIAL`: source was unreadable or only some key fields were directly supported.
- `WRONG`: source text/path clearly contradicted the row or showed a category/field parser mistake.
- Random seed: `20260627`.
