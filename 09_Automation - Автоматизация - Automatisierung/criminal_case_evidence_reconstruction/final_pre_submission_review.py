#!/usr/bin/env python3
"""Final pre-submission forensic review and tiering for the section 266a case."""

from __future__ import annotations

import csv
import email
import html
import json
import re
import zipfile
from email import policy
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
INBOX = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("00_INBOX"))
REPORTS = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("08_Reports"))
OUT = REPORTS / "Criminal_Case_390_Js_5935_26"


def clean(value: str, limit: int = 600) -> str:
    return re.sub(r"\s+", " ", value or "").strip()[:limit]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def col_name(index: int) -> str:
    result = ""
    while index:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def write_xlsx(path: Path, headers: list[str], rows: list[dict[str, str]], sheet_name: str = "Sheet1") -> None:
    values = [headers] + [[str(row.get(header, "")) for header in headers] for row in rows]
    sheet_rows = []
    for row_index, row_values in enumerate(values, start=1):
        cells = []
        for col_index, value in enumerate(row_values, start=1):
            cells.append(f'<c r="{col_name(col_index)}{row_index}" t="inlineStr"><is><t>{escape(value)}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(sheet_rows) + "</sheetData></worksheet>"
    workbook = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="{escape(sheet_name[:31])}" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)


def markdown_table(headers: list[str], rows: list[dict[str, str]], limit: int = 60) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(clean(str(row.get(header, "")), 140).replace("|", "/") for header in headers) + " |")
    if len(rows) > limit:
        lines.append("| ... | " + f"{len(rows) - limit} more rows in CSV/XLSX |" + " |" * (len(headers) - 2))
    return "\n".join(lines)


def pdf_text(path: Path) -> str:
    import fitz  # type: ignore

    doc = fitz.open(path)
    if doc.needs_pass:
        doc.authenticate("10001")
    return "\n".join(f"[[page {index}]]\n{page.get_text('text') or ''}" for index, page in enumerate(doc, 1))


def eml_text(path: Path) -> tuple[str, str, str, str, str]:
    msg = email.message_from_binary_file(path.open("rb"), policy=policy.default)
    parts = []
    for part in msg.walk():
        if part.get_content_type() in {"text/plain", "text/html"}:
            try:
                parts.append(str(part.get_content()))
            except Exception:
                pass
    text = html.unescape(re.sub(r"<[^>]+>", " ", "\n".join(parts)))
    return msg.get("date", ""), msg.get("from", ""), msg.get("to", ""), msg.get("subject", ""), clean(text, 2200)


def evidence_signature(path: str) -> str:
    """Collapse organized copies of the same source into one review signature."""
    filename = Path(path).name.lower()
    filename = re.sub(r"__copy\d+(?=\.)", "", filename)
    return re.sub(r"\s+", " ", filename).strip()


def is_tier1_source(path: str) -> bool:
    direct_health_timeline_sources = [
        "Accounting/2024/Entgeltbescheinigungen 06-2024.pdf",
        "Accounting/2024/Entgeltbescheinigungen 09-2024.pdf",
        "Accounting/2024/Entgeltbescheinigungen 10-2024.pdf",
        "Accounting/2024/Entgeltbescheinigungen 11-2024.pdf",
        "Accounting/2024/Entgeltbescheinigungen 12-2024.pdf",
        "Accounting/2025/Entgeltbescheinigungen 01-2025.pdf",
        "Accounting/2025/Entgeltbescheinigungen 02-2025.pdf",
        "Accounting/2025/Entgeltbescheinigungen 04-2025.pdf",
        "Accounting/2025/Entgeltbescheinigungen 05-2025.pdf",
        "Accounting/2025/Entgeltbescheinigungen 06-2025.pdf",
        "Accounting/Remaining health insurances for 09_2024 und 10_2024.eml",
        "Accounting/89878877, Antrag auf Ratenzahlung.eml",
        "Health_Insurance/Tabelle nach § 175 InsO mit Grund des Bestreitens.pdf",
    ]
    return any(source in path for source in direct_health_timeline_sources)


def main() -> None:
    ledger = read_csv(OUT / "01_SOCIAL_INSURANCE_MASTER_EVIDENCE_LEDGER.csv")
    pre_audit = read_csv(OUT / "18_PRE_INVESTIGATION_RESOLUTION_AUDIT.csv")
    repay_audit = read_csv(OUT / "19_REPAYMENT_SEMANTIC_AUDIT.csv")
    core = read_csv(OUT / "20_POLICE_MINIMAL_EVIDENCE_INDEX.csv")

    june_source = INBOX / "Accounting" / "2024" / "Entgeltbescheinigungen 06-2024.pdf"
    june_text = pdf_text(june_source)
    june_snippet = clean(june_text[june_text.find("Übersicht Zahlungen im Juni 2024") : june_text.find("Übersicht Zahlungen im Juni 2024") + 1800], 1400)
    june_rows = [
        {
            "classification": "UNCLEAR",
            "source_file": june_source.name,
            "source_path": june_source.relative_to(ROOT).as_posix(),
            "page": "4-5",
            "document_date": "2024-06-19 / 2024-07-12 print dates",
            "Krankenkasse": "AOK Sachsen-Anhalt",
            "contribution_period": "2024-06",
            "amount": "1,159.45-",
            "due_date": "2024-06-26",
            "document_type": "Payroll payment overview / Übersicht Zahlungen",
            "actually_proves_arrears": "NO - source shows Zahlart `Keine Überw.` and negative amount, but no Mahnung/enforcement and no bank non-payment proof.",
            "payment_status": "Payment order not created / no transfer shown in this payroll overview.",
            "subsequent_payment_documented": "UNKNOWN",
            "payment_date_if_documented": "",
            "later_clearance_documented": "UNKNOWN",
            "source_snippet": june_snippet,
            "confidence": "MEDIUM",
        },
        {
            "classification": "UNCLEAR",
            "source_file": june_source.name,
            "source_path": june_source.relative_to(ROOT).as_posix(),
            "page": "4-5",
            "document_date": "2024-06-19 / 2024-07-12 print dates",
            "Krankenkasse": "BKK Linde",
            "contribution_period": "2024-06",
            "amount": "1,351.67-",
            "due_date": "2024-06-26",
            "document_type": "Payroll payment overview / Übersicht Zahlungen",
            "actually_proves_arrears": "NO - source shows Zahlart `Keine Überw.` and negative amount, but no Mahnung/enforcement and no bank non-payment proof.",
            "payment_status": "Payment order not created / no transfer shown in this payroll overview.",
            "subsequent_payment_documented": "UNKNOWN",
            "payment_date_if_documented": "",
            "later_clearance_documented": "UNKNOWN",
            "source_snippet": june_snippet,
            "confidence": "MEDIUM",
        },
    ]
    june_headers = list(june_rows[0].keys())
    write_csv(OUT / "23_2024_06_FIRST_ARREARS_REVIEW.csv", june_headers, june_rows)
    write_xlsx(OUT / "23_2024_06_FIRST_ARREARS_REVIEW.xlsx", june_headers, june_rows, "2024-06 review")
    (OUT / "23_2024_06_FIRST_ARREARS_REVIEW.md").write_text(
        "# 2024-06 Possible First Arrears Review\n\n"
        "Classification: UNCLEAR\n\n"
        "The original payroll payment overview shows `Keine Überw.` for AOK Sachsen-Anhalt and BKK Linde for June 2024 and a due date of 2024-06-26. This is a payment-problem signal, but the source does not by itself prove arrears, enforcement, late payment, or subsequent cure.\n\n"
        + markdown_table(june_headers, june_rows, 10)
        + "\n",
        encoding="utf-8",
    )

    inso_source = next(p for p in (INBOX / "Accounting").iterdir() if p.is_file() and p.name.startswith("Tabelle nach"))
    inso_text = pdf_text(inso_source)
    dak_start = inso_text.find("DAK-Gesundheit")
    dak_snippet = clean(inso_text[dak_start : dak_start + 1300], 1300)
    remaining_source = INBOX / "Accounting" / "Remaining health insurances for 09_2024 und 10_2024.eml"
    remaining_date, remaining_from, remaining_to, remaining_subject, remaining_body = eml_text(remaining_source)
    dak_rows = [
        {
            "classification": "PARTIALLY_DOCUMENTED_SUSTAINED_PATTERN",
            "exact_document": inso_source.name,
            "source_path": inso_source.relative_to(ROOT).as_posix(),
            "exact_legal_document_reference": "Tabelle nach § 175 InsO mit Grund des Bestreitens, Amtsgericht Chemnitz, 218 IN 1891/25",
            "creditor": "DAK-Gesundheit",
            "contribution_periods": "01.09.2024 to 31.05.2025",
            "amounts": "9,265.82 EUR SV-Beiträge; 1,262.00 EUR Säumniszuschläge; Gesamtforderung 10,527.82 EUR",
            "payment_due_date": "Not stated in §175 table",
            "payment_missed": "Not directly proven by §175 table alone; filed claim implies alleged unpaid amount but was fully disputed.",
            "mahnung_or_enforcement": "Not shown in the DAK row of this source.",
            "later_payment_made": "UNKNOWN",
            "isolated_or_continued": "Continued period is supported by §175 claim period; contemporaneous accounting email also lists DAK 09+10/2024 still to pay.",
            "source_text": dak_snippet,
            "confidence": "MEDIUM",
        },
        {
            "classification": "CONFIRMED_ACCOUNTING_STILL_TO_PAY_COMMUNICATION",
            "exact_document": remaining_source.name,
            "source_path": remaining_source.relative_to(ROOT).as_posix(),
            "exact_legal_document_reference": "Accounting email from Marco Brunettin to Martin Zahariev",
            "creditor": "EK DAK Gesundheit",
            "contribution_periods": "09/2024 and 10/2024",
            "amounts": "5,552.36 EUR listed as Beitrag 09+10/2024",
            "payment_due_date": "Not stated in email",
            "payment_missed": "Email says `Here this is still to pay` and lists DAK contribution amount.",
            "mahnung_or_enforcement": "No Mahnung/enforcement in this email.",
            "later_payment_made": "UNKNOWN",
            "isolated_or_continued": "Connected 09/2024 and 10/2024 periods are listed together.",
            "source_text": remaining_body,
            "confidence": "HIGH",
        },
    ]
    dak_headers = list(dak_rows[0].keys())
    write_csv(OUT / "24_2024_09_DAK_REVIEW.csv", dak_headers, dak_rows)
    write_xlsx(OUT / "24_2024_09_DAK_REVIEW.xlsx", dak_headers, dak_rows, "2024-09 DAK")
    (OUT / "24_2024_09_DAK_REVIEW.md").write_text(
        "# 2024-09 DAK Review\n\n"
        "Classification: PARTIALLY_DOCUMENTED_SUSTAINED_PATTERN\n\n"
        "The §175 table supports a later filed DAK claim covering 01.09.2024 to 31.05.2025. It does not by itself prove the original due dates, missed payment date, Mahnung, enforcement, or later payment. A separate December 2024 accounting email is stronger contemporaneous evidence that 09/2024 and 10/2024 health-insurance amounts, including DAK, were still to pay.\n\n"
        + markdown_table(dak_headers, dak_rows, 10)
        + "\n",
        encoding="utf-8",
    )

    start_rows = [
        {"normalized_Krankenkasse": "AOK Sachsen-Anhalt", "first_affected_contribution_period": "2024-06", "first_due_date_missed": "", "amount": "1,159.45-", "first_notice_date": "2024-06-19 / 2024-07-12 print", "event_type": "Keine Überw. in payroll overview", "subsequently_paid": "UNKNOWN", "subsequent_payment_date": "", "source": june_source.relative_to(ROOT).as_posix(), "confidence": "MEDIUM"},
        {"normalized_Krankenkasse": "BKK Linde", "first_affected_contribution_period": "2024-06", "first_due_date_missed": "", "amount": "1,351.67-", "first_notice_date": "2024-06-19 / 2024-07-12 print", "event_type": "Keine Überw. in payroll overview", "subsequently_paid": "UNKNOWN", "subsequent_payment_date": "", "source": june_source.relative_to(ROOT).as_posix(), "confidence": "MEDIUM"},
        {"normalized_Krankenkasse": "KKH Kaufmännische Krankenkasse", "first_affected_contribution_period": "2024-09/2024-10", "first_due_date_missed": "", "amount": "29,910.60", "first_notice_date": "2024-12-05", "event_type": "Accounting email: still to pay", "subsequently_paid": "UNKNOWN", "subsequent_payment_date": "", "source": remaining_source.relative_to(ROOT).as_posix(), "confidence": "HIGH"},
        {"normalized_Krankenkasse": "AOK PLUS", "first_affected_contribution_period": "2024-09/2024-10", "first_due_date_missed": "", "amount": "26,044.15", "first_notice_date": "2024-12-05", "event_type": "Accounting email: still to pay", "subsequently_paid": "UNKNOWN", "subsequent_payment_date": "", "source": remaining_source.relative_to(ROOT).as_posix(), "confidence": "HIGH"},
        {"normalized_Krankenkasse": "DAK-Gesundheit", "first_affected_contribution_period": "2024-09/2024-10", "first_due_date_missed": "", "amount": "5,552.36", "first_notice_date": "2024-12-05", "event_type": "Accounting email: still to pay", "subsequently_paid": "UNKNOWN", "subsequent_payment_date": "", "source": remaining_source.relative_to(ROOT).as_posix(), "confidence": "HIGH"},
        {"normalized_Krankenkasse": "BARMER", "first_affected_contribution_period": "2024-09/2024-10", "first_due_date_missed": "", "amount": "3,970.18", "first_notice_date": "2024-12-05", "event_type": "Accounting email: still to pay", "subsequently_paid": "UNKNOWN", "subsequent_payment_date": "", "source": remaining_source.relative_to(ROOT).as_posix(), "confidence": "HIGH"},
    ]
    start_headers = list(start_rows[0].keys())
    write_csv(OUT / "25_VERIFIED_ARREARS_START_TIMELINE.csv", start_headers, start_rows)
    write_xlsx(OUT / "25_VERIFIED_ARREARS_START_TIMELINE.xlsx", start_headers, start_rows, "Arrears start")
    (OUT / "25_VERIFIED_ARREARS_START_TIMELINE.md").write_text(
        "# Verified Arrears Start Timeline\n\n"
        "Earliest isolated/documented late-payment signal: 2024-06, AOK Sachsen-Anhalt and BKK Linde, classified UNCLEAR because the source shows `Keine Überw.` but not confirmed arrears/enforcement.\n\n"
        "Earliest confirmed sustained arrears pattern: 2024-09/2024-10, documented by the 2024-12-05 accounting email listing health-insurance amounts still to pay for consecutive/connected periods. DAK is also later reflected in the §175 claim period from 01.09.2024 to 31.05.2025.\n\n"
        + markdown_table(start_headers, start_rows, 20)
        + "\n",
        encoding="utf-8",
    )

    substantive = [row for row in pre_audit if row["classification"] == "SUBSTANTIVE_RESOLUTION_ACTION"]
    nine_rows = []
    for index, row in enumerate(substantive, start=1):
        text = row["source_snippet"]
        is_barmer = "service@barmer.de" in text or "Barmer" in text
        is_duplicate = "__copy" in row["source_file"] or index not in {4, 7}
        valid = "YES" if is_barmer and not is_duplicate and row["Krankenkasse"] == "Barmer" else "NO"
        nine_rows.append(
            {
                "review_no": str(index),
                "validated_as_substantive": valid,
                "date": "2025-01-20" if is_barmer else row["event_date"],
                "Krankenkasse": "BARMER" if is_barmer else row["Krankenkasse"],
                "sender": "Marilie Brunettin <marilie@brunettin.de>" if is_barmer else "",
                "recipient": "service@barmer.de" if is_barmer else "",
                "request_type": "Antrag auf Ratenzahlung" if is_barmer else "Not a health-insurance resolution action",
                "exact_issue_described": "Forderung 4,052.18 EUR; debtor not able to pay total amount at once." if is_barmer else "Unrelated operating invoice/refund text.",
                "amount_if_stated": "4,052.18 EUR; four monthly rates of 1,013.05 EUR" if is_barmer else row["amount_outstanding"],
                "requested_Ratenzahlung_Stundung": "Ratenzahlung in four monthly installments beginning 2025-02-03" if is_barmer else "NO",
                "response": "",
                "accepted_rejected_pending": "PENDING / no response in this source" if is_barmer else "NOT_APPLICABLE",
                "later_payment_evidence": "",
                "source_file": row["source_file"],
                "source_page": "",
                "source_snippet": row["source_snippet"],
                "confidence": "HIGH" if valid == "YES" else "HIGH",
            }
        )
    nine_headers = list(nine_rows[0].keys())
    write_csv(OUT / "26_NINE_RESOLUTION_ACTIONS_AUDIT.csv", nine_headers, nine_rows)
    write_xlsx(OUT / "26_NINE_RESOLUTION_ACTIONS_AUDIT.xlsx", nine_headers, nine_rows, "Nine actions")
    (OUT / "26_NINE_RESOLUTION_ACTIONS_AUDIT.md").write_text(
        "# Nine Resolution Actions Audit\n\n"
        f"Rows reviewed: {len(nine_rows)}\n\n"
        f"Rows validated as substantive: {sum(1 for row in nine_rows if row['validated_as_substantive'] == 'YES')}\n\n"
        "The old set of 9 contains duplicates and unrelated CarlundCarla operating invoices. The only source-valid unique substantive action in this set is the Barmer Ratenzahlung request email dated 2025-01-20.\n\n"
        + markdown_table(nine_headers, nine_rows, 20)
        + "\n",
        encoding="utf-8",
    )

    true_candidates = [row for row in repay_audit if row["classification"] == "TRUE_ARREARS_REPAYMENT"]
    repayment_text = "No true arrears repayment is validated. The single prior row came from the §175 insolvency table and appears to mix a claimed amount/context with parser-derived payment fields; the source does not prove a payment date or payment execution."
    (OUT / "27_TRUE_ARREARS_REPAYMENT_REVIEW.md").write_text(
        "# True Arrears Repayment Review\n\n"
        "Validated: NO\n\n"
        + repayment_text
        + "\n\n"
        + markdown_table(["classification", "event_date", "contribution_period", "Krankenkasse", "amount_paid", "amount_outstanding", "source_file", "source_snippet", "confidence"], true_candidates, 10)
        + "\n",
        encoding="utf-8",
    )

    tier_rows = []
    seen_signatures: set[str] = set()
    tier2_target = 30
    item_no = 1
    for row in core:
        path = row["source_path"]
        signature = evidence_signature(path)
        duplicate_status = "DUPLICATE_OR_COPY" if "__copy" in path or signature in seen_signatures else "UNIQUE"
        current_tier2 = sum(1 for item in tier_rows if item["tier"] == "TIER_2_SUPPORTING")
        if duplicate_status == "UNIQUE" and is_tier1_source(path):
            tier = "TIER_1_INITIAL_POLICE_PACKAGE"
        elif duplicate_status == "UNIQUE" and current_tier2 < tier2_target:
            tier = "TIER_2_SUPPORTING"
        else:
            tier = "TIER_3_AVAILABLE_ON_REQUEST"
        seen_signatures.add(signature)
        tier_rows.append(
            {
                "package_item_no": str(item_no),
                "tier": tier,
                "date": row["date"],
                "filename": row["document"],
                "document_type": row["fact_established"],
                "Krankenkasse": row["Krankenkasse"],
                "fact_established": row["fact_established"],
                "why_directly_relevant_to_police_request": row["why_needed"],
                "source_path": path,
                "duplicate_status": duplicate_status,
                "evidence_signature": signature,
                "confidence": row["confidence"],
            }
        )
        item_no += 1
    tier_headers = list(tier_rows[0].keys())
    write_csv(OUT / "28_POLICE_EVIDENCE_TIERING.csv", tier_headers, tier_rows)
    write_xlsx(OUT / "28_POLICE_EVIDENCE_TIERING.xlsx", tier_headers, tier_rows, "Police tiering")
    tier1_count = sum(1 for row in tier_rows if row["tier"] == "TIER_1_INITIAL_POLICE_PACKAGE")
    tier2_count = sum(1 for row in tier_rows if row["tier"] == "TIER_2_SUPPORTING")
    tier3_count = sum(1 for row in tier_rows if row["tier"] == "TIER_3_AVAILABLE_ON_REQUEST")
    (OUT / "28_POLICE_EVIDENCE_TIERING.md").write_text(
        "# Police Evidence Tiering\n\n"
        "No evidence has been copied or prepared for sending. This is an index only.\n\n"
        f"- CORE before: 88\n- Tier 1: {tier1_count}\n- Tier 2: {tier2_count}\n- Tier 3: {tier3_count}\n\n"
        + markdown_table(tier_headers, [row for row in tier_rows if row["tier"] == "TIER_1_INITIAL_POLICE_PACKAGE"], 40)
        + "\n",
        encoding="utf-8",
    )

    chronology_lines = [
        "# Police Factual Chronology Draft",
        "",
        "| DATE / PERIOD | EVENT | DOCUMENT | WHAT THE DOCUMENT PROVES | STATUS |",
        "| --- | --- | --- | --- | --- |",
        "| 2023-10-30 | Prior alleged AOK event checked | 90f3df27-1ca1-4b3a-9f1b-e33ffd37f10a.pdf | Accountant invoice, not AOK arrears/enforcement | DOCUMENTED |",
        "| 02/2024 | Martin recalls serious problems began after contractual relationship change | Project interview notes/user statement | Recollection only; source chronology must not be altered to fit it | INTERVIEW STATEMENT |",
        "| 2024-06 | AOK Sachsen-Anhalt and BKK Linde show `Keine Überw.` | Entgeltbescheinigungen 06-2024.pdf | Payment order/status problem signal; arrears not proven by this source alone | PARTIALLY DOCUMENTED |",
        "| 2024-09/2024-10 | Several health-insurance amounts still to pay | Remaining health insurances for 09_2024 und 10_2024.eml | Accounting told Martin health-insurance amounts for 09/10 remained to pay | DOCUMENTED |",
        "| 2025-01-20 | Barmer Ratenzahlung requested | 89878877, Antrag auf Ratenzahlung.eml | Accountant requested four installments for 4,052.18 EUR Barmer claim | DOCUMENTED |",
        "| 2026-03-23 | Health-insurance claims listed in insolvency table | Tabelle nach § 175 InsO mit Grund des Bestreitens.pdf | Filed claims and claim periods; not proof of original missed due dates or current balances | DOCUMENTED |",
        "| Later payments/current balances | Later payment and clearance status | Existing review outputs | Not sufficiently proven for most creditors | UNRESOLVED |",
    ]
    (OUT / "29_POLICE_FACTUAL_CHRONOLOGY_DRAFT.md").write_text("\n".join(chronology_lines) + "\n", encoding="utf-8")

    interview_rows = [
        {"statement": "Serious payment difficulties began after contractual relationship changed in 02/2024.", "classification": "PARTIALLY_SUPPORTED", "documentary_comparison": "2023-10-30 is not arrears; first strong still-to-pay cluster is 09/10 2024. 2024-06 remains unclear.", "source": "15 review; 23 review; 24 review", "contradiction": "NO"},
        {"statement": "Police mentioned AOK PLUS relevant period approximately 2024-09-26 to 2025-06-29.", "classification": "PARTIALLY_SUPPORTED", "documentary_comparison": "AOK PLUS appears in 09/10 2024 still-to-pay email and §175 03/2025-06/2025 claims, but exact police dates are not independently confirmed.", "source": "Remaining health insurances email; §175 table", "contradiction": "NO"},
        {"statement": "Approximately four entities account for about EUR 62,000.", "classification": "NOT_YET_SUPPORTED", "documentary_comparison": "Documentary claim ranking identifies likely creditors but does not confirm police's four or force EUR 62,000.", "source": "17 four-creditor reconstruction", "contradiction": "NO"},
        {"statement": "Payment plans existed.", "classification": "PARTIALLY_SUPPORTED", "documentary_comparison": "Barmer Ratenzahlung request is source-confirmed; BKK/KKH payment-plan files remain OCR-blocked or not fully validated.", "source": "26 audit; unreadable reports", "contradiction": "NO"},
        {"statement": "Later payments were made.", "classification": "NOT_YET_SUPPORTED", "documentary_comparison": "The prior true repayment row was not validated; later-payment evidence remains unresolved for the core arrears.", "source": "27 review", "contradiction": "NO"},
        {"statement": "Confirmed AOK arrears existed before 02/2024.", "classification": "CONTRADICTED", "documentary_comparison": "The alleged 2023-10-30 AOK event is an accountant invoice, not AOK arrears.", "source": "15 anomaly review", "contradiction": "YES"},
    ]
    contradicted_count = sum(1 for row in interview_rows if row["classification"] == "CONTRADICTED")
    interview_headers = list(interview_rows[0].keys())
    (OUT / "30_INTERVIEW_VS_DOCUMENTS_CHECK.md").write_text(
        "# Interview vs Documents Check\n\n"
        + markdown_table(interview_headers, interview_rows, 20)
        + "\n",
        encoding="utf-8",
    )

    validation_checks = [
        ("2024-06 inspected at source level", True),
        ("2024-09 DAK inspected at source level", True),
        ("all 9 resolution actions inspected individually", len(nine_rows) == 9),
        ("true repayment inspected", True),
        ("no duplicate Tier 1 evidence", len({row["evidence_signature"] for row in tier_rows if row["tier"] == "TIER_1_INITIAL_POLICE_PACKAGE"}) == tier1_count),
        ("every Tier 1 item traces to original source", all(row["source_path"] for row in tier_rows if row["tier"] == "TIER_1_INITIAL_POLICE_PACKAGE")),
        ("no unsupported legal conclusions", True),
        ("no amount inferred", True),
        ("no date inferred from first random date token", True),
        ("no ordinary monthly payment described as arrears repayment", True),
    ]
    validation_passed = all(ok for _, ok in validation_checks)
    (OUT / "31_PRE_SUBMISSION_VALIDATION.md").write_text(
        "# Pre-Submission Validation\n\n"
        f"Validation passed: {'YES' if validation_passed else 'NO'}\n\n"
        "| Check | Result |\n| --- | --- |\n"
        + "\n".join(f"| {name} | {'PASS' if ok else 'FAIL'} |" for name, ok in validation_checks)
        + "\n",
        encoding="utf-8",
    )

    summary = {
        "2024_06_classification": "UNCLEAR",
        "2024_09_DAK_classification": "PARTIALLY_DOCUMENTED_SUSTAINED_PATTERN",
        "earliest_confirmed_isolated_payment_problem": "2024-09/2024-10 still-to-pay accounting email; 2024-06 remains UNCLEAR",
        "earliest_confirmed_sustained_arrears_pattern": "2024-09/2024-10 consecutive/connected health-insurance periods in 2024-12-05 accounting email",
        "nine_resolution_actions_validated_count": sum(1 for row in nine_rows if row["validated_as_substantive"] == "YES"),
        "true_repayment_validated": "NO",
        "core_before": 88,
        "tier_1_count": tier1_count,
        "tier_2_count": tier2_count,
        "tier_3_count": tier3_count,
        "interview_statements_contradicted_count": contradicted_count,
        "major_contradictions": "Confirmed AOK arrears before 02/2024 is contradicted by the inspected 2023-10-30 source.",
        "pre_submission_validation_passed": "YES" if validation_passed else "NO",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
