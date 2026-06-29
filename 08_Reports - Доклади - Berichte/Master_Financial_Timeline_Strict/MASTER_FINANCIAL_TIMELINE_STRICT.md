# Master Financial Timeline Strict

## Why Previous Master Report Was Invalidated
The previous master report is invalid because it reused broad monthly rollups that could mix accounting totals, payments, obligations, invoice totals, and unrelated amounts. This strict rebuild does not reuse those master values. It uses row-level evidence only and excludes unclear amounts from totals.

## Methodology
- Source rows were read from existing Enrico detailed rows and Accounting Cash Flow row-level timelines only.
- No new extraction was run.
- Every numeric value is represented in `financial_evidence_ledger.csv`.
- Monthly totals sum only rows marked `include_in_monthly_totals = YES`.
- `UNKNOWN_AMOUNT_DO_NOT_SUM` rows are never summed.
- Bank movements are not treated as tax paid unless the row has a clear tax creditor and tax type.
- Generic tax `Gesamtbetrag` rows are not treated as tax due unless supported by a stricter due/open/tax-assessment label.
- Generic invoice totals are not treated as operating obligations unless the matched label clearly says due/open/paid/unpaid.

## Rule: Every Number Must Trace To Evidence Row
Every number in `master_financial_timeline_strict.csv` must be traceable to a row in `financial_evidence_ledger.csv` with source file, category/document context, amount type, confidence, source snippet or matched pattern, and extraction method. Missing values remain blank, not zero.

## Monthly Strict Table
| Month | Enrico Coincident | Enrico Sendungsverlust | Enrico Other | Enrico Refunds | Payroll Brutto | Payroll Netto | Health Due | Health Paid | Health Unpaid | Health Late Fees | Tax Due | Tax Paid | Tax Unpaid | Operating Due | Operating Paid | Operating Unpaid | Revenue | Excluded Unknown Rows | Source Files | Confidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2024-01 |  |  |  |  |  |  |  |  |  |  |  | 77464.27 |  |  |  |  |  | 12 | 9 | LOW |
| 2024-02 |  |  |  |  |  |  |  |  |  |  |  | 18516.48 |  |  |  |  |  | 10 | 6 | LOW |
| 2024-03 | -6245.92 |  | -303.25 |  |  |  |  |  |  |  |  |  |  |  |  |  | 186243.20 | 8 | 4 | LOW |
| 2024-04 |  |  |  |  |  |  |  |  |  |  |  | 22853.99 |  |  |  |  |  | 8 | 4 | LOW |
| 2024-05 |  |  |  |  |  |  |  |  |  |  |  | 24018.01 |  |  |  |  |  | 12 | 6 | LOW |
| 2024-06 |  |  |  |  |  |  |  |  |  |  |  | 23553.36 |  |  |  |  |  | 8 | 4 | LOW |
| 2024-07 |  |  |  |  |  |  |  |  |  |  |  | 23067.09 |  |  |  |  |  | 9 | 5 | LOW |
| 2024-08 |  |  |  | 916.00 |  |  |  |  |  |  |  |  |  |  |  |  |  | 8 | 4 | LOW |
| 2024-09 |  |  |  |  |  |  |  |  |  |  |  | 22536.76 |  |  |  |  | 176234.29 | 4 | 6 | LOW |
| 2024-10 |  |  |  |  |  |  |  |  |  |  |  | 24226.58 |  |  |  |  | 197442.02 | 9 | 6 | LOW |
| 2024-11 |  | 147.65 | 16.00 | 100.00 |  |  |  |  |  |  |  | 27948.98 |  |  |  |  | 232318.76 | 12 | 13 | LOW |
| 2024-12 |  | 12.50 |  | 95.95 |  |  |  |  |  |  |  | 23984.73 |  |  |  |  | 188941.38 | 9 | 10 | LOW |
| 2025-01 |  | 51.89 | 16.00 |  |  |  |  |  |  |  |  | 24159.32 |  |  |  |  | 189578.90 | 5 | 10 | LOW |
| 2025-02 |  | 73.29 | 16.00 | 75.91 |  |  |  |  |  |  |  | 22523.36 |  |  |  |  | 170271.25 | 4 | 10 | LOW |
| 2025-03 |  | 223.05 | 16.00 | 50.00 |  |  |  |  |  |  |  |  |  |  |  |  | 202395.66 | 15 | 12 | LOW |
| 2025-04 |  | 2.50 | 16.00 |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 2 | 4 | LOW |
| 2025-05 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 120491.84 | 5 | 6 | LOW |
| 2025-06 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 9 | 4 | LOW |

## Missing Data By Month
- 2024-01: Missing strict included values for: payroll, health insurance, operating cost; 12 excluded/unknown amount rows not summed
- 2024-02: Missing strict included values for: payroll, health insurance, operating cost; 10 excluded/unknown amount rows not summed
- 2024-03: Missing strict included values for: payroll, health insurance, tax, operating cost; 8 excluded/unknown amount rows not summed
- 2024-04: Missing strict included values for: payroll, health insurance, operating cost; 8 excluded/unknown amount rows not summed
- 2024-05: Missing strict included values for: payroll, health insurance, operating cost; 12 excluded/unknown amount rows not summed
- 2024-06: Missing strict included values for: payroll, health insurance, operating cost; 8 excluded/unknown amount rows not summed
- 2024-07: Missing strict included values for: payroll, health insurance, operating cost; 9 excluded/unknown amount rows not summed
- 2024-08: Missing strict included values for: payroll, health insurance, tax, operating cost; 8 excluded/unknown amount rows not summed
- 2024-09: Missing strict included values for: payroll, health insurance, operating cost; 4 excluded/unknown amount rows not summed
- 2024-10: Missing strict included values for: payroll, health insurance, operating cost; 9 excluded/unknown amount rows not summed
- 2024-11: Missing strict included values for: payroll, health insurance, operating cost; 12 excluded/unknown amount rows not summed
- 2024-12: Missing strict included values for: payroll, health insurance, operating cost; 9 excluded/unknown amount rows not summed
- 2025-01: Missing strict included values for: payroll, health insurance, operating cost; 5 excluded/unknown amount rows not summed
- 2025-02: Missing strict included values for: payroll, health insurance, operating cost; 4 excluded/unknown amount rows not summed
- 2025-03: Missing strict included values for: payroll, health insurance, tax, operating cost; 15 excluded/unknown amount rows not summed
- 2025-04: Missing strict included values for: payroll, health insurance, tax, operating cost; 2 excluded/unknown amount rows not summed
- 2025-05: Missing strict included values for: payroll, health insurance, tax, operating cost; 5 excluded/unknown amount rows not summed
- 2025-06: Missing strict included values for: payroll, health insurance, tax, operating cost; 9 excluded/unknown amount rows not summed

## Excluded Unknown Amounts By Month
- 2024-01: 12 excluded/unknown amount rows
- 2024-02: 10 excluded/unknown amount rows
- 2024-03: 8 excluded/unknown amount rows
- 2024-04: 8 excluded/unknown amount rows
- 2024-05: 12 excluded/unknown amount rows
- 2024-06: 8 excluded/unknown amount rows
- 2024-07: 9 excluded/unknown amount rows
- 2024-08: 8 excluded/unknown amount rows
- 2024-09: 4 excluded/unknown amount rows
- 2024-10: 9 excluded/unknown amount rows
- 2024-11: 12 excluded/unknown amount rows
- 2024-12: 9 excluded/unknown amount rows
- 2025-01: 5 excluded/unknown amount rows
- 2025-02: 4 excluded/unknown amount rows
- 2025-03: 15 excluded/unknown amount rows
- 2025-04: 2 excluded/unknown amount rows
- 2025-05: 5 excluded/unknown amount rows
- 2025-06: 9 excluded/unknown amount rows

## High-Confidence Months
- None. No month has complete strict evidence with zero excluded unknown amount rows.

## Low-Confidence Months
- 2024-01
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

## Documents Still Needed
- Complete payroll summaries with explicit brutto/netto totals by month.
- Health insurance statements that clearly distinguish due, paid, unpaid, and late fees by month.
- Tax notices/payment confirmations that clearly identify tax type, creditor, due/paid/unpaid status, and month.
- Operating cost documents that clearly state due/open/unpaid or paid amounts, not only invoice totals.
- Missing Enrico monthly Gutschrift/Abrechnung documents for partial or missing months.

## No Legal Conclusions
This strict timeline is an evidence-indexed financial reconstruction aid. It does not make legal conclusions about liability, insolvency timing, causation, or intent.
