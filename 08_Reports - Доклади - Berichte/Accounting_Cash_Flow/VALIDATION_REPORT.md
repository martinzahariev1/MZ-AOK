# Validation Report

## Scope

Validation sampled up to 20 existing rows per major category from current CSV outputs. It used only `Accounting_Organized`, existing report CSV/XLSX outputs, recovered text files, and processing logs/reports. No analyzer code or extracted tables were modified by the validation engine.

## Overall Accuracy

- Sampled rows: 90
- Overall extraction accuracy: 90.0%
- Incorrect rows: 1
- Partial rows: 8

## Accuracy By Category

| Category | Correct | Partial | Wrong | Accuracy |
| --- | --- | --- | --- | --- |
| Payroll | 10 | 0 | 0 | 100.0% |
| Health Insurance | 20 | 0 | 0 | 100.0% |
| Tax | 13 | 7 | 0 | 65.0% |
| Operating Cost | 18 | 1 | 1 | 90.0% |
| Enrico | 20 | 0 | 0 | 100.0% |

## Wrong Extractions

| Category | Source file | Extracted value | Actual/source evidence | Probable parser mistake |
| --- | --- | --- | --- | --- |
| Operating Cost | 00_INBOX - Входящи - Eingang/Accounting_Organized/08_Operating_Costs/Ihre Lohnauswertungen.eml | {"month": "2024-09", "category": "accounting fees"} | sampled values are supported by source text/path | Month parser selected a nearby date or unrelated filename token. |

## Parser Improvements Ranked By Impact

| Recommended fix | Affected sampled rows |
| --- | --- |
| Add field-specific validation patterns and source text snippets for this document type. | 8 |
| Prefer Leistungszeitraum/document period labels and filename month patterns over first date token. | 1 |

## Method

- `CORRECT`: sampled key fields were directly supported by source text/path.
- `PARTIAL`: source was unreadable or only some key fields were directly supported.
- `WRONG`: source text/path clearly contradicted the row or showed a category/field parser mistake.
- Random seed: `20260627`.
