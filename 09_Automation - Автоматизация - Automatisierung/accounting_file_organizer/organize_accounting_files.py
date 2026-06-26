#!/usr/bin/env python3
"""Copy accounting files into review categories with a full manifest."""

from __future__ import annotations

import csv
import hashlib
import html
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_ROOT = REPO_ROOT / "00_INBOX - Входящи - Eingang" / "Accounting"
OUTPUT_ROOT = REPO_ROOT / "00_INBOX - Входящи - Eingang" / "Accounting_Organized"
LOCAL_PACKAGES = REPO_ROOT / ".python_packages"
PDF_PASSWORD = "10001"

if LOCAL_PACKAGES.exists():
    import sys

    sys.path.insert(0, str(LOCAL_PACKAGES))


CATEGORIES = {
    "01_Accountant_Emails": "Accountant Emails",
    "02_Payroll": "Payroll",
    "03_Employee_Payslips": "Employee Payslips",
    "04_Health_Insurance": "Health Insurance",
    "05_Taxes": "Taxes",
    "06_Bank_Payments": "Bank Payments",
    "07_Cash_Payments": "Cash Payments",
    "08_Operating_Costs": "Operating Costs",
    "09_Enrico_Forwarded": "Enrico Forwarded",
    "10_BWA_Reports": "BWA Reports",
    "11_Contribution_Lists": "Contribution Lists",
    "12_Liability_Overview": "Liability Overview",
    "13_Unknown_To_Review": "Unknown To Review",
    "14_Duplicates": "Duplicates",
}

MANIFEST_HEADERS = [
    "original_path",
    "organized_path",
    "filename",
    "file_type",
    "detected_category",
    "secondary_categories",
    "detected_document_type",
    "detected_month",
    "detected_year",
    "detected_people",
    "detected_companies",
    "detected_amounts",
    "confidence",
    "reason_for_classification",
    "duplicate_group_id",
    "content_read",
    "action_taken",
]

DUPLICATE_HEADERS = [
    "duplicate_group_id",
    "original_path",
    "duplicate_of",
    "filename",
    "file_type",
    "hash",
    "size",
    "reason",
]

UNKNOWN_HEADERS = [
    "original_path",
    "filename",
    "file_type",
    "reason",
    "content_read",
    "recommended_next_action",
]

KEYWORDS = {
    "01_Accountant_Emails": ["eml", "gmail", "brunettin", "marco", "accounting correspondence"],
    "02_Payroll": ["lohnauswertungen", "lohnjournal", "brutto_netto", "brutto-netto", "payroll", "gesamtbrutto", "total payroll"],
    "03_Employee_Payslips": ["entgeltbescheinigung", "entgeltbescheinigungen", "payslip", "salary slip", "lohnabrechnung"],
    "04_Health_Insurance": [
        "aok",
        "aok plus",
        "tk",
        "techniker",
        "kkh",
        "barmer",
        "dak",
        "bkk",
        "ikk",
        "viactiv",
        "vivida",
        "krankenkasse",
        "beitragsnachweis",
        "sozialversicherung",
        "sv-beitraege",
        "sv-beiträge",
    ],
    "05_Taxes": ["finanzamt", "stadt chemnitz", "gewerbesteuer", "umsatzsteuer", "lohnsteuer", "einkommensteuer", "tax office", "tax liabilities"],
    "06_Bank_Payments": ["bankkontoumsaetze", "bankkontoumsätze", "kontoauszug", "zahlungsnachweis", "ueberweisung", "überweisung", "sepa", "payment proof"],
    "07_Cash_Payments": ["barzahlung", "cash salary", "signed salary receipt", "nachweis von lohnzahlungen", "cash receipt"],
    "08_Operating_Costs": [
        "fuel",
        "tank",
        "diesel",
        "vehicle",
        "car",
        "leasing",
        "repair",
        "insurance",
        "rent",
        "phone",
        "accounting fee",
        "scanner",
        "office",
        "equipment",
        "kraftstoff",
        "fahrzeug",
        "reparatur",
        "miete",
        "telefon",
        "büro",
        "buero",
    ],
    "09_Enrico_Forwarded": ["enrico weissflog", "enrico weißflog", "sachsenpower", "gutschrift", "sendungsverlust", "abschlag coincident", "leistungsnachweis", "scannermiete"],
    "10_BWA_Reports": ["bwa", "betriebswirtschaftliche auswertung", "datev bwa", "preliminary result", "sales", "cost groups"],
    "11_Contribution_Lists": ["contributions", "contribution table", "iban", "verwendungszweck"],
    "12_Liability_Overview": ["offene posten", "opos", "offene verbindlichkeiten", "zahlungsübersicht", "zahlungsuebersicht", "amounts due", "unpaid balances", "payment plan", "rückstand", "rueckstand", "mahnung", "forderung"],
}

PRIORITY = [
    "01_Accountant_Emails",
    "11_Contribution_Lists",
    "09_Enrico_Forwarded",
    "04_Health_Insurance",
    "05_Taxes",
    "07_Cash_Payments",
    "06_Bank_Payments",
    "03_Employee_Payslips",
    "02_Payroll",
    "10_BWA_Reports",
    "12_Liability_Overview",
    "08_Operating_Costs",
]


@dataclass
class ReadResult:
    text: str
    content_read: str
    reason: str = ""


class Log:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def add(self, message: str) -> None:
        self.lines.append(f"{datetime.now().isoformat(timespec='seconds')} {message}")

    def write(self) -> None:
        (OUTPUT_ROOT / "organization_log.txt").write_text("\n".join(self.lines) + "\n", encoding="utf-8")


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text_file(path: Path) -> ReadResult:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return ReadResult(path.read_text(encoding=encoding), "YES")
        except UnicodeDecodeError:
            continue
    return ReadResult(path.read_text(encoding="utf-8", errors="replace"), "YES")


def read_pdf(path: Path, log: Log) -> ReadResult:
    errors: list[str] = []
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        if reader.is_encrypted:
            reader.decrypt(PDF_PASSWORD)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            return ReadResult(text, "YES")
        errors.append("pypdf returned no text")
    except Exception as exc:
        errors.append(f"pypdf failed: {exc}")
    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(str(path), password=PDF_PASSWORD) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if text.strip():
            return ReadResult(text, "YES")
        errors.append("pdfplumber returned no text")
    except Exception as exc:
        errors.append(f"pdfplumber failed: {exc}")
    reason = "PDF text unavailable: " + " | ".join(errors)
    log.add(f"{reason}: {repo_relative(path)}")
    return ReadResult("", "NO", reason)


def read_docx(path: Path, log: Log) -> ReadResult:
    try:
        with zipfile.ZipFile(path) as archive:
            texts: list[str] = []
            for name in archive.namelist():
                if name.startswith("word/") and name.endswith(".xml"):
                    root = ET.fromstring(archive.read(name))
                    texts.append(" ".join(root.itertext()))
            return ReadResult("\n".join(texts), "YES")
    except Exception as exc:
        reason = f"DOCX text unavailable: {exc}"
        log.add(f"{reason}: {repo_relative(path)}")
        return ReadResult("", "NO", reason)


def read_xlsx(path: Path, log: Log) -> ReadResult:
    try:
        import openpyxl  # type: ignore

        workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
        rows: list[str] = []
        for sheet in workbook.worksheets:
            rows.append(f"Sheet: {sheet.title}")
            for row in sheet.iter_rows(values_only=True):
                rows.append(" | ".join("" if cell is None else str(cell) for cell in row))
        return ReadResult("\n".join(rows), "YES")
    except Exception as exc:
        reason = f"XLSX text unavailable: {exc}"
        log.add(f"{reason}: {repo_relative(path)}")
        return ReadResult("", "NO", reason)


def read_file(path: Path, log: Log) -> ReadResult:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf(path, log)
    if suffix in {".txt", ".csv", ".eml"}:
        return read_text_file(path)
    if suffix == ".docx":
        return read_docx(path, log)
    if suffix == ".xlsx":
        return read_xlsx(path, log)
    return ReadResult("", "NO", f"Unsupported for content reading: {suffix}")


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


def detect_month_year(text: str) -> tuple[str, str]:
    match = re.search(r"\b(20\d{2})[-_. ](0?[1-9]|1[0-2])\b", text)
    if match:
        return f"{int(match.group(2)):02d}", match.group(1)
    match = re.search(r"\b(0?[1-9]|1[0-2])[-_. ](20\d{2})\b", text)
    if match:
        return f"{int(match.group(1)):02d}", match.group(2)
    return "", ""


def detected_amounts(text: str) -> str:
    values = []
    for match in re.finditer(r"-?\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})|-?\d+(?:[,.]\d{2})", text):
        parsed = parse_decimal(match.group(0))
        if parsed is not None:
            values.append(f"{parsed.quantize(Decimal('0.01'))}")
        if len(values) >= 12:
            break
    return "; ".join(values)


def detected_people(text: str) -> str:
    names = set()
    for match in re.finditer(r"\b([A-ZÄÖÜ][A-Za-zÄÖÜäöüß'-]+(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß'-]+){1,3})\b", text):
        name = match.group(1).strip()
        if 5 <= len(name) <= 80 and not any(skip in name.lower() for skip in ["finanzamt", "stadt chemnitz", "sachsenpower"]):
            names.add(name)
        if len(names) >= 10:
            break
    return "; ".join(sorted(names))


def detected_companies(text: str) -> str:
    companies = set()
    for pattern in [r"\b([A-ZÄÖÜ][^\n\r]{2,80}(?:GmbH|UG|KG|AG|Krankenkasse|Finanzamt|Hauptzollamt|Stadt Chemnitz))\b"]:
        for match in re.finditer(pattern, text):
            companies.add(re.sub(r"\s+", " ", match.group(1)).strip())
            if len(companies) >= 10:
                break
    return "; ".join(sorted(companies))


def classify(path: Path, content: str, content_read: str) -> tuple[str, list[str], str, str, str]:
    haystack = normalize(f"{repo_relative(path)}\n{content}")
    scores: dict[str, int] = {}
    reasons: dict[str, list[str]] = defaultdict(list)
    for category, words in KEYWORDS.items():
        score = 0
        for word in words:
            if normalize(word) in haystack:
                score += 1
                reasons[category].append(word)
        if path.suffix.lower() == ".eml" and category == "01_Accountant_Emails":
            score += 3
            reasons[category].append(".eml")
        if score:
            scores[category] = score

    if "hauptzollamt" in haystack and any(term in haystack for term in ["krankenkasse", "beitrag", "sozialversicherung"]):
        scores["04_Health_Insurance"] = scores.get("04_Health_Insurance", 0) + 2
        reasons["04_Health_Insurance"].append("Hauptzollamt related to Krankenkasse")
    elif "hauptzollamt" in haystack:
        scores["05_Taxes"] = scores.get("05_Taxes", 0) + 1
        reasons["05_Taxes"].append("Hauptzollamt")

    if not scores:
        return "13_Unknown_To_Review", [], "Unknown", "LOW", "No category keywords detected."

    ordered = sorted(scores.items(), key=lambda item: (-item[1], PRIORITY.index(item[0]) if item[0] in PRIORITY else 999))
    primary, score = ordered[0]
    secondary = [category for category, _ in ordered[1:]]
    confidence = "HIGH" if score >= 3 and content_read == "YES" else "MEDIUM" if score >= 2 or content_read == "YES" else "LOW"
    if confidence == "LOW":
        return "13_Unknown_To_Review", secondary, "Unknown", "LOW", f"Low confidence match: {', '.join(reasons[primary])}"
    return primary, secondary, CATEGORIES[primary], confidence, f"Matched keywords: {', '.join(reasons[primary])}"


def safe_copy(source: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    if not target.exists():
        shutil.copy2(source, target)
        return target
    stem, suffix = source.stem, source.suffix
    counter = 2
    while True:
        candidate = target_dir / f"{stem}__copy{counter}{suffix}"
        if not candidate.exists():
            shutil.copy2(source, candidate)
            return candidate
        counter += 1


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


def write_xlsx(path: Path, headers: list[str], rows: list[dict[str, str]], sheet_name: str) -> None:
    values = [headers] + [[str(row.get(header, "")) for header in headers] for row in rows]
    sheet_rows = []
    for row_index, row_values in enumerate(values, start=1):
        cells = []
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


def write_report(manifest: list[dict[str, str]], duplicate_rows: list[dict[str, str]], unknown_rows: list[dict[str, str]]) -> None:
    counts = Counter(row["detected_category"] for row in manifest)
    lines = [
        "# Accounting File Organization Report",
        "",
        f"Total files scanned: {len(manifest)}",
        f"Copied files: {sum(1 for row in manifest if row['action_taken'] == 'COPY')}",
        f"Duplicates: {len(duplicate_rows)}",
        f"Unknown files: {len(unknown_rows)}",
        "",
        "## Category Counts",
        "",
    ]
    for category, label in CATEGORIES.items():
        lines.append(f"- {category} ({label}): {counts.get(category, 0)}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Originals were preserved.",
            "- Files were copied, not moved.",
            "- Low confidence files were placed in `13_Unknown_To_Review`.",
            "- Exact duplicates were placed in `14_Duplicates`.",
        ]
    )
    (OUTPUT_ROOT / "ACCOUNTING_FILE_ORGANIZATION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def organize() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], Log]:
    log = Log()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    for category in CATEGORIES:
        (OUTPUT_ROOT / category).mkdir(parents=True, exist_ok=True)

    files = [path for path in INPUT_ROOT.rglob("*") if path.is_file()]
    hashes: dict[str, str] = {}
    likely: dict[tuple[str, int], str] = {}
    manifest: list[dict[str, str]] = []
    duplicates: list[dict[str, str]] = []
    unknown: list[dict[str, str]] = []
    duplicate_index = 1

    for path in files:
        original = repo_relative(path)
        file_hash = sha256_file(path)
        duplicate_group = ""
        is_duplicate = False
        reason = ""
        if file_hash in hashes:
            is_duplicate = True
            duplicate_group = f"DUP-{duplicate_index:06d}"
            duplicate_index += 1
            reason = "Exact duplicate by SHA-256 hash."
            duplicate_of = hashes[file_hash]
        else:
            duplicate_of = ""
            hashes[file_hash] = original
            likely_key = (normalize(path.name), path.stat().st_size)
            if likely_key in likely:
                is_duplicate = True
                duplicate_group = f"DUP-{duplicate_index:06d}"
                duplicate_index += 1
                reason = "Likely duplicate by filename and size."
                duplicate_of = likely[likely_key]
            else:
                likely[likely_key] = original

        read = read_file(path, log)
        content_basis = f"{path.name}\n{original}\n{read.text}"
        category, secondary, doc_type, confidence, classify_reason = classify(path, read.text, read.content_read)
        if is_duplicate:
            category = "14_Duplicates"
            confidence = "HIGH"
            doc_type = "Duplicate"
            classify_reason = reason
        elif confidence == "LOW":
            category = "13_Unknown_To_Review"

        organized_path = safe_copy(path, OUTPUT_ROOT / category)
        month, year = detect_month_year(content_basis)
        row = {
            "original_path": original,
            "organized_path": repo_relative(organized_path),
            "filename": path.name,
            "file_type": path.suffix.lower(),
            "detected_category": category,
            "secondary_categories": "; ".join(secondary),
            "detected_document_type": doc_type,
            "detected_month": month,
            "detected_year": year,
            "detected_people": detected_people(content_basis),
            "detected_companies": detected_companies(content_basis),
            "detected_amounts": detected_amounts(content_basis),
            "confidence": confidence,
            "reason_for_classification": classify_reason,
            "duplicate_group_id": duplicate_group,
            "content_read": read.content_read,
            "action_taken": "COPY",
        }
        manifest.append(row)
        if is_duplicate:
            duplicates.append(
                {
                    "duplicate_group_id": duplicate_group,
                    "original_path": original,
                    "duplicate_of": duplicate_of,
                    "filename": path.name,
                    "file_type": path.suffix.lower(),
                    "hash": file_hash,
                    "size": str(path.stat().st_size),
                    "reason": reason,
                }
            )
        if category == "13_Unknown_To_Review":
            unknown.append(
                {
                    "original_path": original,
                    "filename": path.name,
                    "file_type": path.suffix.lower(),
                    "reason": classify_reason,
                    "content_read": read.content_read,
                    "recommended_next_action": "Review manually or add category-specific keyword/parser.",
                }
            )
        log.add(f"COPY {original} -> {repo_relative(organized_path)} [{category}]")

    return manifest, duplicates, unknown, log


def main() -> int:
    manifest, duplicates, unknown, log = organize()
    write_csv(OUTPUT_ROOT / "file_organization_manifest.csv", MANIFEST_HEADERS, manifest)
    write_xlsx(OUTPUT_ROOT / "file_organization_manifest.xlsx", MANIFEST_HEADERS, manifest, "Manifest")
    write_csv(OUTPUT_ROOT / "duplicate_files.csv", DUPLICATE_HEADERS, duplicates)
    write_csv(OUTPUT_ROOT / "unknown_files.csv", UNKNOWN_HEADERS, unknown)
    write_report(manifest, duplicates, unknown)
    log.write()
    counts = Counter(row["detected_category"] for row in manifest)
    print(f"Total files scanned: {len(manifest)}")
    print(f"Copied files: {sum(1 for row in manifest if row['action_taken'] == 'COPY')}")
    print(f"Duplicates: {len(duplicates)}")
    print(f"Unknown files: {len(unknown)}")
    for category in CATEGORIES:
        print(f"{category}: {counts.get(category, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
