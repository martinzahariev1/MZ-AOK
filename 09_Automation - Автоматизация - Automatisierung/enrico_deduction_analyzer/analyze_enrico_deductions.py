#!/usr/bin/env python3
"""Analyze Enrico/Sachsenpower financial deductions by month.

The analyzer is intentionally conservative. It never modifies source files,
does not invent values, and leaves fields empty with LOW confidence when a
value cannot be extracted.
"""

from __future__ import annotations

import csv
import email
import hashlib
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from email import policy
from email.message import EmailMessage, Message
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_ROOT = REPO_ROOT / "03_Documents - Документи - Dokumente"
INBOX_ROOT = REPO_ROOT / "_INBOX"
REPORT_ROOT = REPO_ROOT / "08_Reports - Доклади - Berichte" / "Enrico_Deductions"

SUPPORTED_EXTENSIONS = {".pdf", ".zip", ".rar", ".txt", ".csv", ".eml"}
PERIOD_START = (2024, 2)
PERIOD_END = (2025, 6)

DETAIL_HEADERS = [
    "document_filename",
    "document_type",
    "document_number",
    "document_date",
    "leistungszeitraum",
    "month_year",
    "position_code",
    "position_name",
    "quantity",
    "price_per_unit",
    "amount",
    "package_id",
    "tour_number",
    "customer_location",
    "source_file_path",
    "source_container",
    "confidence_level",
    "deduction_category",
    "content_hash",
    "duplicate_key",
    "notes",
]

MONTHLY_HEADERS = [
    "month",
    "gross_credit_gutschrift_total",
    "abschlag_coincident_total",
    "abschlag_mitnahme_total",
    "abschlag_quittungslose_sendung_total",
    "sendungsverlust_total",
    "scannermiete_total",
    "other_deductions_total",
    "total_deductions",
    "net_amount_if_available",
    "number_of_source_documents",
    "missing_source_documents",
    "notes",
]

DUPLICATE_HEADERS = [
    "duplicate_key",
    "kept_source_file",
    "duplicate_source_file",
    "document_number",
    "document_date",
    "amount",
    "content_hash",
    "reason",
]

MISSING_HEADERS = ["month", "missing_source_documents", "notes"]

DOCUMENT_TERMS = [
    "Gutschrift",
    "Rechnung",
    "Leistungsnachweis",
    "Sendungsverlust",
    "Rückerstattung",
    "Rueckerstattung",
    "Rechnungskorrektur",
    "Scannermiete",
    "Abschlag Coincident",
    "Abschlag Mitnahme",
    "Abschlag Quittungslose Sendung",
]

DEDUCTION_CATEGORIES = [
    "Abschlag Coincident",
    "Abschlag Mitnahme",
    "Abschlag Quittungslose Sendung",
    "Sendungsverlust",
    "Scannermiete",
    "Scanner-related invoices",
    "Other deductions",
]


@dataclass
class SourceDocument:
    path: Path
    display_path: str
    source_container: str = ""
    extracted_from: str = ""
    email_metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class DetailRow:
    document_filename: str = ""
    document_type: str = ""
    document_number: str = ""
    document_date: str = ""
    leistungszeitraum: str = ""
    month_year: str = ""
    position_code: str = ""
    position_name: str = ""
    quantity: str = ""
    price_per_unit: str = ""
    amount: str = ""
    package_id: str = ""
    tour_number: str = ""
    customer_location: str = ""
    source_file_path: str = ""
    source_container: str = ""
    confidence_level: str = "LOW"
    deduction_category: str = ""
    content_hash: str = ""
    duplicate_key: str = ""
    notes: str = ""

    def as_dict(self) -> dict[str, str]:
        return {header: getattr(self, header) for header in DETAIL_HEADERS}


class ProcessingLog:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def add(self, message: str) -> None:
        timestamp = datetime.now().isoformat(timespec="seconds")
        self.lines.append(f"{timestamp} {message}")

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


def safe_extract_path(base_dir: Path, member_name: str) -> Path | None:
    target = (base_dir / member_name).resolve()
    try:
        target.relative_to(base_dir.resolve())
    except ValueError:
        return None
    return target


def scan_input_files(log: ProcessingLog) -> list[SourceDocument]:
    roots = [root for root in [INBOX_ROOT, DOCUMENTS_ROOT] if root.exists()]
    documents: list[SourceDocument] = []
    for root in roots:
        log.add(f"Scanning input folder: {repo_relative(root)}")
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                documents.append(SourceDocument(path=path, display_path=repo_relative(path)))
    log.add(f"Found {len(documents)} supported source files before archive/email expansion.")
    return documents


def extract_zip(source: SourceDocument, temp_root: Path, log: ProcessingLog) -> list[SourceDocument]:
    extracted: list[SourceDocument] = []
    target_root = temp_root / "zip" / hashlib.sha1(str(source.path).encode("utf-8")).hexdigest()
    target_root.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(source.path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                target = safe_extract_path(target_root, member.filename)
                if target is None:
                    log.add(f"Skipped unsafe ZIP member path: {member.filename}")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                if target.suffix.lower() in SUPPORTED_EXTENSIONS:
                    extracted.append(
                        SourceDocument(
                            path=target,
                            display_path=f"{source.display_path}::{member.filename}",
                            source_container=source.display_path,
                            extracted_from="zip",
                        )
                    )
        log.add(f"Extracted {len(extracted)} supported files from ZIP: {source.display_path}")
    except zipfile.BadZipFile:
        log.add(f"Failed to read ZIP archive: {source.display_path}")
    return extracted


def extract_rar(source: SourceDocument, temp_root: Path, log: ProcessingLog) -> list[SourceDocument]:
    try:
        import rarfile  # type: ignore
    except ImportError:
        log.add(f"RAR skipped because optional dependency 'rarfile' is not installed: {source.display_path}")
        return []

    extracted: list[SourceDocument] = []
    target_root = temp_root / "rar" / hashlib.sha1(str(source.path).encode("utf-8")).hexdigest()
    target_root.mkdir(parents=True, exist_ok=True)
    try:
        with rarfile.RarFile(source.path) as archive:
            for member in archive.infolist():
                if member.isdir():
                    continue
                target = safe_extract_path(target_root, member.filename)
                if target is None:
                    log.add(f"Skipped unsafe RAR member path: {member.filename}")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                if target.suffix.lower() in SUPPORTED_EXTENSIONS:
                    extracted.append(
                        SourceDocument(
                            path=target,
                            display_path=f"{source.display_path}::{member.filename}",
                            source_container=source.display_path,
                            extracted_from="rar",
                        )
                    )
        log.add(f"Extracted {len(extracted)} supported files from RAR: {source.display_path}")
    except Exception as exc:  # RAR support depends on local backend tools.
        log.add(f"Failed to read RAR archive {source.display_path}: {exc}")
    return extracted


def message_body(message: Message) -> str:
    parts: list[str] = []
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_disposition() == "attachment":
                continue
            content_type = part.get_content_type()
            if content_type in {"text/plain", "text/html"}:
                try:
                    payload = part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True) or b""
                    payload = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                parts.append(str(payload))
    else:
        try:
            parts.append(str(message.get_content()))
        except Exception:
            payload = message.get_payload(decode=True) or b""
            parts.append(payload.decode(message.get_content_charset() or "utf-8", errors="replace"))
    return "\n".join(parts)


def extract_eml(source: SourceDocument, temp_root: Path, log: ProcessingLog) -> tuple[str, list[SourceDocument], dict[str, str]]:
    attachments: list[SourceDocument] = []
    metadata = {
        "email_date": "",
        "sender": "",
        "recipient": "",
        "subject": "",
        "attachments": "",
    }
    try:
        with source.path.open("rb") as handle:
            message = email.message_from_binary_file(handle, policy=policy.default)
    except Exception as exc:
        log.add(f"Failed to read EML {source.display_path}: {exc}")
        return "", attachments, metadata

    metadata = {
        "email_date": str(message.get("date", "")),
        "sender": str(message.get("from", "")),
        "recipient": str(message.get("to", "")),
        "subject": str(message.get("subject", "")),
        "attachments": "",
    }

    target_root = temp_root / "eml" / hashlib.sha1(str(source.path).encode("utf-8")).hexdigest()
    target_root.mkdir(parents=True, exist_ok=True)
    attachment_names: list[str] = []
    if isinstance(message, EmailMessage) or message.is_multipart():
        for index, part in enumerate(message.walk(), start=1):
            if part.get_content_disposition() != "attachment":
                continue
            filename = part.get_filename() or f"attachment-{index}"
            attachment_names.append(filename)
            target = safe_extract_path(target_root, filename)
            if target is None:
                log.add(f"Skipped unsafe EML attachment path: {filename}")
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            if target.suffix.lower() in SUPPORTED_EXTENSIONS:
                attachments.append(
                    SourceDocument(
                        path=target,
                        display_path=f"{source.display_path}::{filename}",
                        source_container=source.display_path,
                        extracted_from="eml",
                        email_metadata=metadata,
                    )
                )
    metadata["attachments"] = "; ".join(attachment_names)
    log.add(f"Read EML {source.display_path} with {len(attachment_names)} attachments.")
    return message_body(message), attachments, metadata


def expand_archives_and_emails(initial_docs: list[SourceDocument], temp_root: Path, log: ProcessingLog) -> list[SourceDocument]:
    expanded: list[SourceDocument] = []
    queue = list(initial_docs)
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
            _, attachments, _ = extract_eml(source, temp_root, log)
            queue.extend(attachments)
            expanded.append(source)
        else:
            expanded.append(source)

    log.add(f"Total supported files after archive/email expansion: {len(expanded)}")
    return expanded


def read_pdf_text(path: Path, log: ProcessingLog) -> tuple[str, str]:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text, "PDF text extracted with pypdf."
    except ImportError:
        pass
    except Exception as exc:
        log.add(f"pypdf failed for {repo_relative(path)}: {exc}")

    try:
        from PyPDF2 import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text, "PDF text extracted with PyPDF2."
    except ImportError:
        pass
    except Exception as exc:
        log.add(f"PyPDF2 failed for {repo_relative(path)}: {exc}")

    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        result = subprocess.run(
            [pdftotext, "-layout", str(path), "-"],
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
        )
        if result.returncode == 0:
            return result.stdout, "PDF text extracted with pdftotext."
        log.add(f"pdftotext failed for {repo_relative(path)}: {result.stderr.strip()}")

    log.add(f"PDF text unavailable; install pypdf, PyPDF2, or pdftotext: {repo_relative(path)}")
    return "", "PDF text unavailable."


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def read_source_text(source: SourceDocument, temp_root: Path, log: ProcessingLog) -> tuple[str, dict[str, str], str]:
    suffix = source.path.suffix.lower()
    if suffix == ".pdf":
        text, note = read_pdf_text(source.path, log)
        return text, {}, note
    if suffix in {".txt", ".csv"}:
        return read_text_file(source.path), {}, "Text read from plain text/CSV file."
    if suffix == ".eml":
        body, _, metadata = extract_eml(source, temp_root, log)
        header_text = "\n".join(f"{key}: {value}" for key, value in metadata.items())
        return f"{header_text}\n\n{body}", metadata, "Email headers and body extracted."
    return "", {}, "Unsupported content reading for this file type."


def normalize_text(value: str) -> str:
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
    }
    for source, replacement in replacements.items():
        value = value.replace(source, replacement)
    return value.lower()


def is_relevant(source: SourceDocument, text: str) -> bool:
    haystack = normalize_text(f"{source.display_path}\n{text}")
    parties = ["enrico", "weissflog", "weissflog", "sachsenpower"]
    terms = [normalize_text(term) for term in DOCUMENT_TERMS]
    return any(party in haystack for party in parties) or any(term in haystack for term in terms)


def detect_document_type(text: str, filename: str) -> str:
    haystack = normalize_text(f"{filename}\n{text}")
    for term in DOCUMENT_TERMS:
        if normalize_text(term) in haystack:
            return term.replace("Rueckerstattung", "Rückerstattung")
    return ""


def parse_decimal(value: str) -> Decimal | None:
    value = value.strip()
    value = re.sub(r"[^\d,.\-]", "", value)
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


def format_decimal(value: Decimal | None) -> str:
    if value is None:
        return ""
    return f"{value.quantize(Decimal('0.01'))}"


def find_first(patterns: Iterable[str], text: str, flags: int = re.IGNORECASE) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()
    return ""


def normalize_date(value: str) -> str:
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return value


def extract_month(text: str, document_date: str, leistungszeitraum: str) -> str:
    period_text = leistungszeitraum or text
    match = re.search(r"\b(0?[1-9]|1[0-2])[./-](20\d{2})\b", period_text)
    if match:
        return f"{int(match.group(2)):04d}-{int(match.group(1)):02d}"
    match = re.search(r"\b(20\d{2})[-/](0?[1-9]|1[0-2])\b", period_text)
    if match:
        return f"{int(match.group(1)):04d}-{int(match.group(2)):02d}"
    if document_date:
        match = re.match(r"(20\d{2})-(\d{2})-\d{2}", document_date)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
    return ""


def extract_amount_near(term: str, text: str) -> Decimal | None:
    normalized_term = re.escape(term)
    patterns = [
        rf"{normalized_term}.{{0,160}}?(-?\d{{1,3}}(?:[.\s]\d{{3}})*(?:,\d{{2}})|-?\d+(?:[,.]\d{{2}})?)\s*(?:EUR|€)",
        rf"{normalized_term}.{{0,160}}?(?:EUR|€)\s*(-?\d{{1,3}}(?:[.\s]\d{{3}})*(?:,\d{{2}})|-?\d+(?:[,.]\d{{2}})?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return parse_decimal(match.group(1))
    return None


def extract_general_amount(text: str) -> Decimal | None:
    patterns = [
        r"(?:Gesamtbetrag|Gutschrift|Rechnungsbetrag|Endbetrag|Summe|Netto)\D{0,80}(-?\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})|-?\d+(?:[,.]\d{2})?)\s*(?:EUR|€)",
        r"(?:EUR|€)\s*(-?\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})|-?\d+(?:[,.]\d{2})?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return parse_decimal(match.group(1))
    return None


def category_from_text(text: str, document_type: str) -> str:
    haystack = normalize_text(f"{document_type}\n{text}")
    if "abschlag coincident" in haystack:
        return "Abschlag Coincident"
    if "abschlag mitnahme" in haystack:
        return "Abschlag Mitnahme"
    if "abschlag quittungslose sendung" in haystack:
        return "Abschlag Quittungslose Sendung"
    if "sendungsverlust" in haystack:
        return "Sendungsverlust"
    if "scannermiete" in haystack:
        return "Scannermiete"
    if "scanner" in haystack and "rechnung" in haystack:
        return "Scanner-related invoices"
    if "abschlag" in haystack or "rueckerstattung" in haystack or "rueck" in haystack:
        return "Other deductions"
    return ""


def extract_detail_rows(source: SourceDocument, text: str, email_metadata: dict[str, str], note: str) -> list[DetailRow]:
    document_type = detect_document_type(text, source.path.name)
    document_number = find_first(
        [
            r"(?:Rechnung(?:s)?nummer|Rechnungsnr\.?|Gutschrift(?:s)?nummer|Belegnummer|Dokumentnummer|Nr\.?)\s*[:#]?\s*([A-Z0-9][A-Z0-9./_-]{2,})",
            r"\b(?:RG|RE|GS|GU|INV)[- ]?(\d{3,})\b",
        ],
        text,
    )
    document_date = normalize_date(
        find_first(
            [
                r"(?:Rechnungsdatum|Gutschriftdatum|Belegdatum|Dokumentdatum|Datum)\s*[:#]?\s*(\d{1,2}\.\d{1,2}\.\d{2,4})",
                r"\b(\d{4}-\d{2}-\d{2})\b",
            ],
            text,
        )
    )
    leistungszeitraum = find_first(
        [
            r"Leistungszeitraum\s*[:#]?\s*([^\n\r]+)",
            r"Leistungsperiode\s*[:#]?\s*([^\n\r]+)",
            r"Zeitraum\s*[:#]?\s*([^\n\r]+)",
        ],
        text,
    )
    month_year = extract_month(text, document_date, leistungszeitraum)
    position_code = find_first([r"(?:Positionsnummer|Position|Pos\.?)\s*[:#]?\s*([A-Z0-9._/-]+)"], text)
    package_id = find_first([r"(?:Paket(?:nummer)?|Sendung(?:snummer)?|Package ID)\s*[:#]?\s*([A-Z0-9._/-]+)"], text)
    tour_number = find_first([r"(?:Tour(?:nummer)?|Tour-Nr\.?)\s*[:#]?\s*([A-Z0-9._/-]+)"], text)
    customer_location = find_first([r"(?:Kunde|Standort|Depot|Ort)\s*[:#]?\s*([^\n\r]+)"], text)
    quantity = find_first([r"(?:Menge|Anzahl|Qty\.?)\s*[:#]?\s*(-?\d+(?:[,.]\d+)?)"], text)
    price = find_first([r"(?:Einzelpreis|Preis je Einheit|Stückpreis)\s*[:#]?\s*(-?\d+(?:[,.]\d{2})?)"], text)

    rows: list[DetailRow] = []
    for category in DEDUCTION_CATEGORIES:
        if category == "Other deductions":
            continue
        amount = extract_amount_near(category, text)
        if amount is not None:
            rows.append(
                build_detail_row(
                    source,
                    document_type,
                    document_number,
                    document_date,
                    leistungszeitraum,
                    month_year,
                    position_code,
                    category,
                    quantity,
                    price,
                    amount,
                    package_id,
                    tour_number,
                    customer_location,
                    category,
                    "MEDIUM",
                    note,
                )
            )

    if rows:
        return rows

    amount = extract_general_amount(text)
    category = category_from_text(text, document_type)
    position_name = category or document_type
    if document_type or category or amount is not None:
        rows.append(
            build_detail_row(
                source,
                document_type,
                document_number,
                document_date,
                leistungszeitraum,
                month_year,
                position_code,
                position_name,
                quantity,
                price,
                amount,
                package_id,
                tour_number,
                customer_location,
                category,
                "LOW" if amount is None else "MEDIUM",
                note,
            )
        )
    elif email_metadata:
        rows.append(
            build_detail_row(
                source,
                "Email",
                document_number,
                normalize_date(email_metadata.get("email_date", "")),
                leistungszeitraum,
                month_year,
                position_code,
                "",
                quantity,
                price,
                None,
                package_id,
                tour_number,
                customer_location,
                "",
                "LOW",
                note,
            )
        )
    return rows


def build_detail_row(
    source: SourceDocument,
    document_type: str,
    document_number: str,
    document_date: str,
    leistungszeitraum: str,
    month_year: str,
    position_code: str,
    position_name: str,
    quantity: str,
    price: str,
    amount: Decimal | None,
    package_id: str,
    tour_number: str,
    customer_location: str,
    category: str,
    confidence: str,
    note: str,
) -> DetailRow:
    content_hash = sha256_file(source.path)
    amount_text = format_decimal(amount)
    duplicate_key = "|".join([document_number, document_date, amount_text, content_hash])
    return DetailRow(
        document_filename=source.path.name,
        document_type=document_type,
        document_number=document_number,
        document_date=document_date,
        leistungszeitraum=leistungszeitraum,
        month_year=month_year,
        position_code=position_code,
        position_name=position_name,
        quantity=quantity,
        price_per_unit=price,
        amount=amount_text,
        package_id=package_id,
        tour_number=tour_number,
        customer_location=customer_location,
        source_file_path=source.display_path,
        source_container=source.source_container,
        confidence_level=confidence,
        deduction_category=category,
        content_hash=content_hash,
        duplicate_key=duplicate_key,
        notes=note,
    )


def deduplicate(rows: list[DetailRow]) -> tuple[list[DetailRow], list[dict[str, str]]]:
    seen: dict[str, DetailRow] = {}
    unique: list[DetailRow] = []
    duplicates: list[dict[str, str]] = []

    for row in rows:
        key = row.duplicate_key
        if key in seen:
            kept = seen[key]
            duplicates.append(
                {
                    "duplicate_key": key,
                    "kept_source_file": kept.source_file_path,
                    "duplicate_source_file": row.source_file_path,
                    "document_number": row.document_number,
                    "document_date": row.document_date,
                    "amount": row.amount,
                    "content_hash": row.content_hash,
                    "reason": "Same document number, date, amount, and file hash.",
                }
            )
            continue
        seen[key] = row
        unique.append(row)
    return unique, duplicates


def amount_to_decimal(value: str) -> Decimal:
    parsed = parse_decimal(value)
    return parsed if parsed is not None else Decimal("0")


def build_monthly(rows: list[DetailRow]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows_by_month: dict[str, list[DetailRow]] = defaultdict(list)
    for row in rows:
        if row.month_year:
            rows_by_month[row.month_year].append(row)

    monthly: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    for month in month_range():
        month_rows = rows_by_month.get(month, [])
        sources = {row.source_file_path for row in month_rows}
        has_gutschrift = any("gutschrift" in normalize_text(row.document_type) for row in month_rows)

        totals = {category: Decimal("0") for category in DEDUCTION_CATEGORIES}
        gross = Decimal("0")
        net = Decimal("0")
        net_available = False
        notes: list[str] = []

        for row in month_rows:
            amount = amount_to_decimal(row.amount)
            if "gutschrift" in normalize_text(row.document_type):
                gross += amount
            if row.deduction_category in totals:
                totals[row.deduction_category] += amount
            if "netto" in normalize_text(row.position_name):
                net += amount
                net_available = True

        missing_source = "NO" if has_gutschrift else "YES"
        if missing_source == "YES":
            notes.append("No Gutschrift/Abrechnung source document detected for this month.")

        total_deductions = sum((totals[category] for category in DEDUCTION_CATEGORIES), Decimal("0"))
        row = {
            "month": month,
            "gross_credit_gutschrift_total": format_decimal(gross) if gross else "",
            "abschlag_coincident_total": format_decimal(totals["Abschlag Coincident"]) if totals["Abschlag Coincident"] else "",
            "abschlag_mitnahme_total": format_decimal(totals["Abschlag Mitnahme"]) if totals["Abschlag Mitnahme"] else "",
            "abschlag_quittungslose_sendung_total": format_decimal(totals["Abschlag Quittungslose Sendung"])
            if totals["Abschlag Quittungslose Sendung"]
            else "",
            "sendungsverlust_total": format_decimal(totals["Sendungsverlust"]) if totals["Sendungsverlust"] else "",
            "scannermiete_total": format_decimal(totals["Scannermiete"]) if totals["Scannermiete"] else "",
            "other_deductions_total": format_decimal(totals["Other deductions"]) if totals["Other deductions"] else "",
            "total_deductions": format_decimal(total_deductions) if total_deductions else "",
            "net_amount_if_available": format_decimal(net) if net_available else "",
            "number_of_source_documents": str(len(sources)),
            "missing_source_documents": missing_source,
            "notes": " ".join(notes),
        }
        monthly.append(row)
        if missing_source == "YES":
            missing.append({"month": month, "missing_source_documents": "YES", "notes": row["notes"]})

    return monthly, missing


def write_csv(path: Path, headers: list[str], rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def write_xlsx(path: Path, headers: list[str], rows: list[dict[str, str]], sheet_name: str) -> None:
    import zipfile as zip_writer

    values = [headers] + [[str(row.get(header, "")) for header in headers] for row in rows]
    sheet_rows: list[str] = []
    for row_index, row_values in enumerate(values, start=1):
        cells: list[str] = []
        for col_index, value in enumerate(row_values, start=1):
            ref = f"{column_name(col_index)}{row_index}"
            escaped = html.escape(value)
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escaped}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    worksheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        "</worksheet>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{html.escape(sheet_name[:31])}" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )

    with zip_writer.ZipFile(path, "w", compression=zip_writer.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)


def total_by_category(rows: list[DetailRow]) -> dict[str, Decimal]:
    totals = {category: Decimal("0") for category in DEDUCTION_CATEGORIES}
    for row in rows:
        if row.deduction_category in totals:
            totals[row.deduction_category] += amount_to_decimal(row.amount)
    return totals


def markdown_table(headers: list[str], rows: list[dict[str, str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")).replace("\n", " ") for header in headers) + " |")
    return "\n".join(lines)


def write_report(rows: list[DetailRow], monthly: list[dict[str, str]], missing: list[dict[str, str]], duplicates: list[dict[str, str]]) -> None:
    totals = total_by_category(rows)
    source_documents = sorted({row.source_file_path for row in rows})
    category_lines = "\n".join(
        f"- {category}: {format_decimal(amount) if amount else ''}" for category, amount in totals.items()
    )
    missing_lines = "\n".join(f"- {row['month']}" for row in missing) or "- None detected"
    source_lines = "\n".join(f"- {source}" for source in source_documents) or "- No Enrico/Sachsenpower source documents detected"

    report = f"""# Enrico Deduction Analysis

## Purpose

Analyze documents from Enrico Weissflog / Sachsenpower and create monthly deduction tables for financial review.

## Period Analyzed

February 2024 through June 2025.

## Total Deductions by Category

{category_lines}

## Monthly Summary Table

{markdown_table(MONTHLY_HEADERS, monthly)}

## Missing Months

{missing_lines}

## Important Observations

- The analyzer does not invent numbers. Empty values mean no reliable value was extracted.
- PDF text extraction depends on an available PDF text backend such as `pypdf`, `PyPDF2`, or `pdftotext`.
- RAR extraction depends on the optional `rarfile` package and a compatible local RAR backend.
- Duplicate detection uses document number, document date, amount, and file hash.
- Duplicate documents detected: {len(duplicates)}

## List of Source Documents

{source_lines}

## Limitations

- OCR is not implemented.
- Scanned PDFs without embedded text cannot be analyzed until OCR is added.
- The script extracts conservative text patterns only; complex tables may require manual review.
- Missing source documents are marked when no Gutschrift or Abrechnung was detected for the month.

## Next Documents Needed

- Missing Gutschrift or Abrechnung documents for all months marked as missing.
- Any Sachsenpower/Enrico ZIP, RAR, EML, PDF, TXT, or CSV files not yet placed in `_INBOX` or `03_Documents - Документи - Dokumente`.
- Original PDFs with embedded text or OCR-ready scanned copies for months where values are empty.
"""
    (REPORT_ROOT / "ENRICO_DEDUCTION_ANALYSIS.md").write_text(report, encoding="utf-8")
    (REPO_ROOT / "ENRICO_DEDUCTION_ANALYSIS.md").write_text(report, encoding="utf-8")


def write_output_readme() -> None:
    readme = """# Enrico Deductions Report Output

This folder contains generated outputs from the Enrico Financial Deduction Analyzer.

## Files

- `enrico_deductions_monthly.csv`: monthly deduction summary from 2024-02 to 2025-06.
- `enrico_deductions_monthly.xlsx`: spreadsheet version of the monthly summary.
- `enrico_deductions_detailed.csv`: extracted document and position-level detail rows.
- `enrico_deductions_detailed.xlsx`: spreadsheet version of the detailed table.
- `missing_months.csv`: months where no Gutschrift or Abrechnung source document was detected.
- `duplicate_documents.csv`: documents skipped as duplicates.
- `processing_log.txt`: scan, extraction, and limitation log.
- `ENRICO_DEDUCTION_ANALYSIS.md`: markdown report.

## Interpretation

Empty financial values mean the analyzer could not reliably extract a number. LOW confidence rows require manual review.
"""
    (REPORT_ROOT / "README.md").write_text(readme, encoding="utf-8")


def analyze() -> tuple[list[DetailRow], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], ProcessingLog]:
    log = ProcessingLog()
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="enrico_deduction_analyzer_") as temp_dir:
        temp_root = Path(temp_dir)
        initial_docs = scan_input_files(log)
        sources = expand_archives_and_emails(initial_docs, temp_root, log)

        rows: list[DetailRow] = []
        for source in sources:
            if source.path.suffix.lower() in {".zip", ".rar"}:
                continue
            text, email_metadata, note = read_source_text(source, temp_root, log)
            if not is_relevant(source, text):
                log.add(f"Skipped non-Enrico/Sachsenpower document: {source.display_path}")
                continue
            extracted_rows = extract_detail_rows(source, text, email_metadata or source.email_metadata, note)
            if extracted_rows:
                rows.extend(extracted_rows)
                log.add(f"Extracted {len(extracted_rows)} detail rows from: {source.display_path}")
            else:
                log.add(f"Relevant document found but no financial rows extracted: {source.display_path}")

        unique_rows, duplicates = deduplicate(rows)
        monthly, missing = build_monthly(unique_rows)
        log.add(f"Unique detail rows: {len(unique_rows)}")
        log.add(f"Duplicate rows: {len(duplicates)}")
        log.add(f"Missing months: {len(missing)}")
        return unique_rows, monthly, missing, duplicates, log


def main() -> int:
    rows, monthly, missing, duplicates, log = analyze()
    detail_dicts = [row.as_dict() for row in rows]

    write_csv(REPORT_ROOT / "enrico_deductions_detailed.csv", DETAIL_HEADERS, detail_dicts)
    write_xlsx(REPORT_ROOT / "enrico_deductions_detailed.xlsx", DETAIL_HEADERS, detail_dicts, "Detailed")
    write_csv(REPORT_ROOT / "enrico_deductions_monthly.csv", MONTHLY_HEADERS, monthly)
    write_xlsx(REPORT_ROOT / "enrico_deductions_monthly.xlsx", MONTHLY_HEADERS, monthly, "Monthly")
    write_csv(REPORT_ROOT / "missing_months.csv", MISSING_HEADERS, missing)
    write_csv(REPORT_ROOT / "duplicate_documents.csv", DUPLICATE_HEADERS, duplicates)
    write_report(rows, monthly, missing, duplicates)
    write_output_readme()
    log.write(REPORT_ROOT / "processing_log.txt")

    print(f"Detailed rows: {len(rows)}")
    print(f"Missing months: {len(missing)}")
    print(f"Duplicates: {len(duplicates)}")
    print(f"Output folder: {repo_relative(REPORT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
