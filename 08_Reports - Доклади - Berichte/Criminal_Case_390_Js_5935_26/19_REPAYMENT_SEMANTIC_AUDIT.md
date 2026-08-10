# Repayment Semantic Audit

Old broad count: 853
New true arrears repayment count: 1

## Classification Counts
- LATE_FEE_PAYMENT: 4
- NORMAL_MONTHLY_PAYMENT: 247
- TRUE_ARREARS_REPAYMENT: 1
- UNCLEAR: 601

## True Arrears Repayment Preview
| classification | reason | event_date | contribution_period | Krankenkasse | amount_paid | amount_outstanding | event_type | source_file | source_snippet | confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TRUE_ARREARS_REPAYMENT | Payment is linked to arrears/enforcement/overdue context. |  | 2025-06 | AOK Plus | 5.20 | 2494.00 | HEALTH_INSURANCE_EXTRACTED_ROW | 00_INBOX - Входящи - Eingang/Accounting_Organized/04_Health_Insurance/Tabelle nach § 175 InsO mit Grund des Bestreitens. | Beiträge EUR GESAMTFORDERUNG 30.000,00 | HIGH |
