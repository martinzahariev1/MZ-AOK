# Enrico Deductions Report Output

This folder contains generated outputs from the Enrico Financial Deduction Analyzer.

## Files

- `enrico_deductions_monthly.csv`: monthly deduction summary from 2024-02 to 2025-06.
- `enrico_deductions_monthly.xlsx`: spreadsheet version of the monthly summary.
- `enrico_deductions_detailed.csv`: extracted document and position-level detail rows.
- `enrico_deductions_detailed.xlsx`: spreadsheet version of the detailed table.
- `missing_months.csv`: months where no Gutschrift or Abrechnung source document was detected.
- `duplicate_documents.csv`: documents skipped as duplicates.
- `processing_log.txt`: scan, extraction, and limitation log.
- `ENRICO_DEDUCTION_ANALYSIS.md`: markdown report.

## Interpretation

Empty financial values mean the analyzer could not reliably extract a number. LOW confidence rows require manual review.
