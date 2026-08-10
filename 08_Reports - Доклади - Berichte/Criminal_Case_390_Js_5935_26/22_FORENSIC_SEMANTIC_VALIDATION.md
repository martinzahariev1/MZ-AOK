# Forensic Semantic Validation

Validation passed: YES

| Check | Result |
| --- | --- |
| no duplicate event counted twice | PASS |
| aliases normalized | PASS |
| ordinary payments not called repayments | PASS |
| ordinary accounting emails not called resolution actions | PASS |
| Hauptzollamt not treated as Krankenkasse unless underlying creditor identified | PASS |
| 2023-10-30 event inspected against original source | PASS |
| no fact altered to fit Martin's recollection | PASS |
| all material claims trace to source | PASS |

## Critical Contradictions
- The previous 2023-10-30 `AOK arrears/enforcement notice` label contradicts the original source, which is an accountant invoice.
- The old `pre-investigation resolution` and `late payment/repayment` counts were semantically too broad and included routine accounting/payment rows.
