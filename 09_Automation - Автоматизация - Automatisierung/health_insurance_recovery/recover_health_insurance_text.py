#!/usr/bin/env python3
"""Recover text from unreadable health-insurance PDFs without modifying originals."""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / "08_Reports - Доклади - Berichte" / "Accounting_Cash_Flow"
INPUT_CSV = REPORT_ROOT / "health_insurance_unreadable_files.csv"
OUTPUT_XLSX = REPORT_ROOT / "health_insurance_unreadable_files.xlsx"
RECOVERED_ROOT = REPORT_ROOT / "recovered_health_insurance_text"
REPORT_MD = REPORT_ROOT / "HEALTH_INSURANCE_RECOVERY_REPORT.md"
LOCAL_PACKAGES = REPO_ROOT / ".python_packages"
PDF_PASSWORD = "10001"

if LOCAL_PACKAGES.exists():
    sys.path.insert(0, str(LOCAL_PACKAGES))

RECOVERY_COLUMNS = ["recovery_status", "recovery_method", "recovered_text_path", "extracted_text_length"]
INSURERS = [
    ("AOK Sachsen-Anhalt", ["aok sachsen-anhalt", "aok sachsen anhalt"]),
    ("AOK", ["aok"]),
    ("TK", ["tk", "techniker"]),
    ("KKH", ["kkh"]),
    ("Barmer", ["barmer"]),
    ("DAK", ["dak"]),
    ("BKK Linde", ["bkk linde"]),
    ("BKK", ["bkk", "vivda bkk", "vivida bkk"]),
    ("VIACTIV", ["viactiv"]),
]


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def normalize(value: str) -> str:
    return value.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-")
    return stem[:120] or "recovered_text"


def detect_insurer(filename: str, path_text: str, text: str = "") -> str:
    haystack = normalize(f"{filename}\n{path_text}\n{text[:5000]}")
    for name, terms in INSURERS:
        if any(normalize(term) in haystack for term in terms):
            return name
    if "krank" in haystack:
        return "Krankenkasse unknown"
    return ""


def detect_dates(text: str) -> list[str]:
    values = set()
    for match in re.finditer(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", text):
        values.add(match.group(0))
    for match in re.finditer(r"\b20\d{2}[-_/ .](?:0?[1-9]|1[0-2])\b", text):
        values.add(match.group(0))
    return sorted(values)


def detect_amounts(text: str) -> list[str]:
    amounts = set()
    money = r"-?\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})|-?\d+(?:[,.]\d{2})"
    for match in re.finditer(money, text):
        amounts.add(match.group(0))
    return sorted(amounts)


def extract_with_fitz(path: Path) -> tuple[str, str, str]:
    try:
        import fitz  # type: ignore
    except Exception as exc:
        return "", "NOT_ATTEMPTED", f"PyMuPDF unavailable: {exc}"
    try:
        doc = fitz.open(path)
        password_success = "NOT_APPLICABLE"
        if doc.needs_pass:
            password_success = "YES" if doc.authenticate(PDF_PASSWORD) else "NO"
            if password_success != "YES":
                return "", password_success, "PyMuPDF password authentication failed"
        text = "\n".join(page.get_text("text") or "" for page in doc)
        return text, password_success, ""
    except Exception as exc:
        return "", "NO", f"PyMuPDF failed: {exc}"


def extract_with_pypdf(path: Path) -> tuple[str, str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:
        return "", "NOT_ATTEMPTED", f"pypdf unavailable: {exc}"
    try:
        reader = PdfReader(str(path))
        password_success = "NOT_APPLICABLE"
        if reader.is_encrypted:
            password_success = "YES" if reader.decrypt(PDF_PASSWORD) else "NO"
            if password_success != "YES":
                return "", password_success, "pypdf password decrypt failed"
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text, password_success, ""
    except Exception as exc:
        return "", "NO", f"pypdf failed: {exc}"


def extract_with_pdfplumber(path: Path) -> tuple[str, str, str]:
    try:
        import pdfplumber  # type: ignore
    except Exception as exc:
        return "", "NOT_ATTEMPTED", f"pdfplumber unavailable: {exc}"
    try:
        with pdfplumber.open(str(path), password=PDF_PASSWORD) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text, "YES", ""
    except Exception as exc:
        return "", "NO", f"pdfplumber failed: {exc}"


def ocr_available() -> bool:
    try:
        import pytesseract  # type: ignore  # noqa: F401
        from pdf2image import convert_from_path  # type: ignore  # noqa: F401
        from PIL import Image  # type: ignore  # noqa: F401
    except Exception:
        return False
    return True


def recover_pdf(path: Path) -> tuple[str, str, str, list[str]]:
    errors: list[str] = []
    for method, extractor in [
        ("PyMuPDF fitz", extract_with_fitz),
        ("pypdf", extract_with_pypdf),
        ("pdfplumber", extract_with_pdfplumber),
    ]:
        text, password_success, error = extractor(path)
        if error:
            errors.append(error)
        if text.strip():
            return text, method, password_success, errors
    return "", "", "NO", errors


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


def write_xlsx(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    values = [headers] + [[str(row.get(header, "")) for header in headers] for row in rows]
    sheet_rows: list[str] = []
    for row_index, row_values in enumerate(values, start=1):
        cells: list[str] = []
        for col_index, value in enumerate(row_values, start=1):
            ref = f"{col_name(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{html.escape(value)}</t></is></c>')
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    worksheet = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(sheet_rows) + "</sheetData></worksheet>"
    workbook = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Unreadable" sheetId="1" r:id="rId1"/></sheets></workbook>'
    rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    # Correct root relationship XML. Kept separate to avoid hand-editing the long worksheet body.
    root_rels = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    content_types = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>'
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)


def write_metadata(path: Path, metadata: dict[str, object]) -> None:
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_rows() -> tuple[list[str], list[dict[str, str]]]:
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        rows = list(reader)
    for column in RECOVERY_COLUMNS:
        if column not in headers:
            headers.append(column)
    return headers, rows


def write_report(rows: list[dict[str, str]]) -> None:
    recovered = [row for row in rows if row.get("recovery_status") == "RECOVERED"]
    ocr_required_rows = [row for row in rows if row.get("recovery_status") == "OCR_REQUIRED"]
    failed = [row for row in rows if row.get("recovery_status") == "FAILED"]
    blockers = ocr_required_rows + failed
    lines = [
        "# Health Insurance Recovery Report",
        "",
        "## Summary",
        "",
        f"- Recovered count: {len(recovered)}",
        f"- OCR required count: {len(ocr_required_rows)}",
        f"- Failed count: {len(failed)}",
        f"- Files still blocking analysis: {len(blockers)}",
        "",
        "## Recovered Files",
        "",
    ]
    lines.extend([f"- `{row['filename']}` via {row.get('recovery_method', '')}: {row.get('extracted_text_length', '0')} chars" for row in recovered] or ["- None"])
    lines.extend(["", "## Files Still Blocking Analysis", ""])
    lines.extend([f"- `{row['filename']}`: {row.get('recovery_status')} ({row.get('recovery_method', '')})" for row in blockers] or ["- None"])
    lines.extend(["", "## Notes", "", "- OCR was not run unless local OCR tooling was already installed.", "- Original evidence files were not modified."])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def process() -> list[dict[str, str]]:
    headers, rows = read_rows()
    RECOVERED_ROOT.mkdir(parents=True, exist_ok=True)
    has_ocr = ocr_available()
    for row in rows:
        source = REPO_ROOT / Path(row.get("full_path", ""))
        stem = safe_stem(row.get("filename", source.name))
        metadata_path = RECOVERED_ROOT / f"{stem}.json"
        text_path = RECOVERED_ROOT / f"{stem}.txt"
        text = ""
        method = ""
        password_success = row.get("password_success", "")
        status = "FAILED"
        errors: list[str] = []

        if not source.exists():
            errors.append("Source file missing")
        elif source.suffix.lower() == ".pdf":
            text, method, password_success, errors = recover_pdf(source)
            if text.strip():
                status = "RECOVERED"
            else:
                status = "OCR_REQUIRED" if has_ocr or row.get("scanned_image_suspected") == "YES" else "OCR_REQUIRED"
                method = "OCR_REQUIRED after PyMuPDF/pypdf/pdfplumber attempts"
        elif source.suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
            status = "OCR_REQUIRED"
            method = "image OCR required"
        else:
            status = "FAILED"
            method = f"unsupported file type: {source.suffix.lower()}"

        recovered_text_path = ""
        if status == "RECOVERED":
            text_path.write_text(text, encoding="utf-8")
            recovered_text_path = repo_relative(text_path)
        text_length = len(text)
        detected_insurer = detect_insurer(row.get("filename", ""), row.get("full_path", ""), text) or row.get("detected_insurance_name_from_filename_path", "")
        metadata = {
            "filename": row.get("filename", source.name),
            "extraction_method": method,
            "password_success": password_success,
            "text_length": text_length,
            "detected_insurance_name": detected_insurer,
            "detected_dates": detect_dates(text),
            "detected_amounts": detect_amounts(text),
            "status": status,
            "source_file": row.get("full_path", ""),
            "technical_errors": errors,
        }
        write_metadata(metadata_path, metadata)

        row["recovery_status"] = status
        row["recovery_method"] = method
        row["recovered_text_path"] = recovered_text_path
        row["extracted_text_length"] = str(text_length)

    write_csv(INPUT_CSV, headers, rows)
    write_xlsx(OUTPUT_XLSX, headers, rows)
    write_report(rows)
    return rows


def main() -> int:
    rows = process()
    recovered = sum(1 for row in rows if row.get("recovery_status") == "RECOVERED")
    ocr_required_rows = sum(1 for row in rows if row.get("recovery_status") == "OCR_REQUIRED")
    failed = sum(1 for row in rows if row.get("recovery_status") == "FAILED")
    print(f"Recovered count: {recovered}")
    print(f"OCR required count: {ocr_required_rows}")
    print(f"Failed count: {failed}")
    print(f"Output folder: {repo_relative(RECOVERED_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
