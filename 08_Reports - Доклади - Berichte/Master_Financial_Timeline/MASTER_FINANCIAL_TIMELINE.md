# Master Financial Timeline

## Scope
This report consolidates existing validated outputs for 01.2024 to 06.2025. It does not run new extraction and does not introduce new source values.

The report distinguishes accounting profit from liquidity pressure: Enrico deductions are treated as visible revenue/liquidity reductions, while accounting obligations remain payroll, health insurance, taxes, and operating costs from the accounting cash-flow reconstruction.

## Data Sources
- `08_Reports - ??????? - Berichte/Enrico_Deductions/enrico_deductions_monthly.csv`
- `08_Reports - ??????? - Berichte/Accounting_Cash_Flow/monthly_cash_flow_reconstruction.csv`
- `08_Reports - ??????? - Berichte/Accounting_Cash_Flow/VALIDATION_REPORT.md`
- `08_Reports - ??????? - Berichte/Accounting_Cash_Flow/validation_results.csv`

## Validation Accuracy Summary
- Sampled rows: 90
- Overall sampled validation accuracy: 100.0%
- Tax sampled validation accuracy: 100.0%
- Operating Cost sampled validation accuracy: 100.0%
- Validation rows showed no incorrect or partial rows in the latest validation report.

## Monthly Table
| Month | Enrico deductions | Coincident | Sendungsverlust | Refunds | Payroll brutto | Payroll netto | Health due | Health paid | Health unpaid | Tax due | Tax paid | Tax unpaid | Operating due | Operating paid | Operating unpaid | Visible obligations | Visible paid | Visible unpaid | Confidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 2024-01 |  |  |  |  |  |  |  |  |  | 268.68 | 83428.40 | 20.00 | 163577.00 |  | 20.00 | 163845.68 | 83428.40 | 40.00 | Accounting MEDIUM; Enrico MISSING |
| 2024-02 |  |  |  |  |  |  |  |  |  | 11182.78 | 84182.26 | 20.00 | 659.11 |  | 20.00 | 11841.89 | 84182.26 | 40.00 | Accounting MEDIUM; Enrico PARTIAL |
| 2024-03 | -6549.17 | -6245.92 |  |  |  |  |  |  |  | 2432.55 | 60336.62 | 20.00 | 20.00 |  | 20.00 | 2452.55 | 60336.62 | 40.00 | Accounting MEDIUM; Enrico HIGH |
| 2024-04 |  |  |  |  |  |  |  |  |  | 363.00 | 80205.88 | 20.00 | 20.00 |  | 20.00 | 383.00 | 80205.88 | 40.00 | Accounting MEDIUM; Enrico PARTIAL |
| 2024-05 |  |  |  |  |  |  |  | -216.63 | 68848.69 | 435.13 | 71122.06 | 20.00 | 20.00 |  | 20.00 | 455.13 | 70905.43 | 68888.69 | Accounting MEDIUM; Enrico PARTIAL |
| 2024-06 |  |  |  |  |  |  |  |  |  | 1137.00 | 84326.62 | 20.00 | 20.00 |  | 20.00 | 1157.00 | 84326.62 | 40.00 | Accounting MEDIUM; Enrico PARTIAL |
| 2024-07 |  |  |  |  |  |  |  | 915.48 |  | 1267.39 | 76420.25 | 20.00 | 20.00 |  | 20.00 | 1287.39 | 77335.73 | 40.00 | Accounting MEDIUM; Enrico PARTIAL |
| 2024-08 |  |  |  | 916.00 |  |  |  |  |  | 2515.77 | 59703.77 | 20.00 | 20.00 |  | 20.00 | 2535.77 | 59703.77 | 40.00 | Accounting MEDIUM; Enrico PARTIAL |
| 2024-09 |  |  |  |  |  |  |  |  |  |  | 27518.62 |  | 303.00 |  |  | 303.00 | 27518.62 |  | Accounting MEDIUM; Enrico HIGH |
| 2024-10 |  |  |  |  |  |  |  |  |  | 1260.94 | 32235.47 | 20.00 | 20.00 |  | 20.00 | 1280.94 | 32235.47 | 40.00 | Accounting MEDIUM; Enrico HIGH |
| 2024-11 | 163.65 |  | 147.65 | 100.00 |  |  |  | 1165.16 |  | 202.33 | 36397.47 | 20.00 | 18555.34 |  | 20.00 | 18757.67 | 37562.63 | 40.00 | Accounting MEDIUM; Enrico HIGH |
| 2024-12 | 12.50 |  | 12.50 | 95.95 |  |  |  |  |  | 19.00 | 25280.51 | 20.00 | 17882.56 |  | 20.00 | 17901.56 | 25280.51 | 40.00 | Accounting MEDIUM; Enrico HIGH |
| 2025-01 | 67.89 |  | 51.89 |  |  |  |  |  |  |  | 25375.10 |  | 18938.06 |  |  | 18938.06 | 25375.10 |  | Accounting MEDIUM; Enrico HIGH |
| 2025-02 | 89.29 |  | 73.29 | 75.91 |  |  |  |  |  |  | 27177.70 |  | 637.84 |  |  | 637.84 | 27177.70 |  | Accounting MEDIUM; Enrico HIGH |
| 2025-03 | 239.05 |  | 223.05 | 50.00 |  |  | 801.50 |  |  | 11081.00 | 4856.33 | 40.00 | 168090.51 |  | 40.00 | 179973.01 | 4856.33 | 80.00 | Accounting MEDIUM; Enrico HIGH |
| 2025-04 | 18.50 |  | 2.50 |  |  |  |  |  |  |  | 3752.34 |  |  |  |  |  | 3752.34 |  | Accounting MEDIUM; Enrico PARTIAL |
| 2025-05 |  |  |  |  |  |  |  |  |  |  | 6947.38 |  | 9985.47 |  |  | 9985.47 | 6947.38 |  | Accounting MEDIUM; Enrico HIGH |
| 2025-06 |  |  |  |  |  |  | 30000.00 | 5.20 | 2494.00 | 23263.84 | 2358.09 |  | 5323.90 |  |  | 58587.74 | 2363.29 | 2494.00 | Accounting MEDIUM; Enrico PARTIAL |

## First Visible Financial Pressure Points
- First visible accounting unpaid balance: 2024-01 with total visible unpaid 40.00.
- First visible Enrico deduction/revenue pressure: 2024-03 with Enrico deductions -6549.17.

Strongest visible pressure months by visible unpaid plus absolute Enrico deductions:
- 2024-05: visible unpaid 68888.69; visible obligations 455.13
- 2024-03: visible unpaid 40.00; Enrico deductions -6549.17; visible obligations 2452.55
- 2025-06: visible unpaid 2494.00; visible obligations 58587.74
- 2025-03: visible unpaid 80.00; Enrico deductions 239.05; visible obligations 179973.01
- 2024-11: visible unpaid 40.00; Enrico deductions 163.65; visible obligations 18757.67

## Months With Missing Or Weak Data
- 2024-01: Accounting MEDIUM; Enrico MISSING; No Enrico monthly row available
- 2024-02: Accounting MEDIUM; Enrico PARTIAL; Enrico: Enrico documents found, but no main monthly Gutschrift/Abrechnung detected.; Enrico has documents but no main monthly Gutschrift detected
- 2024-03: Accounting MEDIUM; Enrico HIGH; Enrico: Main monthly Gutschrift/Abrechnung found.
- 2024-04: Accounting MEDIUM; Enrico PARTIAL; Enrico: No Enrico source document detected for this month.; No Enrico monthly source document detected
- 2024-05: Accounting MEDIUM; Enrico PARTIAL; Enrico: No Enrico source document detected for this month.; No Enrico monthly source document detected
- 2024-06: Accounting MEDIUM; Enrico PARTIAL; Enrico: No Enrico source document detected for this month.; No Enrico monthly source document detected
- 2024-07: Accounting MEDIUM; Enrico PARTIAL; Enrico: No Enrico source document detected for this month.; No Enrico monthly source document detected
- 2024-08: Accounting MEDIUM; Enrico PARTIAL; Enrico: Only refund/correction documents found; main monthly Gutschrift/Abrechnung is missing.; Enrico has documents but no main monthly Gutschrift detected
- 2024-09: Accounting MEDIUM; Enrico HIGH; Enrico: Main monthly Gutschrift/Abrechnung found.
- 2024-10: Accounting MEDIUM; Enrico HIGH; Enrico: Main monthly Gutschrift/Abrechnung found.
- 2024-11: Accounting MEDIUM; Enrico HIGH; Enrico: Main monthly Gutschrift/Abrechnung found.
- 2024-12: Accounting MEDIUM; Enrico HIGH; Enrico: Main monthly Gutschrift/Abrechnung found.
- 2025-01: Accounting MEDIUM; Enrico HIGH; Enrico: Main monthly Gutschrift/Abrechnung found.
- 2025-02: Accounting MEDIUM; Enrico HIGH; Enrico: Main monthly Gutschrift/Abrechnung found.
- 2025-03: Accounting MEDIUM; Enrico HIGH; Enrico: Main monthly Gutschrift/Abrechnung found.
- 2025-04: Accounting MEDIUM; Enrico PARTIAL; Enrico: Enrico documents found, but no main monthly Gutschrift/Abrechnung detected.; Enrico has documents but no main monthly Gutschrift detected
- 2025-05: Accounting MEDIUM; Enrico HIGH; Enrico: Main monthly Gutschrift/Abrechnung found.
- 2025-06: Accounting MEDIUM; Enrico PARTIAL; Enrico: No Enrico source document detected for this month.; No Enrico monthly source document detected

## Important Limitations
- Missing values are left empty; blanks do not mean zero.
- Enrico deductions reduce visible liquidity/revenue but are not counted as accounting obligations in `total_visible_obligations`.
- Accounting profit cannot be inferred from this liquidity timeline alone.
- This report relies on existing validated CSV/XLSX outputs only and does not inspect original documents again.
- Validation is sample-based and supports report quality, but it is not a legal or audit opinion.
- The timeline does not make legal conclusions about responsibility, insolvency timing, or causation.

## Suggested Documents Still Needed
- Missing Enrico main monthly Gutschrift/Abrechnung documents for months flagged as Enrico partial or missing.
- Complete payroll monthly summaries where payroll brutto/netto is blank.
- Complete health insurance contribution statements and payment confirmations for months with blank due/paid/unpaid values.
- Tax office and city tax statements for months with blank tax fields.
- Operating-cost invoices and payment proofs for months with blank due/paid/unpaid values.

## Key Notes By Month
- 2024-01: No Enrico monthly row available
- 2024-02: Enrico: Enrico documents found, but no main monthly Gutschrift/Abrechnung detected.; Enrico has documents but no main monthly Gutschrift detected
- 2024-03: Enrico: Main monthly Gutschrift/Abrechnung found.
- 2024-04: Enrico: No Enrico source document detected for this month.; No Enrico monthly source document detected
- 2024-05: Enrico: No Enrico source document detected for this month.; No Enrico monthly source document detected
- 2024-06: Enrico: No Enrico source document detected for this month.; No Enrico monthly source document detected
- 2024-07: Enrico: No Enrico source document detected for this month.; No Enrico monthly source document detected
- 2024-08: Enrico: Only refund/correction documents found; main monthly Gutschrift/Abrechnung is missing.; Enrico has documents but no main monthly Gutschrift detected
- 2024-09: Enrico: Main monthly Gutschrift/Abrechnung found.
- 2024-10: Enrico: Main monthly Gutschrift/Abrechnung found.
- 2024-11: Enrico: Main monthly Gutschrift/Abrechnung found.
- 2024-12: Enrico: Main monthly Gutschrift/Abrechnung found.
- 2025-01: Enrico: Main monthly Gutschrift/Abrechnung found.
- 2025-02: Enrico: Main monthly Gutschrift/Abrechnung found.
- 2025-03: Enrico: Main monthly Gutschrift/Abrechnung found.
- 2025-04: Enrico: Enrico documents found, but no main monthly Gutschrift/Abrechnung detected.; Enrico has documents but no main monthly Gutschrift detected
- 2025-05: Enrico: Main monthly Gutschrift/Abrechnung found.
- 2025-06: Enrico: No Enrico source document detected for this month.; No Enrico monthly source document detected
