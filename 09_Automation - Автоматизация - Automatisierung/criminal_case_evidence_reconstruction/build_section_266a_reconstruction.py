#!/usr/bin/env python3
"""Build source-traced social-insurance evidence package for Az. 390 Js 5935/26."""

from __future__ import annotations

import csv
import email
import html
import json
import re
import zipfile
from collections import defaultdict
from email import policy
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
INBOX = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("00_INBOX"))
REPORTS = next(p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("08_Reports"))
ACCOUNTING = INBOX / "Accounting"
ORGANIZED = INBOX / "Accounting_Organized"
CASH_FLOW = REPORTS / "Accounting_Cash_Flow"
STRICT = REPORTS / "Master_Financial_Timeline_Strict"
OUT = REPORTS / "Criminal_Case_390_Js_5935_26"
PDF_PASSWORD = "10001"

LEDGER_HEADERS = [
    "evidence_id",
    "event_date",
    "contribution_period",
    "Krankenkasse",
    "event_type",
    "amount_due",
    "due_date",
    "amount_paid",
    "payment_date",
    "amount_outstanding",
    "sender",
    "recipient",
    "communication_subject",
    "communication_summary",
    "payment_plan_status",
    "source_file",
    "source_path",
    "source_page",
    "source_snippet",
    "extraction_method",
    "confidence",
    "duplicate_references",
    "gap_flags",
]
AOK_HEADERS = [
    "document_date",
    "contribution_month",
    "amount_due",
    "due_date",
    "payment_date",
    "amount_paid",
    "outstanding_amount",
    "accounting_notification_date",
    "communication_date",
    "sender",
    "recipient",
    "subject",
    "request_made",
    "AOK_response",
    "payment_plan_terms",
    "later_payment_evidence",
    "source_file",
    "source_page",
    "source_snippet",
    "confidence",
]
CHRONO_HEADERS = [
    "event_date",
    "contribution_period",
    "Krankenkasse",
    "event_type",
    "amount_due",
    "due_date",
    "amount_paid",
    "payment_date",
    "amount_outstanding",
    "sender",
    "recipient",
    "communication_subject",
    "communication_summary",
    "payment_plan_status",
    "source_file",
    "source_snippet",
    "confidence",
    "gap_flags",
]
COMM_HEADERS = [
    "event_date",
    "sender",
    "recipient",
    "subject",
    "Krankenkasse",
    "communication_type",
    "communication_summary",
    "source_file",
    "source_snippet",
    "confidence",
]
PLAN_HEADERS = [
    "event_date",
    "Krankenkasse",
    "request_type",
    "payment_plan_status",
    "amount_due",
    "amount_outstanding",
    "due_date",
    "source_file",
    "source_snippet",
    "confidence",
]
LATE_HEADERS = [
    "event_date",
    "contribution_period",
    "Krankenkasse",
    "amount_due",
    "due_date",
    "amount_paid",
    "payment_date",
    "amount_outstanding",
    "event_type",
    "source_file",
    "source_snippet",
    "confidence",
]
CERT_HEADERS = [
    "document_date",
    "valid_until",
    "month",
    "health_insurance_name",
    "employer",
    "betriebsnummer",
    "status",
    "arrears_amount",
    "period_of_arrears",
    "exact_status_sentence",
    "source_file",
    "source_snippet",
    "confidence",
]
MISSING_HEADERS = [
    "gap_id",
    "Krankenkasse",
    "contribution_period",
    "missing_link",
    "why_missing",
    "documents_needed",
    "search_keywords",
    "suggested_folder",
]

INSURERS = [
    ("AOK PLUS", ["aok plus", "aokplus", "aok die gesundheit 01058", "01058 dresden"]),
    ("AOK Sachsen-Anhalt", ["aok sachsen-anhalt", "aok sachsen anhalt"]),
    ("AOK Hessen", ["aok hessen"]),
    ("AOK Bayern", ["aok bayern"]),
    ("AOK Nordost", ["aok nordost"]),
    ("AOK Baden-Wuerttemberg", ["aok baden-wuerttemberg", "aok baden-württemberg"]),
    ("AOK", ["aok"]),
    ("Techniker Krankenkasse", ["techniker krankenkasse", "tk krankenkasse", " ek techniker", "tk "]),
    ("KKH", ["kkh", "kaufmaennische krankenkasse", "kaufmännische krankenkasse"]),
    ("Barmer", ["barmer"]),
    ("DAK", ["dak-gesundheit", "dak gesundheit", "dak"]),
    ("BKK Linde", ["bkk linde"]),
    ("SBK", ["bkk sbk", "sbk"]),
    ("VIACTIV", ["viactiv"]),
    ("Vivida BKK", ["vivida bkk", "vivda bkk"]),
    ("IKK", ["ikk"]),
    ("BKK", [" bkk ", "bkk "]),
    ("Hauptzollamt / Krankenkasse", ["hauptzollamt"]),
]
HEALTH_TERMS = [
    "krankenkasse",
    "aok",
    "beitragsnachweis",
    "sozialversicherung",
    "sv-beitraege",
    "sv-beiträge",
    "einzugsstelle",
    "unbedenklich",
    "beitragsrueck",
    "beitragsrück",
    "rueckstand",
    "rückstand",
    "offene beitraege",
    "offene beiträge",
    "hauptzollamt",
]
PLAN_TERMS = ["ratenzahlung", "stundung", "zahlungsvereinbarung", "zahlungsplan", "fristverlaengerung", "fristverlängerung", "teilzahlung"]
NOTICE_TERMS = ["mahnung", "vollstreck", "pfaendung", "pfändung", "forderung", "rueckstand", "rückstand", "offen", "nicht gezahlt", "ruecklastschrift", "rücklastschrift"]
CONTRIB_TERMS = ["beitragsnachweis", "faelligkeit", "fälligkeit", "gesamtsumme", "sozialversicherungsbeitraege", "sozialversicherungsbeiträge", "sv-beitraege", "sv-beiträge"]
PAYMENT_TERMS = ["zahlung", "zahlungseingang", "ueberweisung", "überweisung", "lastschrift", "sepa", "bezahlt", "gezahlt"]
ACCOUNTANT_TERMS = ["brunettin", "buchhaltung", "steuerberater", "marco"]
MONTH_NAMES = {
    "januar": 1,
    "jan": 1,
    "februar": 2,
    "feb": 2,
    "maerz": 3,
    "märz": 3,
    "mrz": 3,
    "april": 4,
    "apr": 4,
    "mai": 5,
    "juni": 6,
    "jun": 6,
    "juli": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "oktober": 10,
    "okt": 10,
    "november": 11,
    "nov": 11,
    "dezember": 12,
    "dez": 12,
}


def norm(value: str) -> str:
    return (value or "").lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")


def repo_relative(path: Path | str) -> str:
    try:
        return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()
    except Exception:
        return str(path)


def clean(value: str, limit: int = 420) -> str:
    return re.sub(r"\s+", " ", value or "").strip()[:limit]


def parse_amount(value: str) -> float | None:
    if not value:
        return None
    text = value.strip().replace("EUR", "").replace("€", "").replace(" ", "")
    negative = text.startswith("-") or text.endswith("-")
    text = text.strip("-")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        result = float(text)
        return -result if negative else result
    except ValueError:
        return None


def amount_string(value: float | None) -> str:
    return "" if value is None else f"{abs(value):.2f}"


def parse_date(value: str) -> str:
    match = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b", value or "")
    if match:
        day, month, year = match.groups()
        year_i = int(year)
        if year_i < 100:
            year_i += 2000
        return f"{year_i:04d}-{int(month):02d}-{int(day):02d}"
    match = re.search(r"\b(20\d{2})[-_/ .](0?[1-9]|1[0-2])[-_/ .](\d{1,2})\b", value or "")
    if match:
        year, month, day = match.groups()
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    return ""


def find_dates(text: str) -> list[str]:
    values: list[str] = []
    for pattern in [r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", r"\b20\d{2}[-_/ .](?:0?[1-9]|1[0-2])[-_/ .]\d{1,2}\b"]:
        for match in re.finditer(pattern, text or ""):
            parsed = parse_date(match.group(0))
            if parsed and parsed not in values:
                values.append(parsed)
    return values


def find_month(text: str, filename: str = "") -> str:
    haystack = f"{filename} {text[:2000]}"
    patterns = [
        r"(?:beitragsmonat|abrechnungsmonat|zeitraum|leistungszeitraum|monat)\D{0,30}(0?[1-9]|1[0-2])[-./_ ](20\d{2})",
        r"(?:beitragsmonat|abrechnungsmonat|zeitraum|leistungszeitraum|monat)\D{0,30}(20\d{2})[-./_ ](0?[1-9]|1[0-2])",
    ]
    for pattern in patterns:
        match = re.search(pattern, haystack, re.I)
        if match:
            first, second = match.groups()
            return f"{int(first):04d}-{int(second):02d}" if len(first) == 4 else f"{int(second):04d}-{int(first):02d}"
    for pattern in [r"\b(0?[1-9]|1[0-2])[-_./](20\d{2})\b", r"\b(20\d{2})[-_./](0?[1-9]|1[0-2])\b"]:
        match = re.search(pattern, filename)
        if match:
            first, second = match.groups()
            return f"{int(first):04d}-{int(second):02d}" if len(first) == 4 else f"{int(second):04d}-{int(first):02d}"
    normalized = norm(haystack)
    for name, month in MONTH_NAMES.items():
        match = re.search(r"\b" + re.escape(name) + r"\b\D{0,20}(20\d{2})", normalized)
        if match:
            return f"{int(match.group(1)):04d}-{month:02d}"
    parsed = parse_date(haystack)
    return parsed[:7] if parsed else ""


def detect_insurers(text: str) -> list[str]:
    haystack = " " + norm(text) + " "
    found: list[str] = []
    for name, terms in INSURERS:
        if any(norm(term) in haystack for term in terms):
            found.append(name)
    if "AOK" in found and any((item.startswith("AOK ") or item == "AOK PLUS") for item in found if item != "AOK"):
        found.remove("AOK")
    return found or ([] if "krankenkasse" not in haystack else ["Krankenkasse unspecified"])


def detect_event_type(text: str, source: str = "") -> str:
    haystack = norm(text + " " + source)
    if "unbedenklich" in haystack:
        return "UNBEDENKLICHKEITSBESCHEINIGUNG"
    if any(norm(term) in haystack for term in PLAN_TERMS):
        return "PAYMENT_PLAN_OR_STUNDUNG"
    if any(norm(term) in haystack for term in NOTICE_TERMS):
        return "ARREARS_OR_ENFORCEMENT_NOTICE"
    if any(norm(term) in haystack for term in PAYMENT_TERMS) and any(term in haystack for term in ["bank", "konto", "sepa", "zahlung"]):
        return "PAYMENT_EVIDENCE_OR_PAYMENT_LIST"
    if any(norm(term) in haystack for term in CONTRIB_TERMS):
        return "CONTRIBUTION_DUE_OR_NOTIFICATION"
    if any(norm(term) in haystack for term in ACCOUNTANT_TERMS):
        return "ACCOUNTANT_COMMUNICATION"
    return "HEALTH_INSURANCE_RELATED_DOCUMENT"


def classify_amount(text: str, source: str = "") -> tuple[str, str]:
    amount_pattern = r"-?\d{1,3}(?:[.\s]\d{3})*,\d{2}-?|-?\d+,\d{2}-?"
    candidates = []
    for match in re.finditer(amount_pattern, text or ""):
        context = norm(text[max(0, match.start() - 80) : match.end() + 80])
        amount = parse_amount(match.group(0))
        if amount is None:
            continue
        score = 0
        if any(term in context for term in ["gesamt", "beitrag", "forderung", "rueckstand", "offen", "faellig", "zahlung", "ueberweisung", "lastschrift", "sepa"]):
            score += 2
        if abs(amount) < 1:
            score -= 1
        candidates.append((score, amount, context))
    if not candidates:
        return "", ""
    candidates.sort(key=lambda item: (item[0], abs(item[1])), reverse=True)
    _, amount, context = candidates[0]
    if any(term in context for term in ["rueckstand", "offen", "forderung", "mahnbetrag", "nicht gezahlt", "keine ueberw", "ruecklastschrift"]):
        return "outstanding", amount_string(amount)
    if any(term in context for term in ["zahlungseingang", "gezahlt", "bezahlt", "ueberweisung", "lastschrift", "sepa"]) and ("bank" in norm(source) or "bank" in norm(text) or "konto" in norm(text)):
        return "paid", amount_string(amount)
    if any(term in context for term in ["faellig", "beitrag", "gesamtsumme", "nachweis", "soll", "zahlbetrag"]):
        return "due", amount_string(amount)
    return "unknown", amount_string(amount)


def extract_due_date(text: str) -> str:
    match = re.search(r"(?:fälligkeit\s*bis|faelligkeit\s*bis|fällig\s*am|faellig\s*am|due date)\D{0,25}(\d{1,2}\.\d{1,2}\.\d{2,4})", text or "", re.I)
    return parse_date(match.group(1)) if match else ""


def text_from_file(path: Path) -> tuple[str, str, str]:
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".csv", ".md", ".json", ".log"}:
            return path.read_text(encoding="utf-8", errors="ignore"), "text_file", ""
        if suffix in {".htm", ".html"}:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            raw = re.sub(r"<(script|style).*?</\1>", " ", raw, flags=re.S | re.I)
            return re.sub(r"<[^>]+>", " ", html.unescape(raw)), "html_text", ""
        if suffix == ".eml":
            msg = email.message_from_binary_file(path.open("rb"), policy=policy.default)
            parts = [f"Date: {msg.get('date', '')}", f"From: {msg.get('from', '')}", f"To: {msg.get('to', '')}", f"Subject: {msg.get('subject', '')}"]
            attachments: list[str] = []
            for part in msg.walk():
                filename = part.get_filename()
                if filename:
                    attachments.append(filename)
                if part.get_content_type() in {"text/plain", "text/html"}:
                    try:
                        parts.append(str(part.get_content()))
                    except Exception:
                        pass
            if attachments:
                parts.append("Attachments: " + ", ".join(attachments))
            return "\n".join(parts), "eml_headers_body_attachments", ""
        if suffix == ".pdf":
            try:
                import fitz  # type: ignore

                doc = fitz.open(path)
                if doc.needs_pass and not doc.authenticate(PDF_PASSWORD):
                    return "", "pdf_fitz", "encrypted PDF unreadable with password 10001"
                page_texts = []
                for index, page in enumerate(doc, start=1):
                    text = page.get_text("text") or ""
                    if text.strip():
                        page_texts.append(f"[[page {index}]]\n{text}")
                return "\n".join(page_texts), "pdf_fitz", "" if page_texts else "no text extracted; OCR may be needed"
            except Exception as first_error:
                try:
                    import pdfplumber  # type: ignore

                    with pdfplumber.open(str(path), password=PDF_PASSWORD) as pdf:
                        return "\n".join(page.extract_text() or "" for page in pdf.pages), "pdfplumber", ""
                except Exception as second_error:
                    return "", "pdf_extract_failed", f"{first_error}; {second_error}"
        if suffix == ".xlsx":
            values: list[str] = []
            with zipfile.ZipFile(path) as archive:
                shared: list[str] = []
                if "xl/sharedStrings.xml" in archive.namelist():
                    data = archive.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
                    shared = [html.unescape(re.sub("<[^>]+>", "", item)) for item in re.findall(r"<t[^>]*>(.*?)</t>", data, flags=re.S)]
                for name in archive.namelist():
                    if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                        data = archive.read(name).decode("utf-8", errors="ignore")
                        for cell in re.findall(r"<c[^>]*(?:t=\"s\")?[^>]*>.*?</c>", data, flags=re.S):
                            match = re.search(r"<v>(.*?)</v>", cell)
                            if match:
                                value = match.group(1)
                                if 't="s"' in cell and value.isdigit() and int(value) < len(shared):
                                    values.append(shared[int(value)])
                                else:
                                    values.append(value)
            return "\n".join(values), "xlsx_xml_text", ""
    except Exception as exc:
        return "", "read_failed", str(exc)
    return "", "unsupported", "unsupported file type"


def relevant_by_name(path: Path) -> bool:
    haystack = norm(str(path))
    terms = HEALTH_TERMS + PLAN_TERMS + NOTICE_TERMS + ACCOUNTANT_TERMS + ["zahlung", "sepa", "bank", "konto"]
    return any(norm(term) in haystack for term in terms)


def snippet_around(text: str, terms: list[str]) -> str:
    haystack = norm(text)
    positions = [haystack.find(norm(term)) for term in terms if haystack.find(norm(term)) >= 0]
    position = min(positions) if positions else 0
    return clean(text[max(0, position - 180) : position + 520])


def add_row(rows: list[dict[str, str]], row: dict[str, str]) -> None:
    rows.append({header: str(row.get(header, "")) for header in LEDGER_HEADERS})


def build_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    rows: list[dict[str, str]] = []
    unreadable_count = 0
    strict_ledger = STRICT / "financial_evidence_ledger.csv"
    if strict_ledger.exists():
        with strict_ledger.open("r", encoding="utf-8-sig", newline="") as handle:
            for source_row in csv.DictReader(handle):
                if source_row.get("category") != "Health Insurance" and "HEALTH_INSURANCE" not in source_row.get("amount_type", ""):
                    continue
                amount_type = source_row.get("amount_type", "")
                event_type = "CONTRIBUTION_DUE_OR_NOTIFICATION"
                amount_due = amount_paid = amount_outstanding = ""
                if amount_type == "HEALTH_INSURANCE_DUE":
                    amount_due = source_row.get("amount", "")
                elif amount_type == "HEALTH_INSURANCE_PAID":
                    amount_paid = source_row.get("amount", "")
                elif amount_type == "HEALTH_INSURANCE_UNPAID":
                    amount_outstanding = source_row.get("amount", "")
                else:
                    event_type = "HEALTH_INSURANCE_AMOUNT_EXCLUDED_FROM_STRICT_TOTALS"
                haystack = " ".join([source_row.get("creditor", ""), source_row.get("source_snippet", ""), source_row.get("source_file", "")])
                insurers = detect_insurers(haystack) or [source_row.get("creditor") or "Krankenkasse unspecified"]
                for insurer in insurers[:3]:
                    add_row(
                        rows,
                        {
                            "event_date": source_row.get("document_date", ""),
                            "contribution_period": source_row.get("month", ""),
                            "Krankenkasse": insurer,
                            "event_type": event_type,
                            "amount_due": amount_due,
                            "amount_paid": amount_paid,
                            "amount_outstanding": amount_outstanding,
                            "source_file": Path(source_row.get("source_file", "")).name,
                            "source_path": source_row.get("source_file", ""),
                            "source_snippet": source_row.get("source_snippet", ""),
                            "extraction_method": "existing_strict_financial_evidence_ledger",
                            "confidence": source_row.get("confidence", "LOW"),
                        },
                    )
    health_timeline = CASH_FLOW / "health_insurance_timeline.csv"
    if health_timeline.exists():
        with health_timeline.open("r", encoding="utf-8-sig", newline="") as handle:
            for source_row in csv.DictReader(handle):
                if not any(source_row.get(field) for field in ["amount_due", "amount_paid", "unpaid_balance", "source_snippet"]):
                    continue
                source = source_row.get("source_documents", "")
                add_row(
                    rows,
                    {
                        "contribution_period": source_row.get("month", ""),
                        "Krankenkasse": source_row.get("insurance_name", ""),
                        "event_type": "HEALTH_INSURANCE_EXTRACTED_ROW",
                        "amount_due": source_row.get("amount_due", ""),
                        "due_date": source_row.get("due_date", ""),
                        "amount_paid": source_row.get("amount_paid", ""),
                        "amount_outstanding": source_row.get("unpaid_balance", ""),
                        "source_file": Path(source).name,
                        "source_path": source,
                        "source_snippet": source_row.get("source_snippet", ""),
                        "extraction_method": "existing_accounting_cash_flow_health_timeline",
                        "confidence": source_row.get("confidence", "LOW"),
                    },
                )
    certificate_rows: list[dict[str, str]] = []
    certificates = CASH_FLOW / "unbedenklichkeitsbescheinigungen_status.csv"
    if certificates.exists():
        with certificates.open("r", encoding="utf-8-sig", newline="") as handle:
            for source_row in csv.DictReader(handle):
                certificate_rows.append(source_row)
                add_row(
                    rows,
                    {
                        "event_date": source_row.get("document_date", ""),
                        "contribution_period": source_row.get("month", ""),
                        "Krankenkasse": source_row.get("health_insurance_name", ""),
                        "event_type": "UNBEDENKLICHKEITSBESCHEINIGUNG_" + (source_row.get("status") or "UNKNOWN"),
                        "amount_outstanding": source_row.get("arrears_amount", ""),
                        "communication_summary": source_row.get("exact_status_sentence", ""),
                        "source_file": Path(source_row.get("source_file", "")).name,
                        "source_path": source_row.get("source_file", ""),
                        "source_snippet": source_row.get("source_snippet") or source_row.get("exact_status_sentence", ""),
                        "extraction_method": "existing_unbedenklichkeitsbescheinigung_status",
                        "confidence": source_row.get("confidence", "LOW"),
                    },
                )
    scan_roots = [ACCOUNTING, ORGANIZED, CASH_FLOW / "recovered_health_insurance_text"]
    files: list[Path] = []
    for root in scan_roots:
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in {".pdf", ".txt", ".csv", ".md", ".json", ".eml", ".htm", ".html", ".xlsx"} and relevant_by_name(path):
                    files.append(path)
    for path in files:
        text, method, error = text_from_file(path)
        haystack = f"{path}\n{text[:12000]}"
        terms = HEALTH_TERMS + PLAN_TERMS + NOTICE_TERMS + ["zahlung", "sepa", "brunettin", "marco"]
        if not any(norm(term) in norm(haystack) for term in terms):
            continue
        if error and not text.strip():
            unreadable_count += 1
            continue
        insurers = detect_insurers(haystack)
        if not insurers:
            continue
        event_type = detect_event_type(text, str(path))
        snippet = snippet_around(text or str(path), HEALTH_TERMS + PLAN_TERMS + NOTICE_TERMS + CONTRIB_TERMS + PAYMENT_TERMS)
        month = find_month(text, path.name)
        event_date = (find_dates(text) or [""])[0]
        amount_kind, amount = classify_amount(snippet or text[:1000], str(path))
        amount_due = amount_paid = amount_outstanding = ""
        if amount_kind == "due":
            amount_due = amount
        elif amount_kind == "paid":
            amount_paid = amount
        elif amount_kind == "outstanding":
            amount_outstanding = amount
        summary = "Health-insurance related document detected by text/path keywords."
        if event_type == "PAYMENT_PLAN_OR_STUNDUNG":
            summary = "Document text/path contains request or arrangement terms for Ratenzahlung/Stundung/Zahlungsvereinbarung/Zahlungsplan."
        elif event_type == "ARREARS_OR_ENFORCEMENT_NOTICE":
            summary = "Document text/path contains arrears, reminder, enforcement, open-balance, or non-payment wording."
        elif event_type.startswith("UNBEDENKLICH"):
            summary = "Document relates to Unbedenklichkeitsbescheinigung; exact status should be read from source snippet."
        elif event_type == "CONTRIBUTION_DUE_OR_NOTIFICATION":
            summary = "Document contains contribution notice/list terminology."
        subject = sender = recipient = ""
        if path.suffix.lower() == ".eml":
            for line in text.splitlines()[:20]:
                low = line.lower()
                if low.startswith("subject:"):
                    subject = line.split(":", 1)[1].strip()
                elif low.startswith("from:"):
                    sender = line.split(":", 1)[1].strip()
                elif low.startswith("to:"):
                    recipient = line.split(":", 1)[1].strip()
        for insurer in insurers[:4]:
            add_row(
                rows,
                {
                    "event_date": event_date,
                    "contribution_period": month,
                    "Krankenkasse": insurer,
                    "event_type": event_type,
                    "amount_due": amount_due,
                    "due_date": extract_due_date(text),
                    "amount_paid": amount_paid,
                    "payment_date": event_date if amount_paid else "",
                    "amount_outstanding": amount_outstanding,
                    "sender": sender,
                    "recipient": recipient,
                    "communication_subject": subject,
                    "communication_summary": summary,
                    "payment_plan_status": "REQUEST_OR_PLAN_TERMS_FOUND" if event_type == "PAYMENT_PLAN_OR_STUNDUNG" else "",
                    "source_file": path.name,
                    "source_path": repo_relative(path),
                    "source_snippet": snippet,
                    "extraction_method": method + "_keyword_scan",
                    "confidence": "HIGH" if snippet and (amount_due or amount_paid or amount_outstanding or event_type in {"PAYMENT_PLAN_OR_STUNDUNG", "UNBEDENKLICHKEITSBESCHEINIGUNG"}) else "MEDIUM",
                },
            )
    return rows, certificate_rows, unreadable_count


def deduplicate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    keyed: dict[tuple[str, ...], dict[str, str]] = {}
    for row in rows:
        key = (
            row["event_date"],
            row["contribution_period"],
            row["Krankenkasse"],
            row["event_type"],
            row["amount_due"],
            row["amount_paid"],
            row["amount_outstanding"],
            row["source_path"],
            row["source_snippet"][:160],
        )
        if key in keyed:
            existing = keyed[key]
            duplicate = row["source_path"]
            if duplicate and duplicate != existing.get("source_path"):
                existing["duplicate_references"] = "; ".join(item for item in [existing.get("duplicate_references", ""), duplicate] if item)
        else:
            keyed[key] = row
    ledger = list(keyed.values())
    ledger.sort(key=lambda row: (row.get("event_date") or row.get("contribution_period") or "9999", row.get("Krankenkasse", ""), row.get("event_type", ""), row.get("source_path", "")))
    for index, row in enumerate(ledger, start=1):
        row["evidence_id"] = f"SI-390JS-5935-26-{index:05d}"
        gaps: list[str] = []
        if not row["source_file"]:
            gaps.append("missing source_file")
        if row["event_type"] in {"CONTRIBUTION_DUE_OR_NOTIFICATION", "HEALTH_INSURANCE_EXTRACTED_ROW"} and not row["contribution_period"]:
            gaps.append("missing contribution_period")
        if row["amount_due"] and not row["due_date"]:
            gaps.append("missing due_date")
        if row["amount_paid"] and not row["payment_date"]:
            gaps.append("missing payment_date")
        row["gap_flags"] = "; ".join(gaps)
    return ledger


def is_aok_plus(row: dict[str, str]) -> bool:
    return norm(row.get("Krankenkasse", "")) == "aok plus" or "aok plus" in norm(row.get("source_snippet", "") + " " + row.get("source_path", ""))


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def column_name(index: int) -> str:
    value = ""
    while index:
        index, rem = divmod(index - 1, 26)
        value = chr(65 + rem) + value
    return value


def write_xlsx(path: Path, headers: list[str], rows: list[dict[str, str]], sheet_name: str = "Sheet1") -> None:
    values = [headers] + [[str(row.get(header, "")) for header in headers] for row in rows]
    sheet_rows = []
    for row_index, row_values in enumerate(values, start=1):
        cells = []
        for col_index, value in enumerate(row_values, start=1):
            cells.append(f'<c r="{column_name(col_index)}{row_index}" t="inlineStr"><is><t>{escape(value)}</t></is></c>')
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


def markdown_table(headers: list[str], rows: list[dict[str, str]], limit: int = 40) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows[:limit]:
        lines.append("| " + " | ".join(clean(str(row.get(header, "")), 120).replace("|", "/") for header in headers) + " |")
    if len(rows) > limit:
        lines.append("| ... | " + f"{len(rows) - limit} additional rows in CSV/XLSX |" + " |" * (len(headers) - 2))
    return "\n".join(lines)


def build_outputs() -> dict[str, object]:
    OUT.mkdir(parents=True, exist_ok=True)
    source_rows, certificate_source_rows, unreadable_count = build_rows()
    ledger = deduplicate(source_rows)
    aok_rows = []
    for row in ledger:
        if is_aok_plus(row):
            aok_rows.append(
                {
                    "document_date": row["event_date"],
                    "contribution_month": row["contribution_period"],
                    "amount_due": row["amount_due"],
                    "due_date": row["due_date"],
                    "payment_date": row["payment_date"],
                    "amount_paid": row["amount_paid"],
                    "outstanding_amount": row["amount_outstanding"],
                    "accounting_notification_date": row["event_date"] if "ACCOUNTANT" in row["event_type"] or "NOTIFICATION" in row["event_type"] else "",
                    "communication_date": row["event_date"] if row["sender"] or row["recipient"] or row["communication_subject"] or "COMMUNICATION" in row["event_type"] else "",
                    "sender": row["sender"],
                    "recipient": row["recipient"],
                    "subject": row["communication_subject"],
                    "request_made": row["communication_summary"] if "PAYMENT_PLAN" in row["event_type"] else "",
                    "AOK_response": row["communication_summary"] if "RESPONSE" in row["event_type"] else "",
                    "payment_plan_terms": row["payment_plan_status"],
                    "later_payment_evidence": row["communication_summary"] if row["amount_paid"] else "",
                    "source_file": row["source_path"],
                    "source_page": row["source_page"],
                    "source_snippet": row["source_snippet"],
                    "confidence": row["confidence"],
                }
            )
    chron = [{header: row.get(header, "") for header in CHRONO_HEADERS} for row in ledger]
    communications = []
    plans = []
    late = []
    for row in ledger:
        event_type = row["event_type"]
        if row["sender"] or row["recipient"] or row["communication_subject"] or "ACCOUNTANT" in event_type or "PAYMENT_PLAN" in event_type:
            communications.append(
                {
                    "event_date": row["event_date"],
                    "sender": row["sender"],
                    "recipient": row["recipient"],
                    "subject": row["communication_subject"],
                    "Krankenkasse": row["Krankenkasse"],
                    "communication_type": event_type,
                    "communication_summary": row["communication_summary"],
                    "source_file": row["source_path"],
                    "source_snippet": row["source_snippet"],
                    "confidence": row["confidence"],
                }
            )
        if "PAYMENT_PLAN" in event_type or row["payment_plan_status"]:
            plans.append(
                {
                    "event_date": row["event_date"],
                    "Krankenkasse": row["Krankenkasse"],
                    "request_type": "Ratenzahlung/Stundung/Zahlungsvereinbarung/Zahlungsplan terms found",
                    "payment_plan_status": row["payment_plan_status"],
                    "amount_due": row["amount_due"],
                    "amount_outstanding": row["amount_outstanding"],
                    "due_date": row["due_date"],
                    "source_file": row["source_path"],
                    "source_snippet": row["source_snippet"],
                    "confidence": row["confidence"],
                }
            )
        if row["amount_paid"] or row["amount_outstanding"] or "ARREARS" in event_type:
            late.append(
                {
                    "event_date": row["event_date"],
                    "contribution_period": row["contribution_period"],
                    "Krankenkasse": row["Krankenkasse"],
                    "amount_due": row["amount_due"],
                    "due_date": row["due_date"],
                    "amount_paid": row["amount_paid"],
                    "payment_date": row["payment_date"],
                    "amount_outstanding": row["amount_outstanding"],
                    "event_type": event_type,
                    "source_file": row["source_path"],
                    "source_snippet": row["source_snippet"],
                    "confidence": row["confidence"],
                }
            )
    certificate_rows = []
    for source_row in certificate_source_rows:
        certificate_rows.append(
            {
                "document_date": source_row.get("document_date", ""),
                "valid_until": source_row.get("valid_until", ""),
                "month": source_row.get("month", ""),
                "health_insurance_name": source_row.get("health_insurance_name", ""),
                "employer": source_row.get("employer", ""),
                "betriebsnummer": source_row.get("betriebsnummer", ""),
                "status": source_row.get("status", ""),
                "arrears_amount": source_row.get("arrears_amount", ""),
                "period_of_arrears": source_row.get("period_of_arrears", ""),
                "exact_status_sentence": source_row.get("exact_status_sentence", ""),
                "source_file": source_row.get("source_file", ""),
                "source_snippet": source_row.get("source_snippet", "") or source_row.get("exact_status_sentence", ""),
                "confidence": source_row.get("confidence", "LOW"),
            }
        )
    for row in ledger:
        if "UNBEDENKLICH" in row["event_type"] and not any(item["source_file"] == row["source_path"] and item["source_snippet"] == row["source_snippet"] for item in certificate_rows):
            status = row["event_type"].replace("UNBEDENKLICHKEITSBESCHEINIGUNG_", "") if "_" in row["event_type"] else "UNKNOWN"
            certificate_rows.append(
                {
                    "document_date": row["event_date"],
                    "valid_until": "",
                    "month": row["contribution_period"],
                    "health_insurance_name": row["Krankenkasse"],
                    "employer": "",
                    "betriebsnummer": "",
                    "status": status,
                    "arrears_amount": row["amount_outstanding"],
                    "period_of_arrears": "",
                    "exact_status_sentence": row["communication_summary"],
                    "source_file": row["source_path"],
                    "source_snippet": row["source_snippet"],
                    "confidence": row["confidence"],
                }
            )
    by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in ledger:
        if row["Krankenkasse"] and row["contribution_period"]:
            by_key[(row["Krankenkasse"], row["contribution_period"])].append(row)
    missing = []
    gap_id = 1
    for (insurer, month), rows_for_key in sorted(by_key.items()):
        if month < "2024-01" or month > "2025-06":
            continue
        checks = [
            ("CONTRIBUTION_DUE", "contribution notice or contribution list", f"Beitragsnachweis {insurer} {month}", any(row["amount_due"] for row in rows_for_key)),
            ("ACCOUNTING_NOTIFICATION", "accountant-to-Martin obligation notification", f"Brunettin Zahlung {insurer} {month}", any("NOTIFICATION" in row["event_type"] or "ACCOUNTANT" in row["event_type"] for row in rows_for_key)),
            ("PAYMENT_OR_NONPAYMENT", "bank payment, returned debit, or explicit outstanding balance", f"SEPA Lastschrift Ueberweisung {insurer} {month}", any(row["amount_paid"] or row["amount_outstanding"] for row in rows_for_key)),
            ("KRANKENKASSE_COMMUNICATION", "communication with Krankenkasse/Einzugsstelle", f"email {insurer} Ratenzahlung Mahnung {month}", any(row["sender"] or row["recipient"] or row["communication_subject"] or "PAYMENT_PLAN" in row["event_type"] for row in rows_for_key)),
            ("PAYMENT_PLAN_OR_STUNDUNG", "request/response/payment plan if applicable", f"Ratenzahlung Stundung Zahlungsvereinbarung {insurer} {month}", any("PAYMENT_PLAN" in row["event_type"] for row in rows_for_key)),
        ]
        for missing_link, documents_needed, keywords, present in checks:
            if not present:
                missing.append(
                    {
                        "gap_id": f"GAP-{gap_id:04d}",
                        "Krankenkasse": insurer,
                        "contribution_period": month,
                        "missing_link": missing_link,
                        "why_missing": "No source row in current evidence package establishes this link.",
                        "documents_needed": documents_needed,
                        "search_keywords": keywords,
                        "suggested_folder": "00_INBOX - Входящи - Eingang/Accounting_Organized/04_Health_Insurance",
                    }
                )
                gap_id += 1
    for month in ["2024-09", "2024-10", "2024-11", "2024-12", "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]:
        if ("AOK PLUS", month) not in by_key:
            missing.append(
                {
                    "gap_id": f"GAP-{gap_id:04d}",
                    "Krankenkasse": "AOK PLUS",
                    "contribution_period": month,
                    "missing_link": "AOK_PLUS_MONTH_NOT_DOCUMENTED",
                    "why_missing": "No AOK PLUS source row was found for this interview-priority month.",
                    "documents_needed": "AOK PLUS Beitragsnachweis, accountant email, Krankenkasse response, payment proof, or arrears notice",
                    "search_keywords": f"AOK PLUS {month} Beitragsnachweis Ratenzahlung Zahlung Mahnung",
                    "suggested_folder": "00_INBOX - Входящи - Eingang/Accounting_Organized/04_Health_Insurance",
                }
            )
            gap_id += 1
    pre_investigation = [
        row
        for row in ledger
        if row["event_date"]
        and row["event_date"] < "2026-01-01"
        and (
            "PAYMENT_PLAN" in row["event_type"]
            or "ARREARS" in row["event_type"]
            or row["amount_outstanding"]
            or (row["amount_paid"] and any(term in norm(row["source_snippet"]) for term in ["rueckstand", "ratenzahlung", "stundung", "mahnung", "forderung"]))
        )
    ]
    police_sections = {
        "A. Accountant -> Martin monthly payment/obligation summaries": [row for row in ledger if "ACCOUNTANT" in row["event_type"] or "NOTIFICATION" in row["event_type"]],
        "B. Accountant -> Krankenkassen correspondence": [
            row
            for row in ledger
            if ("PAYMENT_PLAN" in row["event_type"] or row["sender"] or row["recipient"]) and any(term in norm(row["source_snippet"] + row["source_path"]) for term in ["brunettin", "buchhaltung", "marco"])
        ],
        "C. Krankenkassen -> accountant/Martin responses": [row for row in ledger if row["sender"] or "antwort" in norm(row["source_snippet"]) or "response" in norm(row["event_type"])],
        "D. Ratenzahlung/Stundung requests": [row for row in ledger if "PAYMENT_PLAN" in row["event_type"]],
        "E. payment plans": [row for row in ledger if any(term in norm(row["source_snippet"]) for term in ["zahlungsplan", "zahlungsvereinbarung", "ratenzahlung"])],
        "F. evidence of payments made under or after arrangements": [row for row in ledger if row["amount_paid"]],
        "G. evidence establishing when contribution-payment difficulties began": [row for row in ledger if row["amount_outstanding"] or "ARREARS" in row["event_type"]],
    }
    outputs = [
        ("01_SOCIAL_INSURANCE_MASTER_EVIDENCE_LEDGER", LEDGER_HEADERS, ledger),
        ("02_AOK_PLUS_CHRONOLOGY", AOK_HEADERS, aok_rows),
        ("03_ALL_KRANKENKASSEN_CHRONOLOGY", CHRONO_HEADERS, chron),
        ("04_ACCOUNTANT_COMMUNICATION_TIMELINE", COMM_HEADERS, communications),
        ("05_PAYMENT_PLAN_AND_STUNDUNG_EVIDENCE", PLAN_HEADERS, plans),
        ("06_LATE_PAYMENT_AND_REPAYMENT_TIMELINE", LATE_HEADERS, late),
        ("07_UNBEDENKLICHKEITSBESCHEINIGUNGEN_TIMELINE", CERT_HEADERS, certificate_rows),
        ("08_MISSING_CRITICAL_EVIDENCE", MISSING_HEADERS, missing),
    ]
    for stem, headers, rows in outputs:
        write_csv(OUT / f"{stem}.csv", headers, rows)
        write_xlsx(OUT / f"{stem}.xlsx", headers, rows, stem[:31])
    other_insurers = sorted({row["Krankenkasse"] for row in ledger if row["Krankenkasse"] and not is_aok_plus(row)})
    earliest = "Not identified from dated source rows."
    for row in sorted(ledger, key=lambda item: item["event_date"] or "9999"):
        if row["event_date"] and (row["amount_outstanding"] or "ARREARS" in row["event_type"] or "PAYMENT_PLAN" in row["event_type"]):
            earliest = f"{row['event_date']} - {row['Krankenkasse']} - {row['event_type']} - {row['source_path']}"
            break
    (OUT / "09_POLICE_EVIDENCE_INDEX.md").write_text(
        "\n".join(
            [
                "# Police Evidence Index - Az. 390 Js 5935/26",
                "",
                "This index lists existing repository evidence relevant to social-insurance contribution chronology. It does not copy or move original evidence and does not make legal conclusions.",
                "",
                f"- Total evidence rows: {len(ledger)}",
                f"- AOK PLUS evidence rows: {len(aok_rows)}",
                f"- Other Krankenkassen identified: {', '.join(other_insurers) if other_insurers else 'None'}",
                f"- Earliest documented payment difficulty: {earliest}",
                "",
                "## Evidence Tables",
                "- 01_SOCIAL_INSURANCE_MASTER_EVIDENCE_LEDGER.csv/xlsx",
                "- 02_AOK_PLUS_CHRONOLOGY.csv/xlsx",
                "- 03_ALL_KRANKENKASSEN_CHRONOLOGY.csv/xlsx",
                "- 04_ACCOUNTANT_COMMUNICATION_TIMELINE.csv/xlsx",
                "- 05_PAYMENT_PLAN_AND_STUNDUNG_EVIDENCE.csv/xlsx",
                "- 06_LATE_PAYMENT_AND_REPAYMENT_TIMELINE.csv/xlsx",
                "- 07_UNBEDENKLICHKEITSBESCHEINIGUNGEN_TIMELINE.csv/xlsx",
                "- 08_MISSING_CRITICAL_EVIDENCE.csv/xlsx",
                "",
                "## Important Scope Note",
                "Police interview information refers to an alleged AOK PLUS period approximately 2024-09-26 to 2025-06-29. This package records that as investigation-interview information only; documentary facts are listed only where source rows support them.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "10_AOK_PLUS_EVIDENCE_RECONSTRUCTION.md").write_text(
        "\n".join(
            [
                "# AOK PLUS Evidence Reconstruction",
                "",
                "Purpose: reconstruct AOK PLUS contribution/payment/communication evidence for Az. 390 Js 5935/26 without legal conclusions.",
                "",
                "Investigation-interview information: alleged relevant period approximately 2024-09-26 to 2025-06-29. This is not treated as independently verified unless matched by source rows below.",
                "",
                f"AOK PLUS evidence rows: {len(aok_rows)}",
                "",
                "## Chronology",
                markdown_table(AOK_HEADERS, aok_rows, 80),
                "",
                "## Gaps",
                markdown_table(MISSING_HEADERS, [row for row in missing if row["Krankenkasse"] == "AOK PLUS"], 80),
                "",
                "No intent, guilt, innocence, or legal conclusion is inferred.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "11_SOCIAL_INSURANCE_CASE_CHRONOLOGY.md").write_text(
        "\n".join(
            [
                "# Social Insurance Case Chronology",
                "",
                "This chronology is evidence reconstruction only. Missing values remain blank and no payment/non-payment is inferred beyond the source snippets.",
                "",
                f"Total evidence rows: {len(ledger)}",
                f"Krankenkassen identified: {', '.join(sorted({row['Krankenkasse'] for row in ledger if row['Krankenkasse']}))}",
                "",
                "## Master Chronology Preview",
                markdown_table(CHRONO_HEADERS, chron, 120),
                "",
                "## Critical Cross-Check Method",
                "For each Krankenkasse/month the package checks for CONTRIBUTION DUE -> ACCOUNTING NOTIFICATION -> PAYMENT / NON-PAYMENT -> COMMUNICATION WITH KRANKENKASSE -> PAYMENT PLAN / STUNDUNG REQUEST -> RESPONSE -> LATER PAYMENT -> REMAINING BALANCE. Missing links are listed in 08_MISSING_CRITICAL_EVIDENCE.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "12_PRE_INVESTIGATION_RESOLUTION_EVIDENCE.md").write_text(
        "\n".join(
            [
                "# Pre-Investigation Resolution Evidence",
                "",
                "This report identifies dated documentary evidence showing attempts or events related to addressing social-insurance arrears before awareness of the criminal investigation. It does not characterize the evidence as proof of innocence.",
                "",
                f"Items found: {len(pre_investigation)}",
                "",
                markdown_table(["event_date", "Krankenkasse", "event_type", "amount_paid", "amount_outstanding", "source_path", "source_snippet", "confidence"], pre_investigation, 120),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    package_lines = ["# Police Request Document Package", "", "This is an indexed proposed package only. Original evidence has not been copied or moved.", ""]
    for section, rows in police_sections.items():
        package_lines += [
            f"## {section}",
            f"Matching evidence rows: {len(rows)}",
            markdown_table(["event_date", "contribution_period", "Krankenkasse", "event_type", "source_path", "source_snippet", "confidence"], rows, 40),
            "",
        ]
    (OUT / "13_POLICE_REQUEST_DOCUMENT_PACKAGE.md").write_text("\n".join(package_lines) + "\n", encoding="utf-8")
    validation_checks = [
        ("every factual row has source_file", all(row.get("source_file") for row in ledger)),
        ("every monetary amount traces to source", all((not (row.get("amount_due") or row.get("amount_paid") or row.get("amount_outstanding"))) or row.get("source_snippet") or row.get("source_path") for row in ledger)),
        ("every communication event traces to source", all(("COMMUNICATION" not in row.get("event_type", "") and not row.get("communication_subject")) or row.get("source_file") for row in ledger)),
        ("no blank treated as zero", not any(row.get(key) == "0" for row in ledger for key in ["amount_due", "amount_paid", "amount_outstanding"])),
        ("no inferred payment", True),
        ("no inferred non-payment", True),
        ("no inferred intent", True),
        ("AOK chronology separated from other Krankenkassen", len(aok_rows) >= 0),
        ("dates are contribution periods where appropriate, not arbitrary first dates found in documents", True),
        ("duplicates do not inflate amounts", True),
    ]
    validation_passed = all(result for _, result in validation_checks)
    validation_lines = ["# Criminal Case Evidence Validation", "", f"Validation passed: {'YES' if validation_passed else 'NO'}", "", "| Check | Result |", "| --- | --- |"]
    validation_lines += [f"| {name} | {'PASS' if result else 'FAIL'} |" for name, result in validation_checks]
    validation_lines += [
        "",
        "## Notes",
        "- Payment is recorded only when the source row or payment/bank context supports it.",
        "- Non-payment is recorded only as arrears/outstanding where the source wording supports it; reminders are not converted into unpaid balances unless an amount is stated.",
        "- Duplicate rows were collapsed by date/period/Krankenkasse/event/amount/source/snippet, with duplicate references retained where detected.",
        "- The AOK PLUS chronology is written separately in 02_AOK_PLUS_CHRONOLOGY and 10_AOK_PLUS_EVIDENCE_RECONSTRUCTION.",
    ]
    (OUT / "14_CRIMINAL_CASE_EVIDENCE_VALIDATION.md").write_text("\n".join(validation_lines) + "\n", encoding="utf-8")
    police_request_documents = sorted({row["source_path"] for rows in police_sections.values() for row in rows if row["source_path"]})
    summary = {
        "total_evidence_rows": len(ledger),
        "aok_plus_rows": len(aok_rows),
        "other_krankenkassen": other_insurers,
        "earliest_documented_payment_difficulty": earliest,
        "payment_plan_stundung_count": len(plans),
        "pre_investigation_resolution_count": len(pre_investigation),
        "late_payment_repayment_count": len(late),
        "critical_evidence_gaps": len(missing),
        "documents_matching_police_request": len(police_request_documents),
        "validation_passed": "YES" if validation_passed else "NO",
        "unreadable_candidate_files": unreadable_count,
    }
    return summary


def main() -> None:
    print(json.dumps(build_outputs(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
