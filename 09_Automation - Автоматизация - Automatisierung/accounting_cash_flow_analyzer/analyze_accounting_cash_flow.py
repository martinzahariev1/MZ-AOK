#!/usr/bin/env python3
"""Robust accounting cash-flow reconstruction with full file audit."""

from __future__ import annotations

import csv
import email
import hashlib
import html
import re
import shutil
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from email import policy
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_ROOT = REPO_ROOT / "00_INBOX - Входящи - Eingang" / "Accounting_Organized"
REPORT_ROOT = REPO_ROOT / "08_Reports - Доклади - Berichte" / "Accounting_Cash_Flow"
ENRICO_REPORT_DIR = REPO_ROOT / "08_Reports - Доклади - Berichte" / "Enrico_Deductions"
ENRICO_MONTHLY = ENRICO_REPORT_DIR / "enrico_deductions_monthly.csv"
ENRICO_DETAIL = ENRICO_REPORT_DIR / "enrico_deductions_detailed.csv"
LOCAL_PACKAGES = REPO_ROOT / ".python_packages"
PDF_PASSWORD = "10001"
PERIOD_START = (2024, 1)
PERIOD_END = (2025, 6)

if LOCAL_PACKAGES.exists():
    import sys

    sys.path.insert(0, str(LOCAL_PACKAGES))

ARCHIVE_EXTENSIONS = {".zip", ".rar"}
TEXT_EXTENSIONS = {".pdf", ".txt", ".csv", ".xlsx", ".docx", ".eml"}
SUPPORTED_EXTENSIONS = ARCHIVE_EXTENSIONS | TEXT_EXTENSIONS

FOCUSED_CATEGORY_PREFIXES = {
    "02_Payroll",
    "03_Employee_Payslips",
    "04_Health_Insurance",
    "05_Taxes",
    "06_Bank_Payments",
    "08_Operating_Costs",
    "09_Enrico_Forwarded",
    "10_BWA_Reports",
    "11_Contribution_Lists",
    "12_Liability_Overview",
}
SKIPPED_CATEGORY_REASONS = {
    "01_Accountant_Emails": "Skipped accountant-email category for financial extraction; attachments already categorized separately when organizer found them.",
    "07_Cash_Payments": "Skipped cash-payment category because this run only processes focused financial extraction categories.",
    "13_Unknown_To_Review": "Skipped Unknown_To_Review category; manual review is required before financial extraction.",
    "14_Duplicates": "Skipped Duplicates category; original or kept copy should be processed instead.",
}
CATEGORY_HINTS = {
    "02_Payroll": "payroll",
    "03_Employee_Payslips": "payroll",
    "04_Health_Insurance": "health",
    "05_Taxes": "tax",
    "06_Bank_Payments": "bank payments",
    "08_Operating_Costs": "operating",
    "09_Enrico_Forwarded": "enrico cross-check",
    "10_BWA_Reports": "bwa report",
    "11_Contribution_Lists": "contribution list",
    "12_Liability_Overview": "liability overview",
}

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
ENRICO_HEADERS = [
    "month",
    "document_number",
    "document_type",
    "document_date",
    "amount",
    "source_file",
    "already_in_enrico_report",
    "action_needed",
]
MONTHLY_HEADERS = [
    "month",
    "enrico_deductions_total_if_available",
    "revenue_if_available",
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
    "notes",
    "confidence",
]
MISSING_HEADERS = ["month", "has_accounting_document", "notes"]
DUPLICATE_HEADERS = ["content_hash", "kept_source_file", "duplicate_source_file", "reason"]
UNPROCESSED_HEADERS = [
    "filename",
    "full_path",
    "file_type",
    "detected_document_type",
    "reason_not_processed",
    "password_attempted",
    "password_success",
    "text_extracted",
    "structured_rows_extracted",
    "missing_required_fields",
    "recommended_next_action",
    "confidence",
    "status",
]

HEALTH_INSURERS = ["AOK Plus", "AOK", "TK", "KKH", "Barmer", "DAK", "BKK", "IKK", "VIACTIV", "Vivida BKK"]
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
    "car rental": ["mietwagen", "autovermietung", "car rental"],
}
ENRICO_TERMS = [
    "enrico weissflog",
    "enrico weißflog",
    "sachsenpower",
    "gutschrift",
    "sendungsverlust",
    "abschlag coincident",
    "leistungsnachweis",
    "scannermiete",
]


@dataclass
class SourceFile:
    path: Path
    display_path: str
    source_container: str = ""
    category_hint: str = ""
    is_extracted: bool = False


@dataclass
class ReadResult:
    text: str
    confidence: str
    password_attempted: str = "NO"
    password_success: str = "NOT_APPLICABLE"
    reason: str = ""


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


def normalize(value: str) -> str:
    replacements = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value.lower()


def primary_category(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(INPUT_ROOT.resolve())
    except ValueError:
        return ""
    return relative.parts[0] if relative.parts else ""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    direct_patterns = [
        r"\b(20\d{2})[-_/ .](0?[1-9]|1[0-2])\b",
        r"\b(0?[1-9]|1[0-2])[-_/ .](20\d{2})\b",
    ]
    for index, pattern in enumerate(direct_patterns):
        match = re.search(pattern, combined, re.IGNORECASE)
        if match and index == 0:
            return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}"
        if match:
            return f"{int(match.group(2)):04d}-{int(match.group(1)):02d}"
    month_names = [
        ("januar|jan", 1),
        ("februar|feb", 2),
        ("märz|maerz|mar", 3),
        ("april|apr", 4),
        ("mai", 5),
        ("juni|jun", 6),
        ("juli|jul", 7),
        ("august|aug", 8),
        ("september|sep", 9),
        ("oktober|oct|okt", 10),
        ("november|nov", 11),
        ("dezember|dec|dez", 12),
    ]
    for pattern, month in month_names:
        match = re.search(rf"\b(?:{pattern})\s*(20\d{{2}})\b", combined, re.IGNORECASE)
        if match:
            return f"{int(match.group(1)):04d}-{month:02d}"
    return ""


def category_hint(path: Path) -> str:
    category = primary_category(path)
    if category in CATEGORY_HINTS:
        return CATEGORY_HINTS[category]
    text = normalize(" ".join(path.parts))
    if any(term in text for term in ["lohn", "payroll", "entgelt", "brutto_netto", "brutto-netto"]):
        return "payroll"
    if any(term in text for term in ["krankenkasse", "contribution", "aok", "barmer", "kkh", "hauptzollamt"]):
        return "health"
    if any(term in text for term in ["finanzamt", "steuer", "gewerbesteuer", "chemnitz"]):
        return "tax"
    if any(term in text for term in ["kosten", "fuel", "kraftstoff", "fahrzeug", "leasing"]):
        return "operating"
    return ""


def should_process_source(source: SourceFile) -> tuple[bool, str]:
    category = primary_category(source.path)
    if not category:
        return False, "Skipped root-level organizer audit file; not a source evidence document."
    for prefix in FOCUSED_CATEGORY_PREFIXES:
        if category.startswith(prefix):
            return True, ""
    for prefix, reason in SKIPPED_CATEGORY_REASONS.items():
        if category.startswith(prefix):
            return False, reason
    return False, f"Skipped non-focused organized category: {category}"


def detect_document_type(text: str, source: SourceFile) -> str:
    haystack = normalize(f"{source.display_path}\n{source.category_hint}\n{text}")
    if any(term in haystack for term in ["brutto", "netto", "lohn", "entgelt"]):
        return "Payroll"
    if any(name.lower() in haystack for name in HEALTH_INSURERS) or "krankenkasse" in haystack or "hauptzollamt" in haystack:
        return "Health Insurance"
    if any(term in haystack for term in ["finanzamt", "gewerbesteuer", "umsatzsteuer", "lohnsteuer", "einkommensteuer", "stadt chemnitz"]):
        return "Tax"
    if any(term in haystack for terms in OPERATING_KEYWORDS.values() for term in terms):
        return "Operating Cost"
    if any(term in haystack for term in ENRICO_TERMS):
        return "Enrico Cross-Check"
    return source.category_hint or "Unknown"


def scan_inputs(log: ProcessingLog, unprocessed: list[dict[str, str]]) -> list[SourceFile]:
    sources: list[SourceFile] = []
    if not INPUT_ROOT.exists():
        log.add(f"Input folder does not exist: {repo_relative(INPUT_ROOT)}")
        return sources
    scanned_count = 0
    skipped_count = 0
    for path in INPUT_ROOT.rglob("*"):
        if path.is_file():
            scanned_count += 1
            source = SourceFile(path=path, display_path=repo_relative(path), category_hint=category_hint(path))
            log.add(f"Scanned file: {repo_relative(path)}")
            should_process, reason = should_process_source(source)
            if should_process:
                sources.append(source)
            else:
                skipped_count += 1
                row = make_unprocessed(source, reason, source.category_hint)
                row["status"] = "SKIPPED_WITH_REASON"
                unprocessed.append(row)
                log.add(f"SKIPPED category file: {source.display_path} -- {reason}")
    log.stats["scanned_files"] = scanned_count
    log.stats["focused_input_files"] = len(sources)
    log.stats["skipped_before_processing"] = skipped_count
    return sources


def safe_extract_path(base: Path, member_name: str) -> Path | None:
    target = (base / member_name).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        return None
    return target


def make_unprocessed(source: SourceFile, reason: str, detected_type: str = "", read: ReadResult | None = None, structured: int = 0) -> dict[str, str]:
    read = read or ReadResult("", "LOW")
    return {
        "filename": source.path.name,
        "full_path": source.display_path,
        "file_type": source.path.suffix.lower(),
        "detected_document_type": detected_type,
        "reason_not_processed": reason,
        "password_attempted": read.password_attempted,
        "password_success": read.password_success,
        "text_extracted": "YES" if read.text.strip() else "NO",
        "structured_rows_extracted": str(structured),
        "missing_required_fields": "structured accounting fields",
        "recommended_next_action": recommended_action(reason, source),
        "confidence": read.confidence,
        "status": "UNPROCESSED_WITH_REASON",
    }


def recommended_action(reason: str, source: SourceFile) -> str:
    if "RAR extraction unavailable" in reason:
        return "Install 7-Zip, unrar, or rarfile backend and rerun analyzer."
    if "Unsupported file type" in reason:
        return "Convert file to PDF/TXT/CSV/XLSX/DOCX or process manually."
    if "No text extracted" in reason:
        return "Run OCR or provide text-based source document."
    if "No structured rows" in reason:
        return "Review manually or add parser pattern for this accounting format."
    return "Review source file manually."


def seven_zip_executable() -> str | None:
    for exe in ["7z", "7za", "unrar"]:
        found = shutil.which(exe)
        if found:
            return found
    return None


def extract_zip(source: SourceFile, temp_root: Path, log: ProcessingLog) -> list[SourceFile]:
    extracted: list[SourceFile] = []
    target_root = temp_root / "zip" / hashlib.sha1(source.display_path.encode("utf-8")).hexdigest()
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
                extracted.append(
                    SourceFile(target, f"{source.display_path}::{member.filename}", source.display_path, source.category_hint, True)
                )
        log.add(f"Extracted {len(extracted)} files from ZIP: {source.display_path}")
    except Exception as exc:
        log.add(f"ZIP_READ_ERROR {source.display_path}: {exc}")
    return extracted


def extract_rar(source: SourceFile, temp_root: Path, log: ProcessingLog, unprocessed: list[dict[str, str]]) -> list[SourceFile]:
    exe = seven_zip_executable()
    if exe:
        target_root = temp_root / "rar" / hashlib.sha1(source.display_path.encode("utf-8")).hexdigest()
        target_root.mkdir(parents=True, exist_ok=True)
        if Path(exe).name.lower().startswith("unrar"):
            cmd = [exe, "x", "-y", str(source.path), str(target_root)]
        else:
            cmd = [exe, "x", "-y", f"-o{target_root}", str(source.path)]
        result = subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=False)
        if result.returncode != 0:
            reason = f"RAR extraction failed: {result.stderr or result.stdout}"
            log.add(reason)
            unprocessed.append(make_unprocessed(source, reason))
            return []
        out = [
            SourceFile(path, f"{source.display_path}::{path.relative_to(target_root).as_posix()}", source.display_path, source.category_hint, True)
            for path in target_root.rglob("*")
            if path.is_file()
        ]
        log.add(f"Extracted {len(out)} files from RAR: {source.display_path}")
        return out
    reason = "RAR extraction unavailable"
    log.add(f"{reason}: {source.display_path}")
    unprocessed.append(make_unprocessed(source, reason))
    return []


def extract_eml(source: SourceFile, temp_root: Path, log: ProcessingLog) -> tuple[str, list[SourceFile]]:
    try:
        with source.path.open("rb") as handle:
            message = email.message_from_binary_file(handle, policy=policy.default)
    except Exception as exc:
        log.add(f"EML_READ_ERROR {source.display_path}: {exc}")
        return "", []
    body_parts = [
        f"email_date: {message.get('date', '')}",
        f"sender: {message.get('from', '')}",
        f"recipient: {message.get('to', '')}",
        f"subject: {message.get('subject', '')}",
    ]
    attachments: list[SourceFile] = []
    target_root = temp_root / "eml" / hashlib.sha1(source.display_path.encode("utf-8")).hexdigest()
    target_root.mkdir(parents=True, exist_ok=True)
    for index, part in enumerate(message.walk() if message.is_multipart() else [message], start=1):
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
            attachments.append(SourceFile(target, f"{source.display_path}::{filename}", source.display_path, source.category_hint, True))
        elif part.get_content_type() in {"text/plain", "text/html"}:
            try:
                body_parts.append(str(part.get_content()))
            except Exception:
                payload = part.get_payload(decode=True) or b""
                body_parts.append(payload.decode(part.get_content_charset() or "utf-8", errors="replace"))
    log.add(f"Read EML {source.display_path} with {len(attachments)} attachments.")
    return "\n".join(body_parts), attachments


def expand_all(initial: list[SourceFile], temp_root: Path, log: ProcessingLog, unprocessed: list[dict[str, str]]) -> list[SourceFile]:
    expanded: list[SourceFile] = []
    queue = list(initial)
    while queue:
        source = queue.pop(0)
        suffix = source.path.suffix.lower()
        if suffix == ".zip":
            queue.extend(extract_zip(source, temp_root, log))
            expanded.append(source)
        elif suffix == ".rar":
            queue.extend(extract_rar(source, temp_root, log, unprocessed))
            expanded.append(source)
        elif suffix == ".eml":
            _, attachments = extract_eml(source, temp_root, log)
            queue.extend(attachments)
            expanded.append(source)
        else:
            expanded.append(source)
    extracted_count = sum(1 for item in expanded if item.is_extracted)
    log.stats["expanded_archive_files"] = extracted_count
    return expanded


def read_pdf(source: SourceFile, log: ProcessingLog) -> ReadResult:
    errors: list[str] = []
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(source.path))
        attempted = "YES"
        success = "NOT_APPLICABLE"
        if reader.is_encrypted:
            decrypt_result = reader.decrypt(PDF_PASSWORD)
            success = "YES" if decrypt_result else "NO"
            log.add(f"PDF password attempted for {source.display_path}: {success}")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            return ReadResult(text, "HIGH", attempted, success)
        errors.append("pypdf returned no text")
    except Exception as exc:
        errors.append(f"pypdf failed: {exc}")
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(str(source.path), password=PDF_PASSWORD) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if text.strip():
            return ReadResult(text, "HIGH", "YES", "YES")
        errors.append("pdfplumber returned no text")
    except Exception as exc:
        errors.append(f"pdfplumber failed: {exc}")
    reason = "No text extracted from PDF: " + " | ".join(errors)
    log.add(f"PDF_READ_ERROR {source.display_path}: {reason}")
    return ReadResult("", "LOW", "YES", "NO", reason)


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def read_docx(path: Path, log: ProcessingLog) -> ReadResult:
    try:
        with zipfile.ZipFile(path) as archive:
            texts: list[str] = []
            for name in archive.namelist():
                if name.startswith("word/") and name.endswith(".xml"):
                    root = ET.fromstring(archive.read(name))
                    texts.append(" ".join(root.itertext()))
            return ReadResult("\n".join(texts), "MEDIUM")
    except Exception as exc:
        reason = f"DOCX_READ_ERROR: {exc}"
        log.add(f"{reason} {path}")
        return ReadResult("", "LOW", reason=reason)


def read_xlsx(path: Path, log: ProcessingLog) -> ReadResult:
    try:
        import openpyxl  # type: ignore

        workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
        values: list[str] = []
        for sheet in workbook.worksheets:
            values.append(f"Sheet: {sheet.title}")
            for row in sheet.iter_rows(values_only=True):
                values.append(" | ".join("" if cell is None else str(cell) for cell in row))
        return ReadResult("\n".join(values), "HIGH")
    except Exception as exc:
        log.add(f"openpyxl failed for {path}: {exc}")
    try:
        with zipfile.ZipFile(path) as archive:
            values: list[str] = []
            for name in archive.namelist():
                if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                    root = ET.fromstring(archive.read(name))
                    values.append(" ".join(root.itertext()))
            return ReadResult("\n".join(values), "LOW")
    except Exception as exc:
        reason = f"XLSX_READ_ERROR: {exc}"
        log.add(f"{reason} {path}")
        return ReadResult("", "LOW", reason=reason)


def read_source(source: SourceFile, temp_root: Path, log: ProcessingLog) -> ReadResult:
    suffix = source.path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf(source, log)
    if suffix in {".txt", ".csv"}:
        return ReadResult(read_text(source.path), "MEDIUM")
    if suffix == ".xlsx":
        return read_xlsx(source.path, log)
    if suffix == ".docx":
        return read_docx(source.path, log)
    if suffix == ".eml":
        body, _ = extract_eml(source, temp_root, log)
        return ReadResult(body, "MEDIUM" if body.strip() else "LOW")
    return ReadResult("", "LOW", reason=f"Unsupported file type: {suffix}")


def deduplicate(sources: list[SourceFile], log: ProcessingLog) -> tuple[list[SourceFile], list[dict[str, str]], set[str]]:
    seen: dict[str, SourceFile] = {}
    unique: list[SourceFile] = []
    duplicates: list[dict[str, str]] = []
    duplicate_paths: set[str] = set()
    for source in sources:
        if source.path.suffix.lower() in ARCHIVE_EXTENSIONS:
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
            duplicate_paths.add(source.display_path)
            continue
        seen[digest] = source
        unique.append(source)
    return unique, duplicates, duplicate_paths


def extract_amount_near(text: str, terms: Iterable[str]) -> Decimal | None:
    for term in terms:
        match = re.search(rf"{term}.{{0,160}}?({money_pattern()})\s*(?:EUR|€)?", text, re.IGNORECASE | re.DOTALL)
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
            if 4 <= len(name) <= 80:
                names.add(name)
    return sorted(names)


def detect_health_insurer(haystack: str) -> str:
    for name in HEALTH_INSURERS:
        if normalize(name) in haystack:
            return name
    if "krankenkasse" in haystack:
        return "other"
    if "hauptzollamt" in haystack:
        return "Hauptzollamt linked Krankenkasse claim"
    return ""


def extract_rows(source: SourceFile, read: ReadResult) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    text = read.text
    month = extract_month(text, source.display_path)
    haystack = normalize(f"{source.display_path}\n{source.category_hint}\n{text}")
    src = source.display_path
    employee_rows: list[dict[str, str]] = []
    payroll_rows: list[dict[str, str]] = []
    health_rows: list[dict[str, str]] = []
    tax_rows: list[dict[str, str]] = []
    operating_rows: list[dict[str, str]] = []
    enrico_rows: list[dict[str, str]] = []

    if any(term in haystack for term in ENRICO_TERMS):
        number = first_match([r"(?:Gutschrift|Rechnung)\s+Nr\.?\s*[:#]?\s*([A-Z0-9./_-]+(?:\s*-\s*\d{2,4})?)"], text)
        doc_type = first_match([r"\b(Gutschrift|Rechnung|Leistungsnachweis|Sendungsverlust|Scannermiete)\b"], text)
        date = first_match([r"(?:Datum|Rechnungsdatum|Gutschriftdatum)\D{0,40}(\d{1,2}\.\d{1,2}\.\d{2,4})"], text)
        amount = extract_amount_near(text, ["Gesamtbetrag", "Endbetrag", "Nettosumme", "Rechnungsbetrag", "Betrag"])
        enrico_rows.append(
            {
                "month": month,
                "document_number": re.sub(r"\s+", "", number),
                "document_type": doc_type,
                "document_date": date,
                "amount": fmt(amount),
                "source_file": src,
                "already_in_enrico_report": "UNKNOWN",
                "action_needed": "",
            }
        )

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
                    "confidence": read.confidence,
                }
            )

    insurer = detect_health_insurer(haystack)
    if insurer:
        due = extract_amount_near(text, ["fällig", "faellig", "Soll", "Beitrag", "Forderung", "Gesamt", "Betrag"])
        paid = extract_amount_near(text, ["bezahlt", "gezahlt", "payment", "paid", "Ist", "Überweisung", "Ueberweisung"])
        unpaid = extract_amount_near(text, ["offen", "Rückstand", "Rueckstand", "unpaid", "balance", "Rest"])
        late = extract_amount_near(text, ["Säumniszuschlag", "Saeumniszuschlag", "late fee", "Mahngebühr", "Mahngebuehr"])
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
                "confidence": read.confidence if any(v is not None for v in [due, paid, unpaid, late]) else "LOW",
            }
        )

    if any(term in haystack for term in ["finanzamt", "stadt chemnitz", "gewerbesteuer", "umsatzsteuer", "lohnsteuer", "einkommensteuer", "hauptzollamt"]):
        creditor = "Finanzamt" if "finanzamt" in haystack else "Stadt Chemnitz" if "stadt chemnitz" in haystack or "gewerbesteuer" in haystack else "Hauptzollamt" if "hauptzollamt" in haystack else ""
        tax_type = next((term for term in TAX_TYPES if normalize(term) in haystack), "other public liability")
        due = extract_amount_near(text, ["fällig", "faellig", "Steuer", "Soll", "Forderung", "Gesamt", "Betrag"])
        paid = extract_amount_near(text, ["bezahlt", "gezahlt", "payment", "paid", "Ist"])
        unpaid = extract_amount_near(text, ["offen", "Rückstand", "Rueckstand", "unpaid", "balance", "Rest"])
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
                "confidence": read.confidence if any(v is not None for v in [due, paid, unpaid]) else "LOW",
            }
        )

    for category, terms in OPERATING_KEYWORDS.items():
        if any(term in haystack for term in terms):
            due = extract_amount_near(text, ["Betrag", "Rechnung", "Kosten", "amount due", "Gesamt"])
            paid = extract_amount_near(text, ["bezahlt", "gezahlt", "paid"])
            unpaid = extract_amount_near(text, ["offen", "unpaid", "balance", "Rest"])
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
                    "confidence": read.confidence if any(v is not None for v in [due, paid, unpaid]) else "LOW",
                }
            )
            break

    return employee_rows, payroll_rows, health_rows, tax_rows, operating_rows, enrico_rows


def load_enrico_index() -> tuple[dict[str, str], set[str]]:
    monthly: dict[str, str] = {}
    detail_numbers: set[str] = set()
    if ENRICO_MONTHLY.exists():
        with ENRICO_MONTHLY.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                monthly[row.get("month", "")] = row.get("total_deductions_negative") or row.get("total_deductions") or ""
    if ENRICO_DETAIL.exists():
        with ENRICO_DETAIL.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                number = row.get("document_number", "")
                if number:
                    detail_numbers.add(number.replace(" ", ""))
    return monthly, detail_numbers


def finalize_enrico_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    _, detail_numbers = load_enrico_index()
    for row in rows:
        number = row.get("document_number", "").replace(" ", "")
        if number and number in detail_numbers:
            row["already_in_enrico_report"] = "YES"
            row["action_needed"] = ""
        elif number:
            row["already_in_enrico_report"] = "NO"
            row["action_needed"] = "POSSIBLE_MISSING_ENRICO_EVIDENCE"
        else:
            row["already_in_enrico_report"] = "UNKNOWN"
            row["action_needed"] = "REVIEW_ENRICO_DOCUMENT"
    return rows


def write_csv(path: Path, headers: list[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def col_name(index: int) -> str:
    result = ""
    while index:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def write_xlsx(path: Path, headers: list[str], rows: list[dict[str, str]], sheet_name: str) -> None:
    values = [headers] + [[str(row.get(header, "")) for header in headers] for row in rows]
    sheet_rows: list[str] = []
    for row_index, row_values in enumerate(values, start=1):
        cells: list[str] = []
        for col_index, value in enumerate(row_values, start=1):
            ref = f"{col_name(col_index)}{row_index}"
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


def build_monthly(
    employee_rows: list[dict[str, str]],
    payroll_rows: list[dict[str, str]],
    health_rows: list[dict[str, str]],
    tax_rows: list[dict[str, str]],
    operating_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], str]:
    enrico_monthly, _ = load_enrico_index()
    monthly: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    first_unpaid_health = ""
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
        obligations = payroll_brutto + health_due + tax_due + op_due
        paid = payroll_netto + health_paid + tax_paid + op_paid
        unpaid = health_unpaid + tax_unpaid + op_unpaid
        monthly.append(
            {
                "month": month,
                "enrico_deductions_total_if_available": enrico_monthly.get(month, ""),
                "revenue_if_available": "",
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
                "total_monthly_obligations": fmt(obligations) if obligations else "",
                "total_paid": fmt(paid) if paid else "",
                "total_unpaid": fmt(unpaid) if unpaid else "",
                "notes": "" if has_docs else "No extracted accounting values for this month.",
                "confidence": "MEDIUM" if has_docs else "LOW",
            }
        )
    return monthly, missing, first_unpaid_health


def markdown_table(headers: list[str], rows: list[dict[str, str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")).replace("\n", " ") for header in headers) + " |")
    return "\n".join(lines)


def write_unprocessed_report(rows: list[dict[str, str]]) -> None:
    grouped: dict[str, int] = defaultdict(int)
    for row in rows:
        grouped[row.get("reason_not_processed", "")] += 1
    lines = ["# Unprocessed Files Report", "", f"Total unprocessed or partial files: {len(rows)}", ""]
    lines.append("## Reasons")
    for reason, count in sorted(grouped.items()):
        lines.append(f"- {reason}: {count}")
    lines.append("")
    lines.append(markdown_table(["filename", "file_type", "reason_not_processed", "recommended_next_action"], rows[:200]))
    (REPORT_ROOT / "unprocessed_files_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(monthly: list[dict[str, str]], missing: list[dict[str, str]], first_unpaid_health: str, documents_used: list[str]) -> None:
    missing_lines = "\n".join(f"- {row['month']}: {row['notes']}" for row in missing) or "- None detected"
    docs = "\n".join(f"- {doc}" for doc in documents_used[:500]) or "- No accounting source documents produced extractable rows."
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

## First Visible Unpaid Health Insurance Month

{first_unpaid_health or 'Not detected'}

## Months With Missing Data

{missing_lines}

## Documents Used

{docs}

## Limitations

- OCR is not implemented.
- Empty values mean no reliable value was extracted.
- Password-protected PDFs are attempted with password `10001`.
- RAR extraction depends on 7-Zip, unrar, or an equivalent backend.
- Complex accounting spreadsheets may require manual review.

## Next Documents Needed

- Missing monthly payroll summaries from 2024-01 to 2025-06.
- Krankenkassen statements showing due, paid, and unpaid amounts.
- Finanzamt, Stadt Chemnitz, Hauptzollamt, and open-liability tables.
- Text-based or OCR-ready versions of image-only documents.
"""
    (REPORT_ROOT / "ACCOUNTING_CASH_FLOW_RECONSTRUCTION.md").write_text(report, encoding="utf-8")


def write_output_readme() -> None:
    text = """# Accounting Cash Flow Outputs

Generated by `analyze_accounting_cash_flow.py`.

This folder contains reconstructed accounting timelines, Enrico cross-checks, duplicate detection, and a full file audit.

Every scanned or expanded file receives one final status:

- `PROCESSED_STRUCTURED`
- `PROCESSED_PARTIAL`
- `DUPLICATE`
- `ENRICO_CROSS_CHECK`
- `SKIPPED_WITH_REASON`
- `UNPROCESSED_WITH_REASON`

Empty values mean the analyzer could not reliably extract a number.
"""
    (REPORT_ROOT / "README.md").write_text(text, encoding="utf-8")


def analyze() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    list[dict[str, str]],
    str,
    ProcessingLog,
]:
    log = ProcessingLog()
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    employee_rows: list[dict[str, str]] = []
    payroll_rows: list[dict[str, str]] = []
    health_rows: list[dict[str, str]] = []
    tax_rows: list[dict[str, str]] = []
    operating_rows: list[dict[str, str]] = []
    enrico_rows: list[dict[str, str]] = []
    unprocessed: list[dict[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="accounting_cash_flow_") as temp_dir:
        sources = expand_all(scan_inputs(log, unprocessed), Path(temp_dir), log, unprocessed)
        unique_sources, duplicates, duplicate_paths = deduplicate(sources, log)
        for duplicate in duplicates:
            unprocessed.append(
                {
                    "filename": Path(duplicate["duplicate_source_file"]).name,
                    "full_path": duplicate["duplicate_source_file"],
                    "file_type": Path(duplicate["duplicate_source_file"]).suffix.lower(),
                    "detected_document_type": "",
                    "reason_not_processed": "Duplicate file",
                    "password_attempted": "NO",
                    "password_success": "NOT_APPLICABLE",
                    "text_extracted": "NO",
                    "structured_rows_extracted": "0",
                    "missing_required_fields": "",
                    "recommended_next_action": "Use kept source file.",
                    "confidence": "HIGH",
                    "status": "DUPLICATE",
                }
            )

        for source in unique_sources:
            suffix = source.path.suffix.lower()
            if suffix in ARCHIVE_EXTENSIONS:
                continue
            if suffix not in TEXT_EXTENSIONS:
                unprocessed.append(make_unprocessed(source, f"Unsupported file type: {suffix}"))
                log.add(f"UNPROCESSED unsupported file: {source.display_path}")
                continue

            read = read_source(source, Path(temp_dir), log)
            detected_type = detect_document_type(read.text, source)
            if not read.text.strip():
                unprocessed.append(make_unprocessed(source, read.reason or "No text extracted", detected_type, read))
                log.add(f"UNPROCESSED no text: {source.display_path}")
                continue

            extracted = extract_rows(source, read)
            employee_rows.extend(extracted[0])
            payroll_rows.extend(extracted[1])
            health_rows.extend(extracted[2])
            tax_rows.extend(extracted[3])
            operating_rows.extend(extracted[4])
            enrico_rows.extend(extracted[5])
            structured_count = sum(len(part) for part in extracted)

            if extracted[5] and structured_count == len(extracted[5]):
                status = "ENRICO_CROSS_CHECK"
            elif structured_count:
                status = "PROCESSED_STRUCTURED"
            else:
                status = "PROCESSED_PARTIAL"

            if status == "PROCESSED_PARTIAL":
                row = make_unprocessed(source, "No structured rows extracted", detected_type, read, structured_count)
                row["status"] = "PROCESSED_PARTIAL"
                unprocessed.append(row)
            log.stats[status.lower()] += 1
            log.add(f"{status}: {source.display_path}")

    enrico_rows = finalize_enrico_rows(enrico_rows)
    monthly, missing, first_unpaid_health = build_monthly(employee_rows, payroll_rows, health_rows, tax_rows, operating_rows)
    log.stats["employee_rows"] = len(employee_rows)
    log.stats["payroll_rows"] = len(payroll_rows)
    log.stats["health_rows"] = len(health_rows)
    log.stats["tax_rows"] = len(tax_rows)
    log.stats["operating_rows"] = len(operating_rows)
    log.stats["enrico_cross_check"] = len(enrico_rows)
    log.stats["unprocessed"] = sum(1 for row in unprocessed if row["status"] == "UNPROCESSED_WITH_REASON")
    log.stats["skipped"] = sum(1 for row in unprocessed if row["status"] == "SKIPPED_WITH_REASON")
    log.stats["partial"] = sum(1 for row in unprocessed if row["status"] == "PROCESSED_PARTIAL")
    log.stats["duplicates"] = len(duplicates)
    return (
        employee_rows,
        payroll_rows,
        health_rows,
        tax_rows,
        operating_rows,
        enrico_rows,
        monthly,
        missing,
        duplicates,
        unprocessed,
        first_unpaid_health,
        log,
    )


def main() -> int:
    (
        employee_rows,
        payroll_rows,
        health_rows,
        tax_rows,
        operating_rows,
        enrico_rows,
        monthly,
        missing,
        duplicates,
        unprocessed,
        first_unpaid_health,
        log,
    ) = analyze()

    outputs = [
        ("employee_timeline", EMPLOYEE_HEADERS, employee_rows, "Employees"),
        ("payroll_timeline", PAYROLL_HEADERS, payroll_rows, "Payroll"),
        ("health_insurance_timeline", HEALTH_HEADERS, health_rows, "Health"),
        ("tax_timeline", TAX_HEADERS, tax_rows, "Taxes"),
        ("operating_costs_timeline", OPERATING_HEADERS, operating_rows, "Operating"),
        ("enrico_cross_check", ENRICO_HEADERS, enrico_rows, "Enrico"),
        ("monthly_cash_flow_reconstruction", MONTHLY_HEADERS, monthly, "Monthly"),
        ("unprocessed_files", UNPROCESSED_HEADERS, unprocessed, "Unprocessed"),
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
    write_unprocessed_report(unprocessed)
    write_output_readme()
    log.write(REPORT_ROOT / "processing_log.txt")

    print(f"Scanned files: {log.stats.get('scanned_files', 0)}")
    print(f"Expanded archive files: {log.stats.get('expanded_archive_files', 0)}")
    print(f"Processed structured count: {log.stats.get('processed_structured', 0)}")
    print(f"Processed partial count: {log.stats.get('partial', 0)}")
    print(f"Unprocessed count: {log.stats.get('unprocessed', 0)}")
    print(f"Skipped count: {log.stats.get('skipped', 0)}")
    print(f"Duplicate count: {log.stats.get('duplicates', 0)}")
    print(f"Enrico cross-check count: {len(enrico_rows)}")
    print(f"Employee rows: {len(employee_rows)}")
    print(f"Payroll rows: {len(payroll_rows)}")
    print(f"Health insurance rows: {len(health_rows)}")
    print(f"Tax rows: {len(tax_rows)}")
    print(f"Operating cost rows: {len(operating_rows)}")
    print(f"First visible unpaid health insurance month: {first_unpaid_health or 'Not detected'}")
    print(f"Missing months: {len(missing)}")
    print(f"Output folder: {repo_relative(REPORT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
