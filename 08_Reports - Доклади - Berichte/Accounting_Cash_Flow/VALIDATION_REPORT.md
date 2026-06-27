# Validation Report

## Scope

Validation sampled up to 20 existing rows per major category from current CSV outputs. It used only `Accounting_Organized`, existing report CSV/XLSX outputs, recovered text files, and processing logs/reports. No analyzer code or extracted tables were modified by the validation engine.

## Overall Accuracy

- Sampled rows: 90
- Overall extraction accuracy: 100.0%
- Incorrect rows: 0
- Partial rows: 0

## Accuracy By Category

| Category | Correct | Partial | Wrong | Accuracy |
| --- | --- | --- | --- | --- |
| Payroll | 10 | 0 | 0 | 100.0% |
| Health Insurance | 20 | 0 | 0 | 100.0% |
| Tax | 20 | 0 | 0 | 100.0% |
| Operating Cost | 20 | 0 | 0 | 100.0% |
| Enrico | 20 | 0 | 0 | 100.0% |

## Wrong Extractions

- None

## Parser Improvements Ranked By Impact

- No parser improvements required by sampled rows.

## Method

- `CORRECT`: sampled key fields were directly supported by source text/path.
- `PARTIAL`: source was unreadable or only some key fields were directly supported.
- `WRONG`: source text/path clearly contradicted the row or showed a category/field parser mistake.
- Random seed: `20260627`.
