# Criminal Case Evidence Validation

Validation passed: YES

| Check | Result |
| --- | --- |
| every factual row has source_file | PASS |
| every monetary amount traces to source | PASS |
| every communication event traces to source | PASS |
| no blank treated as zero | PASS |
| no inferred payment | PASS |
| no inferred non-payment | PASS |
| no inferred intent | PASS |
| AOK chronology separated from other Krankenkassen | PASS |
| dates are contribution periods where appropriate, not arbitrary first dates found in documents | PASS |
| duplicates do not inflate amounts | PASS |

## Notes
- Payment is recorded only when the source row or payment/bank context supports it.
- Non-payment is recorded only as arrears/outstanding where the source wording supports it; reminders are not converted into unpaid balances unless an amount is stated.
- Duplicate rows were collapsed by date/period/Krankenkasse/event/amount/source/snippet, with duplicate references retained where detected.
- The AOK PLUS chronology is written separately in 02_AOK_PLUS_CHRONOLOGY and 10_AOK_PLUS_EVIDENCE_RECONSTRUCTION.
