# 69,976.32 EUR Email Amount Reconstruction

Original inspected: `00_INBOX - Входящи - Eingang\Accounting\Remaining health insurances for 09_2024 und 10_2024.eml`

Email date/time: Thu, 05 Dec 2024 09:38:41 +0000
Sender: "Brunettin, Marco" <marco@brunettin.de>
Recipient: Martin zahariev <martin.zahariev@gmail.com>
Subject: Remaining health insurances for 09/2024 und 10/2024

Independent recalculation from source components: 69,976.32 EUR (matches 69.976,32 EUR when formatted in German notation).

- CONFIRMED_OVERDUE_TOTAL: 0,00 EUR
- CURRENT_BUT_NOT_PROVEN_OVERDUE_TOTAL: 0,00 EUR
- UNKNOWN_STATUS_TOTAL: 69.976,32 EUR

Reason: the source wording says `Here this is still to pay`, but it does not state due dates. Therefore the complete total is reconstructed as still-to-pay, not independently classified as legally/chronologically overdue from this source alone.

| component_id | krankenkasse | contribution_period | amount | payment_status_wording | due_date_if_stated | whether_already_overdue_on_05_12_2024 | whether_currently_due | whether_future_current_obligation | whether_subsequently_paid | subsequent_payment_source_if_found | status_bucket | source_snippet |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 69K-01 | EK Techniker Krankenkasse | 10/2024 | 88,53 | Email/forwarded text says `Here this is still to pay`. |  | UNKNOWN - due date not stated in source | UNKNOWN from this source | UNKNOWN from this source | NOT SOURCE-CONFIRMED in targeted review |  | UNKNOWN_STATUS | IBAN Zweck Betrag EK Techniker Krankenkasse DE33 1004 0000 0545 4665 00 89878877, Beitrag 10/2024 88,53 KKH Kaufm. Krankenkasse DE52 2508 0020 0170 0170 00 89878877, Beitrag 09+10/2024 29.910,60 BKK Viactiv DE16 4301 011 |
| 69K-02 | KKH Kaufm. Krankenkasse | 09+10/2024 | 29.910,60 | Email/forwarded text says `Here this is still to pay`. |  | UNKNOWN - due date not stated in source | UNKNOWN from this source | UNKNOWN from this source | NOT SOURCE-CONFIRMED in targeted review |  | UNKNOWN_STATUS | IBAN Zweck Betrag EK Techniker Krankenkasse DE33 1004 0000 0545 4665 00 89878877, Beitrag 10/2024 88,53 KKH Kaufm. Krankenkasse DE52 2508 0020 0170 0170 00 89878877, Beitrag 09+10/2024 29.910,60 BKK Viactiv DE16 4301 011 |
| 69K-03 | BKK Viactiv | 09/2024 | 564,78 | Email/forwarded text says `Here this is still to pay`. |  | UNKNOWN - due date not stated in source | UNKNOWN from this source | UNKNOWN from this source | NOT SOURCE-CONFIRMED in targeted review |  | UNKNOWN_STATUS | IBAN Zweck Betrag EK Techniker Krankenkasse DE33 1004 0000 0545 4665 00 89878877, Beitrag 10/2024 88,53 KKH Kaufm. Krankenkasse DE52 2508 0020 0170 0170 00 89878877, Beitrag 09+10/2024 29.910,60 BKK Viactiv DE16 4301 011 |
| 69K-04 | EK Barmer | 09+10/2024 | 3.970,18 | Email/forwarded text says `Here this is still to pay`. |  | UNKNOWN - due date not stated in source | UNKNOWN from this source | UNKNOWN from this source | NOT SOURCE-CONFIRMED in targeted review |  | UNKNOWN_STATUS | IBAN Zweck Betrag EK Techniker Krankenkasse DE33 1004 0000 0545 4665 00 89878877, Beitrag 10/2024 88,53 KKH Kaufm. Krankenkasse DE52 2508 0020 0170 0170 00 89878877, Beitrag 09+10/2024 29.910,60 BKK Viactiv DE16 4301 011 |
| 69K-05 | AOK Hessen | 09/2024 | 1.244,22 | Email/forwarded text says `Here this is still to pay`. |  | UNKNOWN - due date not stated in source | UNKNOWN from this source | UNKNOWN from this source | NOT SOURCE-CONFIRMED in targeted review |  | UNKNOWN_STATUS | IBAN Zweck Betrag EK Techniker Krankenkasse DE33 1004 0000 0545 4665 00 89878877, Beitrag 10/2024 88,53 KKH Kaufm. Krankenkasse DE52 2508 0020 0170 0170 00 89878877, Beitrag 09+10/2024 29.910,60 BKK Viactiv DE16 4301 011 |
| 69K-06 | BKK Linde | 09+10/2024 | 2.601,50 | Email/forwarded text says `Here this is still to pay`. |  | UNKNOWN - due date not stated in source | UNKNOWN from this source | UNKNOWN from this source | NOT SOURCE-CONFIRMED in targeted review |  | UNKNOWN_STATUS | IBAN Zweck Betrag EK Techniker Krankenkasse DE33 1004 0000 0545 4665 00 89878877, Beitrag 10/2024 88,53 KKH Kaufm. Krankenkasse DE52 2508 0020 0170 0170 00 89878877, Beitrag 09+10/2024 29.910,60 BKK Viactiv DE16 4301 011 |
| 69K-07 | AOK PLUS | 09+10/2024 | 26.044,15 | Email/forwarded text says `Here this is still to pay`. |  | UNKNOWN - due date not stated in source | UNKNOWN from this source | UNKNOWN from this source | NOT SOURCE-CONFIRMED in targeted review |  | UNKNOWN_STATUS | IBAN Zweck Betrag EK Techniker Krankenkasse DE33 1004 0000 0545 4665 00 89878877, Beitrag 10/2024 88,53 KKH Kaufm. Krankenkasse DE52 2508 0020 0170 0170 00 89878877, Beitrag 09+10/2024 29.910,60 BKK Viactiv DE16 4301 011 |
| 69K-08 | EK DAK Gesundheit | 09+10/2024 | 5.552,36 | Email/forwarded text says `Here this is still to pay`. |  | UNKNOWN - due date not stated in source | UNKNOWN from this source | UNKNOWN from this source | NOT SOURCE-CONFIRMED in targeted review |  | UNKNOWN_STATUS | IBAN Zweck Betrag EK Techniker Krankenkasse DE33 1004 0000 0545 4665 00 89878877, Beitrag 10/2024 88,53 KKH Kaufm. Krankenkasse DE52 2508 0020 0170 0170 00 89878877, Beitrag 09+10/2024 29.910,60 BKK Viactiv DE16 4301 011 |
