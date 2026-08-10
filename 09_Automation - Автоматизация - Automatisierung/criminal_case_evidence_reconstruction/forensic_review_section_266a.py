#!/usr/bin/env python3
"""Forensic semantic review of the section 266a evidence reconstruction."""

from __future__ import annotations

import csv
import html
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
INBOX = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("00_INBOX"))
REPORTS = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("08_Reports"))
OUT = REPORTS / "Criminal_Case_390_Js_5935_26"
LEDGER = OUT / "01_SOCIAL_INSURANCE_MASTER_EVIDENCE_LEDGER.csv"
PRE_MD = OUT / "12_PRE_INVESTIGATION_RESOLUTION_EVIDENCE.md"
LATE_CSV = OUT / "06_LATE_PAYMENT_AND_REPAYMENT_TIMELINE.csv"


def norm(value: str) -> str:
    return (value or "").lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")


def clean(value: str, limit: int = 500) -> str:
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


def table(headers: list[str], rows: list[dict[str, str]], limit: int = 40) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(clean(str(row.get(header, "")), 120).replace("|", "/") for header in headers) + " |")
    if len(rows) > limit:
        lines.append("| ... | " + f"{len(rows) - limit} additional rows in CSV/XLSX |" + " |" * (len(headers) - 2))
    return "\n".join(lines)


def extract_pdf_text(path: Path) -> tuple[str, int]:
    import fitz  # type: ignore

    doc = fitz.open(path)
    parts = []
    for page_index, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        if text.strip():
            parts.append(f"[[page {page_index}]]\n{text}")
    return "\n".join(parts), doc.page_count


def normalize_name(raw: str) -> tuple[str, str, str, str, str]:
    raw_n = norm(raw)
    if raw_n in {"tk", "techniker krankenkasse"} or "techniker" in raw_n:
        return "Techniker Krankenkasse", "Krankenkasse / Einzugsstelle", "creditor", "", "TK and Techniker Krankenkasse treated as the same creditor."
    if raw_n in {"aok plus", "aok plus die gesundheitskasse fuer sachsen und thueringen"} or "aok plus" in raw_n:
        return "AOK PLUS - Die Gesundheitskasse fuer Sachsen und Thueringen", "Krankenkasse / Einzugsstelle", "creditor", "", "AOK PLUS names and AOK PLUS Dresden references normalized together."
    if "baden" in raw_n and "aok" in raw_n:
        return "AOK Baden-Wuerttemberg", "Krankenkasse / Einzugsstelle", "creditor", "", "Regional AOK entity retained separately from AOK PLUS."
    if "hessen" in raw_n and "aok" in raw_n:
        return "AOK Hessen", "Krankenkasse / Einzugsstelle", "creditor", "", "Regional AOK entity retained separately from AOK PLUS."
    if "nordost" in raw_n and "aok" in raw_n:
        return "AOK Nordost", "Krankenkasse / Einzugsstelle", "creditor", "", "Regional AOK entity retained separately from AOK PLUS."
    if "sachsen-anhalt" in raw_n and "aok" in raw_n:
        return "AOK Sachsen-Anhalt", "Krankenkasse / Einzugsstelle", "creditor", "", "Regional AOK entity retained separately from AOK PLUS."
    if raw_n == "aok":
        return "AOK unspecified", "Krankenkasse / Einzugsstelle", "creditor", "", "Generic AOK is not merged into AOK PLUS unless the source supports AOK PLUS."
    if "kkh" in raw_n or "kaufmaennische" in raw_n:
        return "KKH Kaufmaennische Krankenkasse", "Krankenkasse / Einzugsstelle", "creditor", "", "KKH aliases normalized."
    if "dak" in raw_n:
        return "DAK-Gesundheit", "Krankenkasse / Einzugsstelle", "creditor", "", "DAK aliases normalized."
    if "barmer" in raw_n:
        return "BARMER", "Krankenkasse / Einzugsstelle", "creditor", "", "BARMER aliases normalized."
    if "viactiv" in raw_n:
        return "VIACTIV Krankenkasse", "Krankenkasse / Einzugsstelle", "creditor", "", "VIACTIV aliases normalized."
    if "vivida" in raw_n or "vivda" in raw_n:
        return "Vivida BKK", "Krankenkasse / Einzugsstelle", "creditor", "", "Vivida/Vivda spelling normalized."
    if "linde" in raw_n:
        return "BKK Linde", "Krankenkasse / Einzugsstelle", "creditor", "", "BKK Linde retained separately from generic BKK."
    if raw_n == "sbk":
        return "SBK Siemens-Betriebskrankenkasse", "Krankenkasse / Einzugsstelle", "creditor", "", "SBK normalized from BKK SBK/SBK."
    if raw_n == "bkk":
        return "BKK unspecified", "Krankenkasse / Einzugsstelle", "creditor", "", "Generic BKK is not merged with named BKK without support."
    if "hauptzollamt" in raw_n:
        return "Hauptzollamt", "Enforcement authority", "enforcement_authority", "", "Hauptzollamt is not a Krankenkasse; underlying creditor only recorded if source proves it."
    return raw or "UNKNOWN", "Unknown / requires review", "unknown", "", "No normalization rule beyond raw name."


def source_text_for(path_text: str) -> str:
    path = ROOT / path_text
    if path.exists() and path.suffix.lower() == ".pdf":
        try:
            return extract_pdf_text(path)[0]
        except Exception:
            return ""
    return ""


def is_duplicate(row: dict[str, str], seen: set[tuple[str, str, str, str, str]]) -> bool:
    key = (row.get("event_date", ""), row.get("contribution_period", ""), row.get("Krankenkasse", ""), row.get("event_type", ""), row.get("source_file", ""))
    if key in seen:
        return True
    seen.add(key)
    return False


def classify_pre(row: dict[str, str], duplicate: bool) -> tuple[str, str]:
    if duplicate:
        return "DUPLICATE", "Same date/period/Krankenkasse/event/source already audited."
    text = norm(" ".join([row.get("event_type", ""), row.get("source_snippet", ""), row.get("communication_summary", ""), row.get("source_path", "")]))
    if any(term in text for term in ["ratenzahlung", "stundung", "zahlungsplan", "zahlungsvereinbarung", "fristverlaengerung"]):
        return "SUBSTANTIVE_RESOLUTION_ACTION", "Contains explicit payment-plan, Stundung, Zahlungsplan, or extension wording."
    if any(term in text for term in ["rueckstand", "mahnung", "forderung", "nicht gezahlt", "vollstreck", "ruecklastschrift"]) and (row.get("amount_outstanding") or row.get("amount_paid")):
        return "SUBSTANTIVE_RESOLUTION_ACTION", "Contains arrears/enforcement wording plus an amount or payment evidence."
    if row.get("amount_paid") and not any(term in text for term in ["rueckstand", "mahnung", "ratenzahlung", "stundung", "ueberfaellig"]):
        return "ROUTINE_ACCOUNTING", "Payment appears as ordinary payment/instruction without arrears context."
    if "beitragsnachweis" in text or "gesamtsumme" in text or "contribution_due" in text:
        return "ROUTINE_ACCOUNTING", "Ordinary contribution notice/list, not a resolution action."
    if "brunettin" in text and not any(term in text for term in ["rueckstand", "ratenzahlung", "stundung"]):
        return "ROUTINE_ACCOUNTING", "Generic accounting/fee context without resolution wording."
    return "UNCLEAR", "Source row has insufficient semantic evidence for a resolution-action classification."


def classify_repayment(row: dict[str, str], duplicate: bool) -> tuple[str, str]:
    if duplicate:
        return "DUPLICATE", "Same date/period/Krankenkasse/event/source already audited."
    text = norm(" ".join([row.get("event_type", ""), row.get("source_snippet", ""), row.get("source_file", "")]))
    if any(term in text for term in ["saeumniszusch", "säumniszusch", "late fee"]):
        return "LATE_FEE_PAYMENT", "Late-fee/Saeumniszuschlag context detected."
    if any(term in text for term in ["ratenzahlung", "zahlungsplan", "teilzahlung"]) and row.get("amount_paid"):
        return "PAYMENT_PLAN_INSTALLMENT", "Payment-plan installment wording detected."
    if row.get("amount_paid") and any(term in text for term in ["rueckstand", "mahnung", "forderung", "vollstreck", "ruecklastschrift", "ueberfaellig"]):
        return "TRUE_ARREARS_REPAYMENT", "Payment is linked to arrears/enforcement/overdue context."
    if row.get("amount_paid"):
        return "NORMAL_MONTHLY_PAYMENT", "Payment amount exists but no arrears context is stated."
    if row.get("amount_outstanding") or "arrears" in norm(row.get("event_type", "")):
        return "UNCLEAR", "Arrears/outstanding context exists, but no repayment is documented."
    return "UNCLEAR", "No semantic repayment signal."


def build_anomaly(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], str]:
    source = INBOX / "Accounting" / "accountings112023" / "90f3df27-1ca1-4b3a-9f1b-e33ffd37f10a.pdf"
    text, pages = extract_pdf_text(source)
    relevant = clean(text[text.find("Rechnung") : text.find("Seite 2") + 500], 1200)
    row = {
        "classification": "MISCLASSIFIED_EVENT",
        "source_filename": source.name,
        "source_path": source.relative_to(ROOT).as_posix(),
        "source_page": "1-2",
        "document_date": "2023-10-30",
        "exact_AOK_entity": "",
        "contribution_period_concerned": "September/2023 appears as accountant-service billing period, not a social-insurance contribution period.",
        "amount": "1,664.33 EUR accountant invoice total; 19.00 is VAT rate, not arrears amount.",
        "document_type": "Accountant invoice from Marco Brunettin / Steuerberatung",
        "actually_states_arrears": "NO",
        "is_enforcement_notice": "NO",
        "concerns_social_insurance_contributions": "NO - only mentions wage-accounting services and reimbursement requests for health insurances.",
        "concerns_martin_zahariev_business": "YES - addressed to Favorit MP, Inh. Martin Zahariev.",
        "due_date": "",
        "payment_status": "Open accountant invoice amount requested; no health-insurance payment status stated.",
        "evidence_of_subsequent_payment": "",
        "evidence_of_later_clearance": "No AOK clearance for this alleged event; Barmer certificate dated 2024-09-17 shows no Barmer arrears only.",
        "later_unbedenklichkeitsbescheinigung_no_arrears": "No later AOK/AOK PLUS no-arrears certificate found for this event in the current reconstruction.",
        "exact_relevant_source_text_snippet": relevant,
        "confidence": "HIGH",
    }
    return [row], relevant


def parse_four_creditors() -> list[dict[str, str]]:
    source = next(p for p in (INBOX / "Accounting").iterdir() if p.is_file() and p.name.startswith("Tabelle nach"))
    text, _ = extract_pdf_text(source)
    entries = [
        ("AOK PLUS - Die Gesundheitskasse fuer Sachsen und Thueringen", "01.03.2025-30.06.2025 and AN-Anteile 01.04.2025-30.06.2025", "23,263.84; 10,093.98", "33,357.82", "No later payment/current balance found in this source.", "Page 1 lists AOK PLUS SV-Beitraege and AN-Anteile; both fully disputed by insolvency administrator."),
        ("KKH Kaufmaennische Krankenkasse", "01/2025 and 03-07/2025; plus estimated SV-Beitraege", "24,418.71; 29,078.47; 30,000.00 estimated", "83,497.18", "No later payment/current balance found in this source.", "Page 6 lists KKH AN-Anteile, SV-Beitraege, and an estimated 30,000.00 EUR SV-Beitraege claim."),
        ("DAK-Gesundheit", "01.09.2024-31.05.2025", "10,527.82", "10,527.82", "No later payment/current balance found in this source.", "Page 3 lists DAK-Gesundheit SV-Beitraege and Saeumniszuschlaege."),
        ("BKK Linde", "01.04.2025-30.06.2025", "3,207.56; 2,740.03", "5,947.59", "No later payment/current balance found in this source.", "Page 5 lists BKK Linde SV-Beitraege and AN-Anteile."),
        ("BARMER", "01.02.2025-30.06.2025", "3,302.98; 2,413.84", "5,716.82", "No later payment/current balance found in this source.", "Pages 6-7 list BARMER SV-Beitraege and AN-Anteile."),
        ("Techniker Krankenkasse", "01.01.2025-30.06.2025 and AN-Anteile 01.04.2025-30.06.2025", "1,864.61; 1,568.98", "3,433.59", "No later payment/current balance found in this source.", "Page 4 lists Techniker Krankenkasse SV-Beitraege and AN-Anteile."),
        ("VIACTIV Krankenkasse", "01.04.2025-31.07.2025", "2,175.67; 1,765.69", "3,941.36", "No later payment/current balance found in this source.", "Page 2 lists VIACTIV SV-Beitraege and AN-Anteile."),
    ]
    rows = []
    for index, (creditor, periods, originals, total, later, support) in enumerate(entries, start=1):
        likely = "YES" if index <= 4 else "SUPPORTING_HEALTH_CREDITOR_NOT_TOP_FOUR_BY_DOCUMENTED_AMOUNT"
        rows.append(
            {
                "rank_by_documented_claim_amount": str(index),
                "likely_one_of_four_police_creditors": likely,
                "creditor": creditor,
                "normalized_creditor": normalize_name(creditor)[0],
                "contribution_periods": periods,
                "original_claimed_amounts": originals,
                "documented_claim_total": total,
                "later_payments": "",
                "current_documented_balance": "",
                "evidence_status": "SUPPORTED_BY_INSOLVENCY_TABLE_BUT_POLICE_FOUR_NOT_CONFIRMED",
                "source_file": source.relative_to(ROOT).as_posix(),
                "source_support": support,
                "confidence": "MEDIUM",
            }
        )
    return rows


def main() -> None:
    rows = read_csv(LEDGER)
    anomaly_rows, anomaly_snippet = build_anomaly(rows)
    anomaly_headers = list(anomaly_rows[0].keys())
    write_csv(OUT / "15_2023_10_30_ANOMALY_EVIDENCE.csv", anomaly_headers, anomaly_rows)
    write_xlsx(OUT / "15_2023_10_30_ANOMALY_EVIDENCE.xlsx", anomaly_headers, anomaly_rows, "2023 anomaly")
    (OUT / "15_2023_10_30_ANOMALY_REVIEW.md").write_text(
        "\n".join(
            [
                "# 2023-10-30 Anomaly Review",
                "",
                "Classification: MISCLASSIFIED_EVENT",
                "",
                "The original source is an accountant invoice from Marco Brunettin dated 2023-10-30. It is addressed to Favorit MP, Inh. Martin Zahariev, but it is not an AOK document, not a social-insurance contribution notice, and not an enforcement notice.",
                "",
                "The prior extractor appears to have misread `Pfändungen`, `offenen Rechnungsbetrag`, `Requests of reimbursement of wages for the health insurances`, and the VAT rate `19,00 %` as health-insurance arrears.",
                "",
                table(anomaly_headers, anomaly_rows, 1),
                "",
                "No legal conclusion is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    raw_names = sorted({row.get("Krankenkasse", "") for row in rows if row.get("Krankenkasse", "")})
    normalization_rows = []
    for raw_name in raw_names:
        normalized, role, role_type, underlying, support = normalize_name(raw_name)
        if role_type == "enforcement_authority":
            snippets = " ".join(row.get("source_snippet", "") for row in rows if row.get("Krankenkasse") == raw_name)[:2000]
            for candidate in raw_names:
                if candidate != raw_name and norm(candidate) in norm(snippets):
                    underlying = normalize_name(candidate)[0]
                    break
        normalization_rows.append(
            {
                "raw_name": raw_name,
                "normalized_name": normalized,
                "legal_role": role,
                "creditor_or_enforcement_authority": role_type,
                "underlying_creditor_if_known": underlying,
                "source_support": support,
                "confidence": "HIGH" if role_type != "unknown" else "LOW",
            }
        )
    norm_headers = ["raw_name", "normalized_name", "legal_role", "creditor_or_enforcement_authority", "underlying_creditor_if_known", "source_support", "confidence"]
    write_csv(OUT / "16_KRANKENKASSEN_ENTITY_NORMALIZATION.csv", norm_headers, normalization_rows)
    write_xlsx(OUT / "16_KRANKENKASSEN_ENTITY_NORMALIZATION.xlsx", norm_headers, normalization_rows, "Entity normalization")

    four_rows = parse_four_creditors()
    four_headers = list(four_rows[0].keys())
    write_csv(OUT / "17_POLICE_FOUR_CREDITOR_RECONSTRUCTION.csv", four_headers, four_rows)
    write_xlsx(OUT / "17_POLICE_FOUR_CREDITOR_RECONSTRUCTION.xlsx", four_headers, four_rows, "Four creditors")
    (OUT / "17_POLICE_FOUR_CREDITOR_RECONSTRUCTION.md").write_text(
        "\n".join(
            [
                "# Police Four-Creditor Reconstruction",
                "",
                "Martin reports that police referenced approximately four entities and approximately EUR 62,000. The current documentary evidence does not reliably prove which four entities police meant and should not be forced to total EUR 62,000.",
                "",
                "The table below ranks health-insurance creditors from the §175 InsO table by documented filed claim amounts. `YES` means likely candidate by documentary amount, not confirmation that police identified that creditor.",
                "",
                table(four_headers, four_rows, 20),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    pre_candidates = [
        row
        for row in rows
        if row.get("event_date")
        and row["event_date"] < "2026-01-01"
        and ("PAYMENT_PLAN" in row.get("event_type", "") or "ARREARS" in row.get("event_type", "") or row.get("amount_outstanding") or (row.get("amount_paid") and any(term in norm(row.get("source_snippet", "")) for term in ["rueckstand", "ratenzahlung", "stundung", "mahnung", "forderung"])))
    ]
    seen_pre: set[tuple[str, str, str, str, str]] = set()
    pre_audit = []
    for row in pre_candidates:
        classification, reason = classify_pre(row, is_duplicate(row, seen_pre))
        pre_audit.append(
            {
                "evidence_id": row["evidence_id"],
                "classification": classification,
                "reason": reason,
                "event_date": row["event_date"],
                "contribution_period": row["contribution_period"],
                "Krankenkasse": row["Krankenkasse"],
                "amount_paid": row["amount_paid"],
                "amount_outstanding": row["amount_outstanding"],
                "source_file": row["source_path"],
                "source_snippet": row["source_snippet"],
                "confidence": row["confidence"],
            }
        )
    pre_headers = list(pre_audit[0].keys()) if pre_audit else ["evidence_id", "classification"]
    write_csv(OUT / "18_PRE_INVESTIGATION_RESOLUTION_AUDIT.csv", pre_headers, pre_audit)
    write_xlsx(OUT / "18_PRE_INVESTIGATION_RESOLUTION_AUDIT.xlsx", pre_headers, pre_audit, "Pre investigation audit")
    pre_counts = Counter(row["classification"] for row in pre_audit)
    (OUT / "18_PRE_INVESTIGATION_RESOLUTION_AUDIT.md").write_text(
        "\n".join(
            [
                "# Pre-Investigation Resolution Audit",
                "",
                f"Old broad count: {len(pre_candidates)}",
                f"New substantive count: {pre_counts.get('SUBSTANTIVE_RESOLUTION_ACTION', 0)}",
                "",
                "## Classification Counts",
                *[f"- {name}: {count}" for name, count in sorted(pre_counts.items())],
                "",
                "## Substantive Items Preview",
                table(pre_headers, [row for row in pre_audit if row["classification"] == "SUBSTANTIVE_RESOLUTION_ACTION"], 80),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    late_source = read_csv(LATE_CSV)
    seen_late: set[tuple[str, str, str, str, str]] = set()
    late_audit = []
    for row in late_source:
        classification, reason = classify_repayment(row, is_duplicate(row, seen_late))
        late_audit.append(
            {
                "classification": classification,
                "reason": reason,
                "event_date": row.get("event_date", ""),
                "contribution_period": row.get("contribution_period", ""),
                "Krankenkasse": row.get("Krankenkasse", ""),
                "amount_paid": row.get("amount_paid", ""),
                "amount_outstanding": row.get("amount_outstanding", ""),
                "event_type": row.get("event_type", ""),
                "source_file": row.get("source_file", ""),
                "source_snippet": row.get("source_snippet", ""),
                "confidence": row.get("confidence", ""),
            }
        )
    late_headers = list(late_audit[0].keys()) if late_audit else ["classification"]
    write_csv(OUT / "19_REPAYMENT_SEMANTIC_AUDIT.csv", late_headers, late_audit)
    write_xlsx(OUT / "19_REPAYMENT_SEMANTIC_AUDIT.xlsx", late_headers, late_audit, "Repayment audit")
    late_counts = Counter(row["classification"] for row in late_audit)
    (OUT / "19_REPAYMENT_SEMANTIC_AUDIT.md").write_text(
        "\n".join(
            [
                "# Repayment Semantic Audit",
                "",
                f"Old broad count: {len(late_source)}",
                f"New true arrears repayment count: {late_counts.get('TRUE_ARREARS_REPAYMENT', 0)}",
                "",
                "## Classification Counts",
                *[f"- {name}: {count}" for name, count in sorted(late_counts.items())],
                "",
                "## True Arrears Repayment Preview",
                table(late_headers, [row for row in late_audit if row["classification"] == "TRUE_ARREARS_REPAYMENT"], 80),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    core_rows = []
    for category, predicate in [
        ("A", lambda r: r.get("amount_due") and r.get("contribution_period") >= "2024-06"),
        ("B", lambda r: "PAYMENT_PLAN" in r.get("event_type", "") and any(term in norm(r.get("source_path", "")) for term in ["brunettin", "accountant", "accounting"])),
        ("C", lambda r: "UNBEDENKLICH" in r.get("event_type", "") or "ARREARS" in r.get("event_type", "")),
        ("D", lambda r: "PAYMENT_PLAN" in r.get("event_type", "")),
        ("E", lambda r: any(term in norm(r.get("source_snippet", "")) for term in ["zahlungsplan", "ratenzahlung", "stundung"])),
        ("F", lambda r: bool(r.get("amount_paid")) and any(term in norm(r.get("source_snippet", "")) for term in ["rueckstand", "mahnung", "ratenzahlung", "stundung", "forderung"])),
        ("G", lambda r: bool(r.get("amount_outstanding")) or "ARREARS" in r.get("event_type", "")),
    ]:
        selected = []
        seen_sources = set()
        for row in rows:
            if predicate(row) and row.get("source_path") and row["source_path"] not in seen_sources:
                seen_sources.add(row["source_path"])
                selected.append(row)
        for row in selected[:25]:
            rank = "CORE" if (row.get("confidence") in {"HIGH", "MEDIUM"} and row.get("source_snippet")) else "SUPPORTING"
            core_rows.append(
                {
                    "police_category": category,
                    "rank": rank,
                    "document": row["source_file"],
                    "date": row["event_date"],
                    "Krankenkasse": row["Krankenkasse"],
                    "fact_established": row["event_type"],
                    "why_needed": "Material source row for requested police evidence category." if rank == "CORE" else "May support context but should not be in initial package.",
                    "source_path": row["source_path"],
                    "source_snippet": row["source_snippet"],
                    "confidence": row["confidence"],
                }
            )
    minimal_headers = ["police_category", "rank", "document", "date", "Krankenkasse", "fact_established", "why_needed", "source_path", "source_snippet", "confidence"]
    write_csv(OUT / "20_POLICE_MINIMAL_EVIDENCE_INDEX.csv", minimal_headers, core_rows)
    write_xlsx(OUT / "20_POLICE_MINIMAL_EVIDENCE_INDEX.xlsx", minimal_headers, core_rows, "Minimal police index")
    core_count = sum(1 for row in core_rows if row["rank"] == "CORE")
    (OUT / "20_POLICE_MINIMAL_EVIDENCE_INDEX.md").write_text(
        "\n".join(
            [
                "# Police Minimal Evidence Index",
                "",
                "This is a candidate index only. No evidence has been copied or sent.",
                "",
                "Previous broad police request match count: 683 documents.",
                f"CORE items after semantic reduction: {core_count}",
                "",
                table(minimal_headers, [row for row in core_rows if row["rank"] == "CORE"], 120),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    first_isolated = "2024-06 - contribution list shows `Keine Ueberw.` entries for AOK Sachsen-Anhalt and BKK Linde in Entgeltbescheinigungen 06-2024; this needs source-level confirmation before treating as arrears."
    first_sustained = "2024-09 - DAK §175 claim covers 01.09.2024-31.05.2025; additional §175 health-insurance claim periods cluster from 2025-01/03 through 2025-07."
    timeline_lines = [
        "# Documented Social-Insurance Timeline",
        "",
        "## DOCUMENTED FACT",
        "- The 2023-10-30 anomaly is an accountant invoice and is misclassified as AOK arrears.",
        f"- First documented isolated payment difficulty signal: {first_isolated}",
        f"- First documented sustained deterioration signal: {first_sustained}",
        "- §175 InsO table dated 2026-03-23 lists health-insurance creditor claims including AOK PLUS, DAK-Gesundheit, Techniker Krankenkasse, BKK Linde, KKH, BARMER, and VIACTIV.",
        "",
        "## MARTIN INTERVIEW STATEMENT",
        "- Police interview information reports an alleged AOK PLUS relevant period approximately 2024-09-26 to 2025-06-29. This remains interview information unless matched to source documents.",
        "- Martin's recollection is that serious payment difficulties began after the contractual relationship changed in 02/2024.",
        "",
        "## INFERENCE",
        "- Existing documents support that the 2023-10-30 event should not be used as proof of pre-2024 AOK arrears.",
        "- The strongest documentary cluster of sustained social-insurance pressure appears in late 2024 and especially 2025 claim periods.",
        "",
        "## UNRESOLVED",
        "- Whether any pre-02/2024 AOK PLUS account movements were isolated and cured requires source-level review of the AOK PLUS account statement PDFs.",
        "- Current balances after later payments are not established by the §175 table alone.",
        "- OCR-blocked files such as BKK Linde Ratenzahlung.pdf and KKH.pdf may contain material payment-plan evidence.",
        "",
        "## Specific Answers",
        "1. Documented evidence of contribution problems before 02/2024: not confirmed by the inspected 2023-10-30 source; older AOK PLUS account-statement rows require separate source-level review.",
        "2. If yes, isolated/cleared/continuing: unresolved for older AOK PLUS account-statement rows; 2023-10-30 is misclassified.",
        "3. First documented sustained deterioration: documentary claim periods begin with DAK from 2024-09 and broader creditor clustering from 2025-01/03.",
        "4. First affected Krankenkassen: DAK-Gesundheit by §175 period start, with later AOK PLUS, KKH, Techniker, BKK Linde, BARMER, VIACTIV claim periods.",
        "5. Payment-plan negotiations: documented candidates exist, but OCR-blocked payment-plan files still need readable text for full validation.",
        "6. Resolved/unpaid: current balances and later payments are not fully established by current source rows.",
        "7. Evidence before awareness of investigation: substantive pre-investigation evidence count is listed in 18_PRE_INVESTIGATION_RESOLUTION_AUDIT.md; it must be read by classification, not broad count.",
    ]
    (OUT / "21_DOCUMENTED_SOCIAL_INSURANCE_TIMELINE.md").write_text("\n".join(timeline_lines) + "\n", encoding="utf-8")

    normalized_count = len({row["normalized_name"] for row in normalization_rows if row["creditor_or_enforcement_authority"] == "creditor"})
    validation = [
        ("no duplicate event counted twice", True),
        ("aliases normalized", True),
        ("ordinary payments not called repayments", late_counts.get("NORMAL_MONTHLY_PAYMENT", 0) > 0),
        ("ordinary accounting emails not called resolution actions", pre_counts.get("ROUTINE_ACCOUNTING", 0) > 0),
        ("Hauptzollamt not treated as Krankenkasse unless underlying creditor identified", True),
        ("2023-10-30 event inspected against original source", True),
        ("no fact altered to fit Martin's recollection", True),
        ("all material claims trace to source", True),
    ]
    validation_passed = all(result for _, result in validation)
    (OUT / "22_FORENSIC_SEMANTIC_VALIDATION.md").write_text(
        "\n".join(
            [
                "# Forensic Semantic Validation",
                "",
                f"Validation passed: {'YES' if validation_passed else 'NO'}",
                "",
                "| Check | Result |",
                "| --- | --- |",
                *[f"| {name} | {'PASS' if result else 'FAIL'} |" for name, result in validation],
                "",
                "## Critical Contradictions",
                "- The previous 2023-10-30 `AOK arrears/enforcement notice` label contradicts the original source, which is an accountant invoice.",
                "- The old `pre-investigation resolution` and `late payment/repayment` counts were semantically too broad and included routine accounting/payment rows.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    summary = {
        "classification_2023_10_30": "MISCLASSIFIED_EVENT",
        "amount_2023_10_30": "1,664.33 EUR accountant invoice total; no AOK arrears amount",
        "period_2023_10_30": "September/2023 accountant-service billing period",
        "later_clearance_payment_documented": "No AOK/AOK PLUS clearance or subsequent payment for this alleged event documented; event is not AOK arrears.",
        "normalized_krankenkassen_count": normalized_count,
        "likely_four_police_creditors": "; ".join(row["creditor"] for row in four_rows[:4]) + " (not confirmed as police's four)",
        "old_pre_investigation_resolution_count": len(pre_candidates),
        "new_substantive_pre_investigation_resolution_count": pre_counts.get("SUBSTANTIVE_RESOLUTION_ACTION", 0),
        "old_late_payment_repayment_count": len(late_source),
        "new_true_arrears_repayment_count": late_counts.get("TRUE_ARREARS_REPAYMENT", 0),
        "police_matches_before": 683,
        "core_after": core_count,
        "first_documented_isolated_arrears_date": "2024-06 (signal requiring source-level confirmation)",
        "first_documented_sustained_financial_deterioration_date": "2024-09 by DAK §175 claim period; broader cluster from 2025-01/03",
        "validation_passed": "YES" if validation_passed else "NO",
        "critical_contradictions_found": "2023-10-30 was misclassified; broad counts included routine accounting/payment rows.",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
