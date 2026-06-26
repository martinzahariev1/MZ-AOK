# Accounting Cash Flow Reconstruction Analyzer

## Purpose

This tool scans accounting documents prepared by Marco/accounting and creates monthly cash-flow reconstruction tables for `01.2024` through `06.2025`.

It is conservative by design: empty fields are preferred over guessed numbers.

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

The script scans:

`00_INBOX - Входящи - Eingang/Accounting`

Supported files:

- PDF
- ZIP
- RAR
- TXT
- CSV
- XLSX
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
- `monthly_cash_flow_reconstruction.csv` / `.xlsx`
- `missing_accounting_months.csv`
- `duplicate_accounting_documents.csv`
- `processing_log.txt`
- `README.md`
- `ACCOUNTING_CASH_FLOW_RECONSTRUCTION.md`

## Limits

- OCR is not implemented.
- Scanned PDFs without embedded text may be unreadable.
- Complex accounting tables may require manual review.
- If a value cannot be extracted, it is left empty and confidence is marked `LOW`.

