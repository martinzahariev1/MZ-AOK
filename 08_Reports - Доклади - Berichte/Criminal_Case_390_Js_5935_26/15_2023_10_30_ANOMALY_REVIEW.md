# 2023-10-30 Anomaly Review

Classification: MISCLASSIFIED_EVENT

The original source is an accountant invoice from Marco Brunettin dated 2023-10-30. It is addressed to Favorit MP, Inh. Martin Zahariev, but it is not an AOK document, not a social-insurance contribution notice, and not an enforcement notice.

The prior extractor appears to have misread `Pfändungen`, `offenen Rechnungsbetrag`, `Requests of reimbursement of wages for the health insurances`, and the VAT rate `19,00 %` as health-insurance arrears.

| classification | source_filename | source_path | source_page | document_date | exact_AOK_entity | contribution_period_concerned | amount | document_type | actually_states_arrears | is_enforcement_notice | concerns_social_insurance_contributions | concerns_martin_zahariev_business | due_date | payment_status | evidence_of_subsequent_payment | evidence_of_later_clearance | later_unbedenklichkeitsbescheinigung_no_arrears | exact_relevant_source_text_snippet | confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MISCLASSIFIED_EVENT | 90f3df27-1ca1-4b3a-9f1b-e33ffd37f10a.pdf | 00_INBOX - Входящи - Eingang/Accounting/accountings112023/90f3df27-1ca1-4b3a-9f1b-e33ffd37f10a.pdf | 1-2 | 2023-10-30 |  | September/2023 appears as accountant-service billing period, not a social-insurance contribution period. | 1,664.33 EUR accountant invoice total; 19.00 is VAT rate, not arrears amount. | Accountant invoice from Marco Brunettin / Steuerberatung | NO | NO | NO - only mentions wage-accounting services and reimbursement requests for health insurances. | YES - addressed to Favorit MP, Inh. Martin Zahariev. |  | Open accountant invoice amount requested; no health-insurance payment status stated. |  | No AOK clearance for this alleged event; Barmer certificate dated 2024-09-17 shows no Barmer arrears only. | No later AOK/AOK PLUS no-arrears certificate found for this event in the current reconstruction. | Rechnung Mandantennummer: Rechnungsnummer: 42303 230946 Rechnungsdatum: 30.10.2023 Mitarbeiter: Marco Brunettin, LL.M. S | HIGH |

No legal conclusion is made.
