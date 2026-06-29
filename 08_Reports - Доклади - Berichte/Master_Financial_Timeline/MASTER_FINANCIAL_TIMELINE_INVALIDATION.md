# Master Financial Timeline Invalidation

The previous `MASTER_FINANCIAL_TIMELINE.md`, `master_financial_timeline.csv`, and `master_financial_timeline.xlsx` are invalidated.

## Why It Is Invalid

- It reused monthly rollups instead of strict row-level evidence.
- Some tax paid values appear to include unrelated bank/accounting movements rather than clearly identified tax payments.
- Some operating cost due values appear to include invoice totals that do not clearly represent monthly due/open obligations.
- Payroll brutto/netto and health insurance fields were often blank even though underlying documents exist.
- Accounting totals, payments, obligations, invoice totals, and unrelated amounts were mixed in one timeline.

## Replacement

Use `08_Reports - ??????? - Berichte/Master_Financial_Timeline_Strict/MASTER_FINANCIAL_TIMELINE_STRICT.md`.

The strict replacement uses an evidence ledger. Every number in a monthly total must trace to a ledger row with source file, amount type, confidence, snippet/pattern, and extraction method. Ambiguous amounts are classified as `UNKNOWN_AMOUNT_DO_NOT_SUM` and excluded from monthly totals.
