#!/usr/bin/env python3
"""Reconstruct monthly accounting cash flow from accounting inbox documents."""

from __future__ import annotations

import csv
import email
import hashlib
import html
import re
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from email import policy
from email.message import Message
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_ROOT = REPO_ROOT / "00_INBOX - Входящи - Eingang" / "Accounting"
REPORT_ROOT = REPO_ROOT / "08_Reports - Доклади - Berichte" / "Accounting_Cash_Flow"
ENRICO_MONTHLY = REPO_ROOT / "08_Reports - Доклади - Berichte" / "Enrico_Deductions" / "enrico_deductions_monthly.csv"
LOCAL_PACKAGES = REPO_ROOT / ".python_packages"
PDF_PASSWORD = "10001"
SUPPORTED_EXTENSIONS = {".pdf", ".zip", ".rar", ".txt", ".csv", ".xlsx", ".eml"}
PERIOD_START = (2024, 1)
PERIOD_END = (2025, 6)

if LOCAL_PACKAGES.exists():
    import sys

    sys.path.insert(0, str(LOCAL_PACKAGES))


EMPLOYEE_HEADERS = ["month", "employee_count", "employee_names", "source_documents", "confidence"]
PAYROLL_HEADERS = ["month", "total_brutto", "total_netto", "source_documents", "confidence"]
HEALTH_HEADERS = [
    "month",
    "insurance_name",
    "amount_due",
    "amount_paid",
    "unpaid_balance",
    "due_date",
    "late_fees",
    "source_documents",
    "confidence",
]
TAX_HEADERS = [
    "month",
    "creditor",
    "tax_type",
    "amount_due",
    "amount_paid",
    "unpaid_balance",
    "due_date",
    "source_documents",
    "confidence",
]
OPERATING_HEADERS = [
    "month",
    "category",
    "creditor",
    "amount_due",
    "amount_paid",
    "unpaid_balance",
    "source_documents",
    "confidence",
]
MONTHLY_HEADERS = [
    "month",
    "enrico_deductions_total_if_available",
    "payroll_brutto",
    "payroll_netto",
    "health_insurance_due",
    "health_insurance_paid",
    "health_insurance_unpaid",
    "tax_due",
    "tax_paid",
    "tax_unpaid",
    "operating_costs_due",
    "operating_costs_paid",
    "operating_costs_unpaid",
    "total_monthly_obligations",
    "total_paid",
    "total_unpaid",
    "first_visible_financial_pressure_yes_no",
    "notes",
    "confidence",
]
MISSING_HEADERS = ["month", "has_accounting_document", "notes"]
DUPLICATE_HEADERS = ["content_hash", "kept_source_file", "duplicate_source_file", "reason"]

HEALTH_INSURERS = ["AOK", "TK", "KKH", "Barmer", "DAK", "BKK", "IKK", "VIACTIV"]
TAX_TYPES = ["Gewerbesteuer", "Umsatzsteuer", "Lohnsteuer", "Einkommensteuer"]
OPERATING_KEYWORDS = {
    "fuel": ["fuel", "kraftstoff", "diesel", "benzin", "tank"],
    "vehicle costs": ["fahrzeug", "vehicle", "kfz", "auto"],
    "repairs": ["reparatur", "werkstatt", "repair"],
    "leasing": ["leasing"],
    "insurance": ["versicherung", "insurance"],
    "rent": ["miete", "rent"],
    "phone": ["telefon", "phone", "mobilfunk"],
    "accounting fees": ["buchhaltung", "steuerberater", "accounting"],
    "equipment": ["ausstattung", "equipment", "scanner", "gerät", "geraet"],
}


@dataclass
class SourceDocument:
    path: Path
    display_path: str
    source_container: str = ""
    category_hint: str = ""


class ProcessingLog:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.stats: dict[str, int] = defaultdict(int)

    def add(self, message: str) -> None:
        self.lines.append(f"{datetime.now().isoformat(timespec='seconds')} {message}")

    def write(self, path: Path) -> None:
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


def month_range() -> list[str]:
    months: list[str] = []
    year, month = PERIOD_START
    while (year, month) <= PERIOD_END:
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    return months


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(value: str) -> str:
    replacements = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}
    for source, replacement in replacements.items():
        value = value.replace(source, replacement)
    return value.lower()


def parse_decimal(value: str) -> Decimal | None:
    value = re.sub(r"[^\d,.\-]", "", value.strip())
    if not value:
        return None
    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        value = value.replace(".", "").replace(",", ".")
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def fmt(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{value.quantize(Decimal('0.01'))}"


def amount_to_decimal(value: str) -> Decimal:
    return parse_decimal(value) or Decimal("0")


def money_pattern() -> str:
    return r"-?\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})|-?\d+(?:[,.]\d{2})"


def first_match(patterns: Iterable[str], text: str, flags: int = re.IGNORECASE | re.DOTALL) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()
    return ""


def extract_month(text: str, display_path: str) -> str:
    combined = f"{display_path}\n{text}"
    patterns = [
        r"\b(20\d{2})[-_/ .](0?[1-9]|1[0-2])\b",
        r"\b(0?[1-9]|1[0-2])[-_/ .](20\d{2})\b",
        r"\b(?:Januar|Jan)\s*(20\d{2})\b",
        r"\b(?:Februar|Feb)\s*(20\d{2})\b",
        r"\b(?:März|Maerz|Mar)\s*(20\d{2})\b",
        r"\b(?:April|Apr)\s*(20\d{2})\b",
        r"\b(?:Mai)\s*(20\d{2})\b",
        r"\b(?:Juni|Jun)\s*(20\d{2})\b",
        r"\b(?:Juli|Jul)\s*(20\d{2})\b",
        r"\b(?:August|Aug)\s*(20\d{2})\b",
        r"\b(?:September|Sep)\s*(20\d{2})\b",
        r"\b(?:Oktober|Oct|Okt)\s*(20\d{2})\b",
        r"\b(?:November|Nov)\s*(20\d{2})\b",
        r"\b(?:Dezember|Dec|Dez)\s*(20\d{2})\b",
    ]
    for index, pattern in enumerate(patterns):
        match = re.search(pattern, combined, re.IGNORECASE)
        if not match:
            continue
        if index == 0:
            return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}"
        if index == 1:
            return f"{int(match.group(2)):04d}-{int(match.group(1)):02d}"
        return f"{int(match.group(1)):04d}-{index - 1:02d}"
    return ""


def category_hint(path: Path) -> str:
    parts = " ".join(path.parts)
    text = normalize(parts)
    if any(term in text for term in ["lohn", "payroll", "entgelt"]):
        return "payroll"
    if any(term in text for term in ["krankenkasse", "health", "aok", "barmer", "kkh"]):
        return "health"
    if any(term in text for term in ["finanzamt", "steuer", "gewerbesteuer", "chemnitz"]):
        return "tax"
    if any(term in text for term in ["kosten", "fuel", "kraftstoff", "fahrzeug", "leasing"]):
        return "operating"
    return ""


def scan_inputs(log: ProcessingLog) -> list[SourceDocument]:
    docs: list[SourceDocument] = []
    if not INPUT_ROOT.exists():
        log.add(f"Input folder does not exist: {repo_relative(INPUT_ROOT)}")
        return docs
    for path in INPUT_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            docs.append(SourceDocument(path, repo_relative(path), category_hint(path)))
            log.add(f"Scanned file: {repo_relative(path)}")
    log.stats["scanned_files"] = len(docs)
    return docs


def safe_extract_path(base: Path, name: str) -> Path | None:
    target = (base / name).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        return None
    return target


def extract_zip(source: SourceDocument, temp_root: Path, log: ProcessingLog) -> list[SourceDocument]:
    out: list[SourceDocument] = []
    target_root = temp_root / "zip" / hashlib.sha1(str(source.path).encode("utf-8")).hexdigest()
    target_root.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(source.path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                target = safe_extract_path(target_root, member.filename)
                if target is None:
                    log.add(f"Unsafe ZIP member skipped: {member.filename}")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                if target.suffix.lower() in SUPPORTED_EXTENSIONS:
                    out.append(SourceDocument(target, f"{source.display_path}::{member.filename}", source.display_path, source.category_hint))
        log.add(f"Extracted {len(out)} supported files from ZIP: {source.display_path}")
    except Exception as exc:
        log.add(f"ZIP_READ_ERROR {source.display_path}: {exc}")
    return out


def extract_rar(source: SourceDocument, temp_root: Path, log: ProcessingLog) -> list[SourceDocument]:
    try:
        import rarfile  # type: ignore
    except ImportError:
        log.add(f"RAR skipped, dependency missing: {source.display_path}")
        return []
    out: list[SourceDocument] = []
    target_root = temp_root / "rar" / hashlib.sha1(str(source.path).encode("utf-8")).hexdigest()
    target_root.mkdir(parents=True, exist_ok=True)
    try:
        with rarfile.RarFile(source.path) as archive:
            for member in archive.infolist():
                if member.isdir():
                    continue
                target = safe_extract_path(target_root, member.filename)
                if target is None:
                    log.add(f"Unsafe RAR member skipped: {member.filename}")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                if target.suffix.lower() in SUPPORTED_EXTENSIONS:
                    out.append(SourceDocument(target, f"{source.display_path}::{member.filename}", source.display_path, source.category_hint))
        log.add(f"Extracted {len(out)} supported files from RAR: {source.display_path}")
    except Exception as exc:
        log.add(f"RAR_READ_ERROR {source.display_path}: {exc}")
    return out


def extract_eml(source: SourceDocument, temp_root: Path, log: ProcessingLog) -> tuple[str, list[SourceDocument]]:
    try:
        with source.path.open("rb") as handle:
            message = email.message_from_binary_file(handle, policy=policy.default)
    except Exception as exc:
        log.add(f"EML_READ_ERROR {source.display_path}: {exc}")
        return "", []
    body_parts: list[str] = [
        f"email_date: {message.get('date', '')}",
        f"sender: {message.get('from', '')}",
        f"recipient: {message.get('to', '')}",
        f"subject: {message.get('subject', '')}",
    ]
    attachments: list[SourceDocument] = []
    target_root = temp_root / "eml" / hashlib.sha1(str(source.path).encode("utf-8")).hexdigest()
    target_root.mkdir(parents=True, exist_ok=True)
    if message.is_multipart():
        for index, part in enumerate(message.walk(), start=1):
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename() or f"attachment-{index}"
                payload = part.get_payload(decode=True)
                if payload is None:
                    continue
                target = safe_extract_path(target_root, filename)
                if target is None:
                    log.add(f"Unsafe EML attachment skipped: {filename}")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
                if target.suffix.lower() in SUPPORTED_EXTENSIONS:
                    attachments.append(SourceDocument(target, f"{source.display_path}::{filename}", source.display_path, source.category_hint))
            elif part.get_content_type() in {"text/plain", "text/html"}:
                try:
                    body_parts.append(str(part.get_content()))
                except Exception:
                    pass
    else:
        try:
            body_parts.append(str(message.get_content()))
        except Exception:
            pass
    log.add(f"Read EML {source.display_path} with {len(attachments)} supported attachments.")
    return "\n".join(body_parts), attachments


def expand_sources(initial: list[SourceDocument], temp_root: Path, log: ProcessingLog) -> list[SourceDocument]:
    expanded: list[SourceDocument] = []
    queue = list(initial)
    seen: set[Path] = set()
    while queue:
        source = queue.pop(0)
        resolved = source.path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        suffix = source.path.suffix.lower()
        if suffix == ".zip":
            queue.extend(extract_zip(source, temp_root, log))
            expanded.append(source)
        elif suffix == ".rar":
            queue.extend(extract_rar(source, temp_root, log))
            expanded.append(source)
        elif suffix == ".eml":
            _, attachments = extract_eml(source, temp_root, log)
            queue.extend(attachments)
            expanded.append(source)
        else:
            expanded.append(source)
    log.stats["expanded_files"] = len(expanded)
    return expanded


def read_pdf(path: Path, log: ProcessingLog) -> tuple[str, str]:
    errors: list[str] = []
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        if reader.is_encrypted:
            result = reader.decrypt(PDF_PASSWORD)
            log.add(f"PDF decrypt attempted for {repo_relative(path)} with result {result}")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            return text, "HIGH"
        errors.append("pypdf returned no text")
    except Exception as exc:
        errors.append(f"pypdf failed: {exc}")
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(str(path), password=PDF_PASSWORD) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if text.strip():
            return text, "HIGH"
        errors.append("pdfplumber returned no text")
    except Exception as exc:
        errors.append(f"pdfplumber failed: {exc}")
    log.add(f"PDF_READ_ERROR {repo_relative(path)} :: {' | '.join(errors)}")
    return "", "LOW"


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def read_xlsx_text(path: Path, log: ProcessingLog) -> tuple[str, str]:
    try:
        import openpyxl  # type: ignore

        workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
        values: list[str] = []
        for sheet in workbook.worksheets:
            values.append(f"Sheet: {sheet.title}")
            for row in sheet.iter_rows(values_only=True):
                values.append(" | ".join("" if cell is None else str(cell) for cell in row))
        return "\n".join(values), "HIGH"
    except Exception as exc:
        log.add(f"openpyxl unavailable or failed for {repo_relative(path)}: {exc}")
    try:
        with zipfile.ZipFile(path) as archive:
            shared: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                shared = ["".join(node.itertext()) for node in root]
            values = []
            for name in archive.namelist():
                if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                    root = ET.fromstring(archive.read(name))
                    for cell in root.iter():
                        if cell.tag.endswith("}c"):
                            cell_type = cell.attrib.get("t")
                            v = next((child for child in cell if child.tag.endswith("}v")), None)
                            if v is not None and v.text:
                                if cell_type == "s" and v.text.isdigit() and int(v.text) < len(shared):
                                    values.append(shared[int(v.text)])
                                else:
                                    values.append(v.text)
            return "\n".join(values), "LOW"
    except Exception as exc:
        log.add(f"XLSX_READ_ERROR {repo_relative(path)}: {exc}")
        return "", "LOW"


def read_source(source: SourceDocument, temp_root: Path, log: ProcessingLog) -> tuple[str, str]:
    suffix = source.path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf(source.path, log)
    if suffix in {".txt", ".csv"}:
        return read_text(source.path), "MEDIUM"
    if suffix == ".xlsx":
        return read_xlsx_text(source.path, log)
    if suffix == ".eml":
        body, _ = extract_eml(source, temp_root, log)
        return body, "MEDIUM" if body else "LOW"
    return "", "LOW"


def deduplicate(sources: list[SourceDocument], log: ProcessingLog) -> tuple[list[SourceDocument], list[dict[str, str]]]:
    seen: dict[str, SourceDocument] = {}
    unique: list[SourceDocument] = []
    duplicates: list[dict[str, str]] = []
    for source in sources:
        if source.path.suffix.lower() in {".zip", ".rar"}:
            continue
        try:
            digest = sha256_file(source.path)
        except OSError as exc:
            log.add(f"HASH_ERROR {source.display_path}: {exc}")
            continue
        if digest in seen:
            duplicates.append(
                {
                    "content_hash": digest,
                    "kept_source_file": seen[digest].display_path,
                    "duplicate_source_file": source.display_path,
                    "reason": "Same file hash.",
                }
            )
            continue
        seen[digest] = source
        unique.append(source)
    return unique, duplicates


def extract_amount_near(text: str, terms: Iterable[str]) -> Decimal | None:
    for term in terms:
        pattern = rf"{term}.{{0,120}}?({money_pattern()})\s*(?:EUR|€)?"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return parse_decimal(match.group(1))
    return None


def extract_employee_names(text: str) -> list[str]:
    names: set[str] = set()
    for pattern in [
        r"(?:Arbeitnehmer|Mitarbeiter|Beschäftigte?r?|Beschaeftigte?r?)\s*[:#]?\s*([A-ZÄÖÜ][A-Za-zÄÖÜäöüß' -]{3,})",
        r"\b([A-ZÄÖÜ][A-Za-zÄÖÜäöüß' -]+,\s*[A-ZÄÖÜ][A-Za-zÄÖÜäöüß' -]+)\b",
    ]:
        for match in re.finditer(pattern, text):
            name = re.sub(r"\s+", " ", match.group(1)).strip(" ,-")
            if len(name) <= 80:
                names.add(name)
    return sorted(names)


def extract_rows(source: SourceDocument, text: str, confidence: str) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    month = extract_month(text, source.display_path)
    haystack = normalize(f"{source.display_path}\n{source.category_hint}\n{text}")
    src = source.display_path
    employee_rows: list[dict[str, str]] = []
    payroll_rows: list[dict[str, str]] = []
    health_rows: list[dict[str, str]] = []
    tax_rows: list[dict[str, str]] = []
    operating_rows: list[dict[str, str]] = []

    if any(term in haystack for term in ["lohn", "entgelt", "brutto", "netto", "arbeitnehmer", "mitarbeiter"]):
        names = extract_employee_names(text)
        employee_rows.append(
            {
                "month": month,
                "employee_count": str(len(names)) if names else "",
                "employee_names": "; ".join(names),
                "source_documents": src,
                "confidence": "MEDIUM" if names else "LOW",
            }
        )
        brutto = extract_amount_near(text, ["Gesamtbrutto", "Bruttoarbeitslohn", "Brutto", "total_brutto"])
        netto = extract_amount_near(text, ["Auszahlungsbetrag", "Nettoverdienst", "Netto", "total_netto"])
        if brutto is not None or netto is not None:
            payroll_rows.append(
                {
                    "month": month,
                    "total_brutto": fmt(brutto),
                    "total_netto": fmt(netto),
                    "source_documents": src,
                    "confidence": confidence if brutto is not None or netto is not None else "LOW",
                }
            )

    if any(term.lower() in haystack for term in [name.lower() for name in HEALTH_INSURERS]) or "krankenkasse" in haystack:
        insurer = next((name for name in HEALTH_INSURERS if name.lower() in haystack), "other")
        due = extract_amount_near(text, ["fällig", "faellig", "Soll", "Beitrag", "amount due", "Gesamt"])
        paid = extract_amount_near(text, ["bezahlt", "gezahlt", "payment", "paid", "Ist"])
        unpaid = extract_amount_near(text, ["offen", "rückstand", "rueckstand", "unpaid", "balance"])
        late = extract_amount_near(text, ["Säumniszuschlag", "Saeumniszuschlag", "late fee"])
        due_date = first_match([r"(?:fällig|faellig|due date)\D{0,40}(\d{1,2}\.\d{1,2}\.\d{2,4})"], text)
        health_rows.append(
            {
                "month": month,
                "insurance_name": insurer,
                "amount_due": fmt(due),
                "amount_paid": fmt(paid),
                "unpaid_balance": fmt(unpaid),
                "due_date": due_date,
                "late_fees": fmt(late),
                "source_documents": src,
                "confidence": confidence if any(v is not None for v in [due, paid, unpaid, late]) else "LOW",
            }
        )

    if any(term in haystack for term in ["finanzamt", "stadt chemnitz", "gewerbesteuer", "umsatzsteuer", "lohnsteuer", "einkommensteuer", "steuer"]):
        creditor = "Finanzamt" if "finanzamt" in haystack else "Stadt Chemnitz" if "stadt chemnitz" in haystack or "gewerbesteuer" in haystack else ""
        tax_type = next((term for term in TAX_TYPES if normalize(term) in haystack), "other public liability")
        due = extract_amount_near(text, ["fällig", "faellig", "Steuer", "Soll", "amount due", "Gesamt"])
        paid = extract_amount_near(text, ["bezahlt", "gezahlt", "payment", "paid", "Ist"])
        unpaid = extract_amount_near(text, ["offen", "rückstand", "rueckstand", "unpaid", "balance"])
        due_date = first_match([r"(?:fällig|faellig|due date)\D{0,40}(\d{1,2}\.\d{1,2}\.\d{2,4})"], text)
        tax_rows.append(
            {
                "month": month,
                "creditor": creditor,
                "tax_type": tax_type,
                "amount_due": fmt(due),
                "amount_paid": fmt(paid),
                "unpaid_balance": fmt(unpaid),
                "due_date": due_date,
                "source_documents": src,
                "confidence": confidence if any(v is not None for v in [due, paid, unpaid]) else "LOW",
            }
        )

    for category, terms in OPERATING_KEYWORDS.items():
        if any(term in haystack for term in terms):
            due = extract_amount_near(text, ["Betrag", "Rechnung", "Kosten", "amount due", "Gesamt"])
            paid = extract_amount_near(text, ["bezahlt", "gezahlt", "paid"])
            unpaid = extract_amount_near(text, ["offen", "unpaid", "balance"])
            creditor = first_match([r"(?:Kreditor|Lieferant|Gläubiger|Glaeubiger)\s*[:#]?\s*([^\n\r]+)"], text)
            operating_rows.append(
                {
                    "month": month,
                    "category": category,
                    "creditor": creditor,
                    "amount_due": fmt(due),
                    "amount_paid": fmt(paid),
                    "unpaid_balance": fmt(unpaid),
                    "source_documents": src,
                    "confidence": confidence if any(v is not None for v in [due, paid, unpaid]) else "LOW",
                }
            )
            break

    return employee_rows, payroll_rows, health_rows, tax_rows, operating_rows


def write_csv(path: Path, headers: list[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def column_name(index: int) -> str:
    result = ""
    while index:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def write_xlsx(path: Path, headers: list[str], rows: list[dict[str, str]], sheet_name: str) -> None:
    values = [headers] + [[str(row.get(header, "")) for header in headers] for row in rows]
    sheet_rows: list[str] = []
    for row_index, row_values in enumerate(values, start=1):
        cells = []
        for col_index, value in enumerate(row_values, start=1):
            ref = f"{column_name(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(value)}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(sheet_rows) + "</sheetData></worksheet>"
    workbook = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="' + html.escape(sheet_name[:31]) + '" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    content_types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)


def sum_rows(rows: list[dict[str, str]], month: str, field: str) -> Decimal:
    return sum((amount_to_decimal(row.get(field, "")) for row in rows if row.get("month") == month), Decimal("0"))


def read_enrico_totals() -> dict[str, str]:
    if not ENRICO_MONTHLY.exists():
        return {}
    try:
        with ENRICO_MONTHLY.open("r", encoding="utf-8-sig", newline="") as handle:
            return {
                row["month"]: row.get("total_deductions_negative") or row.get("total_deductions") or ""
                for row in csv.DictReader(handle)
            }
    except Exception:
        return {}


def build_monthly(employee_rows: list[dict[str, str]], payroll_rows: list[dict[str, str]], health_rows: list[dict[str, str]], tax_rows: list[dict[str, str]], operating_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], str]:
    enrico = read_enrico_totals()
    monthly: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    first_unpaid_health = ""
    first_pressure_found = False
    for month in month_range():
        payroll_brutto = sum_rows(payroll_rows, month, "total_brutto")
        payroll_netto = sum_rows(payroll_rows, month, "total_netto")
        health_due = sum_rows(health_rows, month, "amount_due")
        health_paid = sum_rows(health_rows, month, "amount_paid")
        health_unpaid = sum_rows(health_rows, month, "unpaid_balance")
        tax_due = sum_rows(tax_rows, month, "amount_due")
        tax_paid = sum_rows(tax_rows, month, "amount_paid")
        tax_unpaid = sum_rows(tax_rows, month, "unpaid_balance")
        op_due = sum_rows(operating_rows, month, "amount_due")
        op_paid = sum_rows(operating_rows, month, "amount_paid")
        op_unpaid = sum_rows(operating_rows, month, "unpaid_balance")
        has_docs = any(row.get("month") == month for row in employee_rows + payroll_rows + health_rows + tax_rows + operating_rows)
        if not has_docs:
            missing.append({"month": month, "has_accounting_document": "NO", "notes": "No accounting document data extracted for this month."})
        if health_unpaid > 0 and not first_unpaid_health:
            first_unpaid_health = month
        total_obligations = payroll_brutto + health_due + tax_due + op_due
        total_paid = payroll_netto + health_paid + tax_paid + op_paid
        total_unpaid = health_unpaid + tax_unpaid + op_unpaid
        pressure = total_unpaid > 0
        first_pressure = "YES" if pressure and not first_pressure_found else "NO"
        if pressure:
            first_pressure_found = True
        confidence = "MEDIUM" if has_docs else "LOW"
        monthly.append(
            {
                "month": month,
                "enrico_deductions_total_if_available": enrico.get(month, ""),
                "payroll_brutto": fmt(payroll_brutto) if payroll_brutto else "",
                "payroll_netto": fmt(payroll_netto) if payroll_netto else "",
                "health_insurance_due": fmt(health_due) if health_due else "",
                "health_insurance_paid": fmt(health_paid) if health_paid else "",
                "health_insurance_unpaid": fmt(health_unpaid) if health_unpaid else "",
                "tax_due": fmt(tax_due) if tax_due else "",
                "tax_paid": fmt(tax_paid) if tax_paid else "",
                "tax_unpaid": fmt(tax_unpaid) if tax_unpaid else "",
                "operating_costs_due": fmt(op_due) if op_due else "",
                "operating_costs_paid": fmt(op_paid) if op_paid else "",
                "operating_costs_unpaid": fmt(op_unpaid) if op_unpaid else "",
                "total_monthly_obligations": fmt(total_obligations) if total_obligations else "",
                "total_paid": fmt(total_paid) if total_paid else "",
                "total_unpaid": fmt(total_unpaid) if total_unpaid else "",
                "first_visible_financial_pressure_yes_no": first_pressure,
                "notes": "" if has_docs else "No extracted accounting values for this month.",
                "confidence": confidence,
            }
        )
    return monthly, missing, first_unpaid_health


def markdown_table(headers: list[str], rows: list[dict[str, str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")).replace("\n", " ") for header in headers) + " |")
    return "\n".join(lines)


def write_report(monthly: list[dict[str, str]], missing: list[dict[str, str]], first_unpaid_health: str, documents_used: list[str]) -> None:
    missing_lines = "\n".join(f"- {row['month']}: {row['notes']}" for row in missing) or "- None detected"
    docs = "\n".join(f"- {doc}" for doc in documents_used) or "- No accounting source documents produced extractable rows."
    report = f"""# Accounting Cash Flow Reconstruction

## Period Analyzed

January 2024 through June 2025.

## Total Payroll by Month

{markdown_table(['month', 'payroll_brutto', 'payroll_netto'], monthly)}

## Total Health Insurance Liabilities by Month

{markdown_table(['month', 'health_insurance_due', 'health_insurance_paid', 'health_insurance_unpaid'], monthly)}

## Unpaid Health Insurance Amounts by Month

{markdown_table(['month', 'health_insurance_unpaid'], monthly)}

## Tax Liabilities by Month

{markdown_table(['month', 'tax_due', 'tax_paid', 'tax_unpaid'], monthly)}

## First Month With Unpaid Health Insurance

{first_unpaid_health or 'Not detected'}

## First Month With Growing Arrears

Not detected automatically. Review unpaid balance trends after source data is available.

## Months With Missing Data

{missing_lines}

## Documents Used

{docs}

## Limitations

- OCR is not implemented.
- Empty values mean no reliable value was extracted.
- Password-protected PDFs are attempted with password `10001`.
- Complex accounting spreadsheets may require manual review.

## Next Documents Needed

- Monthly payroll summaries for every month from 2024-01 to 2025-06.
- Krankenkassen statements showing due, paid, and unpaid amounts.
- Finanzamt and Stadt Chemnitz notices or open-liability tables.
- Bankkonto payment proofs and cash payment confirmations where available.
"""
    (REPORT_ROOT / "ACCOUNTING_CASH_FLOW_RECONSTRUCTION.md").write_text(report, encoding="utf-8")


def write_output_readme() -> None:
    text = """# Accounting Cash Flow Outputs

Generated by `analyze_accounting_cash_flow.py`.

The files in this folder reconstruct employee, payroll, health insurance, tax, operating-cost, and monthly cash-flow timelines from accounting inbox documents.

Empty values mean the analyzer could not reliably extract a number.
"""
    (REPORT_ROOT / "README.md").write_text(text, encoding="utf-8")


def analyze() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], str, ProcessingLog]:
    log = ProcessingLog()
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    employee_rows: list[dict[str, str]] = []
    payroll_rows: list[dict[str, str]] = []
    health_rows: list[dict[str, str]] = []
    tax_rows: list[dict[str, str]] = []
    operating_rows: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="accounting_cash_flow_") as temp_dir:
        sources = expand_sources(scan_inputs(log), Path(temp_dir), log)
        unique, duplicates = deduplicate(sources, log)
        for source in unique:
            text, confidence = read_source(source, Path(temp_dir), log)
            if not text.strip():
                log.add(f"Unreadable or empty text: {source.display_path}")
                continue
            extracted = extract_rows(source, text, confidence)
            employee_rows.extend(extracted[0])
            payroll_rows.extend(extracted[1])
            health_rows.extend(extracted[2])
            tax_rows.extend(extracted[3])
            operating_rows.extend(extracted[4])
            log.add(f"Processed file: {source.display_path}")
    monthly, missing, first_unpaid_health = build_monthly(employee_rows, payroll_rows, health_rows, tax_rows, operating_rows)
    log.stats["employee_rows"] = len(employee_rows)
    log.stats["payroll_rows"] = len(payroll_rows)
    log.stats["health_rows"] = len(health_rows)
    log.stats["tax_rows"] = len(tax_rows)
    log.stats["operating_rows"] = len(operating_rows)
    log.stats["missing_months"] = len(missing)
    return employee_rows, payroll_rows, health_rows, tax_rows, operating_rows, monthly, missing, duplicates, first_unpaid_health, log


def main() -> int:
    employee_rows, payroll_rows, health_rows, tax_rows, operating_rows, monthly, missing, duplicates, first_unpaid_health, log = analyze()
    outputs = [
        ("employee_timeline", EMPLOYEE_HEADERS, employee_rows, "Employees"),
        ("payroll_timeline", PAYROLL_HEADERS, payroll_rows, "Payroll"),
        ("health_insurance_timeline", HEALTH_HEADERS, health_rows, "Health"),
        ("tax_timeline", TAX_HEADERS, tax_rows, "Taxes"),
        ("operating_costs_timeline", OPERATING_HEADERS, operating_rows, "Operating"),
        ("monthly_cash_flow_reconstruction", MONTHLY_HEADERS, monthly, "Monthly"),
    ]
    for stem, headers, rows, sheet in outputs:
        write_csv(REPORT_ROOT / f"{stem}.csv", headers, rows)
        write_xlsx(REPORT_ROOT / f"{stem}.xlsx", headers, rows, sheet)
    write_csv(REPORT_ROOT / "missing_accounting_months.csv", MISSING_HEADERS, missing)
    write_csv(REPORT_ROOT / "duplicate_accounting_documents.csv", DUPLICATE_HEADERS, duplicates)
    documents_used = sorted(
        {
            row.get("source_documents", "")
            for row in employee_rows + payroll_rows + health_rows + tax_rows + operating_rows
            if row.get("source_documents")
        }
    )
    write_report(monthly, missing, first_unpaid_health, documents_used)
    write_output_readme()
    log.write(REPORT_ROOT / "processing_log.txt")
    print(f"Scanned files: {log.stats.get('scanned_files', 0)}")
    print(f"Extracted employee rows: {len(employee_rows)}")
    print(f"Extracted payroll rows: {len(payroll_rows)}")
    print(f"Extracted health insurance rows: {len(health_rows)}")
    print(f"Extracted tax rows: {len(tax_rows)}")
    print(f"Extracted operating cost rows: {len(operating_rows)}")
    print(f"First unpaid health insurance month: {first_unpaid_health or 'Not detected'}")
    print(f"Missing months: {len(missing)}")
    print(f"Output folder: {repo_relative(REPORT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
