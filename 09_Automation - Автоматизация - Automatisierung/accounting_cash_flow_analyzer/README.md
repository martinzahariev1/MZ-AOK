# Accounting Cash Flow Reconstruction Analyzer

## Purpose

This tool scans accounting documents prepared by Marco/accounting and creates monthly cash-flow reconstruction tables for `01.2024` through `06.2025`.

It is conservative by design: empty fields are preferred over guessed numbers, and every unreadable, duplicate, partial, or unsupported file is recorded in the audit outputs.

## Run

From this folder:

```powershell
python analyze_accounting_cash_flow.py
```

From the repository root:

```powershell
python "09_Automation - Автоматизация - Automatisierung/accounting_cash_flow_analyzer/analyze_accounting_cash_flow.py"
```

## Input

The script scans the organized accounting evidence folder:

`00_INBOX - Входящи - Eingang/Accounting_Organized`

It processes the focused financial categories:

- `02_Payroll`
- `03_Employee_Payslips`
- `04_Health_Insurance`
- `05_Taxes`
- `06_Bank_Payments`
- `08_Operating_Costs`
- `09_Enrico_Forwarded`
- `10_BWA_Reports`
- `11_Contribution_Lists`
- `12_Liability_Overview`

It records but does not process `13_Unknown_To_Review` and `14_Duplicates`.

Supported files:

- PDF
- ZIP
- RAR
- TXT
- CSV
- XLSX
- DOCX
- EML

PDF password used for protected PDFs:

`10001`

## Output

Reports are written to:

`08_Reports - Доклади - Berichte/Accounting_Cash_Flow`

Generated files:

- `employee_timeline.csv` / `.xlsx`
- `payroll_timeline.csv` / `.xlsx`
- `health_insurance_timeline.csv` / `.xlsx`
- `tax_timeline.csv` / `.xlsx`
- `operating_costs_timeline.csv` / `.xlsx`
- `enrico_cross_check.csv` / `.xlsx`
- `monthly_cash_flow_reconstruction.csv` / `.xlsx`
- `missing_accounting_months.csv`
- `duplicate_accounting_documents.csv`
- `unprocessed_files.csv` / `.xlsx`
- `unprocessed_files_report.md`
- `processing_log.txt`
- `README.md`
- `ACCOUNTING_CASH_FLOW_RECONSTRUCTION.md`

## File Audit Statuses

Each processed file receives one final status in the logs or audit tables:

- `PROCESSED_STRUCTURED`
- `PROCESSED_PARTIAL`
- `DUPLICATE`
- `ENRICO_CROSS_CHECK`
- `UNPROCESSED_WITH_REASON`

## Limits

- OCR is not implemented.
- Scanned PDFs without embedded text may be unreadable.
- RAR extraction depends on local 7-Zip, unrar, or equivalent support.
- If RAR extraction tools are unavailable, affected RAR files are reported as `RAR extraction unavailable`.
- Complex accounting tables may require manual review.
- If a value cannot be extracted, it is left empty and confidence is marked `LOW`.
